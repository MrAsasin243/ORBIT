#!/usr/bin/env python3
"""Orbit LAN server: single-host SQLite storage + same-origin static frontend."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import hmac
import json
import mimetypes
import os
import secrets
import socket
import sqlite3
import sys
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "orbit.sqlite3"
CONFIG_PATH = DATA_DIR / "server-config.json"
APP_NAME = "Orbit Server"
SCHEMA_VERSION = 5
MAX_BODY = 80 * 1024 * 1024
SESSION_TTL_SECONDS = 12 * 60 * 60
PBKDF2_ITERATIONS = 260_000

SESSIONS: dict[str, float] = {}
SESSION_LOCK = threading.Lock()
LOGIN_ATTEMPTS: dict[str, deque[float]] = defaultdict(deque)
LOGIN_LOCK = threading.Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def default_state() -> dict:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "profile": {"xp": 0, "createdAt": utc_now()},
        "tasks": [], "goals": [], "timeEntries": [], "projects": [],
        "dailyPriorities": {}, "studySubjects": [], "habits": [],
        "reviews": [], "examDecks": [], "fitnessSessions": [], "timer": None,
    }


def hash_password(password: str, salt: bytes | None = None) -> dict:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return {"salt": salt.hex(), "hash": digest.hex(), "iterations": PBKDF2_ITERATIONS}


def verify_password(password: str, config: dict) -> bool:
    try:
        salt = bytes.fromhex(config["salt"])
        expected = bytes.fromhex(config["hash"])
        iterations = int(config.get("iterations", PBKDF2_ITERATIONS))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except (KeyError, ValueError, TypeError):
        return False


def save_config(config: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp = CONFIG_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(temp, 0o600)
    except OSError:
        pass
    temp.replace(CONFIG_PATH)


def load_or_create_config(explicit_password: str | None, set_password: str | None) -> tuple[dict, str | None]:
    if CONFIG_PATH.exists():
        try:
            config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if not isinstance(config, dict) or "hash" not in config or "salt" not in config:
                raise ValueError("Неверный формат конфигурации сервера")
        except Exception as exc:
            raise SystemExit(f"Не удалось прочитать {CONFIG_PATH}: {exc}")
        if set_password:
            if len(set_password) < 10:
                raise SystemExit("Новый пароль должен содержать не менее 10 символов.")
            config = hash_password(set_password)
            save_config(config)
            print("Пароль сервера успешно изменён.")
        elif explicit_password:
            print("Внимание: --password применяется только при первом запуске. Для смены существующего пароля используй --set-password.")
        return config, None

    password = set_password or explicit_password or os.environ.get("ORBIT_PASSWORD")
    generated = False
    if not password:
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789-_!"
        password = "".join(secrets.choice(alphabet) for _ in range(20))
        generated = True
    if len(password) < 10:
        raise SystemExit("Пароль должен содержать не менее 10 символов.")
    config = hash_password(password)
    save_config(config)
    return config, password if generated else None


def db_connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db_session():
    conn = db_connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db_session() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS app_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            state_json TEXT NOT NULL,
            revision INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            revision INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            reason TEXT NOT NULL,
            state_json TEXT NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_created ON snapshots(created_at DESC)")


def json_response(handler: "OrbitHandler", status: int, payload: dict, headers: dict | None = None) -> None:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
    handler.send_header("Pragma", "no-cache")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("Referrer-Policy", "same-origin")
    if headers:
        for key, value in headers.items():
            handler.send_header(key, value)
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: "OrbitHandler") -> dict | None:
    try:
        length = int(handler.headers.get("Content-Length", "0"))
    except ValueError:
        json_response(handler, 400, {"error": "Некорректный Content-Length."})
        return None
    if length <= 0 or length > MAX_BODY:
        json_response(handler, 413 if length > MAX_BODY else 400, {"error": "Пустой запрос или превышен лимит 80 МБ."})
        return None
    try:
        raw = handler.rfile.read(length)
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        json_response(handler, 400, {"error": "Тело запроса должно быть корректным JSON в UTF-8."})
        return None
    if not isinstance(data, dict):
        json_response(handler, 400, {"error": "Ожидался JSON-объект."})
        return None
    return data


def validate_state(state: object) -> tuple[bool, str]:
    if not isinstance(state, dict):
        return False, "Поле state должно быть JSON-объектом."
    for key in ("tasks", "goals", "timeEntries"):
        if not isinstance(state.get(key), list):
            return False, f"В данных отсутствует массив {key}."
    if len(state["tasks"]) > 100_000 or len(state["goals"]) > 50_000 or len(state["timeEntries"]) > 500_000:
        return False, "Количество записей превышает допустимый предел."
    return True, ""


def current_state() -> tuple[dict, int, str, bool]:
    with db_session() as conn:
        row = conn.execute("SELECT state_json, revision, updated_at FROM app_state WHERE id=1").fetchone()
    if not row:
        return default_state(), 0, "", True
    return json.loads(row["state_json"]), int(row["revision"]), row["updated_at"], False


def token_from_request(handler: "OrbitHandler") -> str:
    auth = handler.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return ""
    return auth[7:].strip()


def authenticated(handler: "OrbitHandler") -> bool:
    token = token_from_request(handler)
    if not token:
        json_response(handler, 401, {"error": "Требуется вход в Orbit Server."})
        return False
    now = time.monotonic()
    with SESSION_LOCK:
        expires = SESSIONS.get(token)
        if not expires or expires < now:
            SESSIONS.pop(token, None)
            json_response(handler, 401, {"error": "Сессия истекла. Войди на сервер повторно."})
            return False
        SESSIONS[token] = now + SESSION_TTL_SECONDS
    return True


def login_allowed(ip: str) -> bool:
    now = time.monotonic()
    with LOGIN_LOCK:
        q = LOGIN_ATTEMPTS[ip]
        while q and now - q[0] > 300:
            q.popleft()
        return len(q) < 8


def record_login_failure(ip: str) -> None:
    with LOGIN_LOCK:
        LOGIN_ATTEMPTS[ip].append(time.monotonic())


class OrbitHandler(SimpleHTTPRequestHandler):
    server_version = "OrbitLAN/1.0"
    sys_version = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        sys.stdout.write(f"[{self.log_date_time_string()}] {self.client_address[0]} {fmt % args}\n")

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        super().end_headers()

    def list_directory(self, path):
        self.send_error(HTTPStatus.FORBIDDEN, "Directory listing disabled")
        return None

    def translate_path(self, path: str) -> str:
        translated = super().translate_path(path)
        try:
            relative = Path(translated).resolve().relative_to(ROOT.resolve())
        except (ValueError, OSError):
            return str(ROOT / "__forbidden__")
        if not relative.parts:
            return str(ROOT / "index.html")
        first = relative.parts[0].lower()
        if first in {"data", ".git", "server.py", "start-server.bat", "start-server.sh"}:
            return str(ROOT / "__forbidden__")
        if any(part.startswith(".") for part in relative.parts):
            return str(ROOT / "__forbidden__")
        return translated

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/health":
            json_response(self, 200, {"app": APP_NAME, "version": 1, "storage": "sqlite", "auth": "password"})
            return
        if path == "/api/state":
            if not authenticated(self):
                return
            state, revision, updated_at, is_new = current_state()
            json_response(self, 200, {"state": state, "revision": revision, "updatedAt": updated_at, "isNew": is_new})
            return
        if path == "/api/export":
            if not authenticated(self):
                return
            state, revision, updated_at, _ = current_state()
            payload = {"app": "Orbit Productivity Tracker", "schemaVersion": SCHEMA_VERSION, "exportedAt": utc_now(), "serverRevision": revision, "serverUpdatedAt": updated_at, "state": state}
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="orbit-server-backup-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json"')
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/backups":
            if not authenticated(self):
                return
            with db_session() as conn:
                rows = conn.execute("SELECT id, revision, created_at, reason FROM snapshots ORDER BY id DESC LIMIT 30").fetchall()
            json_response(self, 200, {"items": [dict(row) for row in rows]})
            return
        if path.startswith("/api/"):
            json_response(self, 404, {"error": "API endpoint not found."})
            return
        super().do_GET()

    def do_POST(self):
        path = urlsplit(self.path).path
        data = read_json(self)
        if data is None:
            return
        if path == "/api/login":
            ip = self.client_address[0]
            if not login_allowed(ip):
                json_response(self, 429, {"error": "Слишком много попыток входа. Подожди 5 минут."})
                return
            password = str(data.get("password", ""))
            if not verify_password(password, self.server.password_config):
                record_login_failure(ip)
                json_response(self, 401, {"error": "Неверный пароль."})
                return
            token = secrets.token_urlsafe(36)
            with SESSION_LOCK:
                SESSIONS[token] = time.monotonic() + SESSION_TTL_SECONDS
            with LOGIN_LOCK:
                LOGIN_ATTEMPTS.pop(ip, None)
            json_response(self, 200, {"token": token, "expiresIn": SESSION_TTL_SECONDS})
            return
        if path == "/api/snapshot":
            if not authenticated(self):
                return
            state, revision, _, is_new = current_state()
            if is_new:
                json_response(self, 409, {"error": "На сервере пока нет сохранённых данных."})
                return
            reason = str(data.get("reason") or "Ручная копия")[:100]
            with db_session() as conn:
                conn.execute("INSERT INTO snapshots(revision, created_at, reason, state_json) VALUES(?,?,?,?)", (revision, utc_now(), reason, json.dumps(state, ensure_ascii=False)))
                conn.execute("DELETE FROM snapshots WHERE id NOT IN (SELECT id FROM snapshots ORDER BY id DESC LIMIT 30)")
            json_response(self, 201, {"ok": True, "revision": revision})
            return
        json_response(self, 404, {"error": "API endpoint not found."})

    def do_PUT(self):
        path = urlsplit(self.path).path
        if path != "/api/state":
            json_response(self, 404, {"error": "API endpoint not found."})
            return
        if not authenticated(self):
            return
        data = read_json(self)
        if data is None:
            return
        new_state = data.get("state")
        ok, reason = validate_state(new_state)
        if not ok:
            json_response(self, 400, {"error": reason})
            return
        try:
            base_revision = int(data.get("baseRevision", -1))
        except (TypeError, ValueError):
            json_response(self, 400, {"error": "baseRevision должен быть целым числом."})
            return
        serialized = json.dumps(new_state, ensure_ascii=False, separators=(",", ":"))
        now = utc_now()
        try:
            conn = db_connect()
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT state_json, revision, updated_at FROM app_state WHERE id=1").fetchone()
            current_revision = int(row["revision"]) if row else 0
            if base_revision != current_revision:
                conn.rollback()
                json_response(self, 409, {"error": "Данные на сервере уже изменились с момента последней синхронизации.", "serverRevision": current_revision})
                return
            if row:
                last_snapshot = conn.execute("SELECT created_at FROM snapshots ORDER BY id DESC LIMIT 1").fetchone()
                snapshot_old = True
                if last_snapshot:
                    try:
                        last_dt = datetime.fromisoformat(last_snapshot["created_at"].replace("Z", "+00:00"))
                        snapshot_old = (datetime.now(timezone.utc) - last_dt).total_seconds() >= 12 * 60 * 60
                    except ValueError:
                        snapshot_old = True
                if snapshot_old:
                    conn.execute("INSERT INTO snapshots(revision, created_at, reason, state_json) VALUES(?,?,?,?)", (current_revision, now, "Автоматическая серверная копия", row["state_json"]))
                    conn.execute("DELETE FROM snapshots WHERE id NOT IN (SELECT id FROM snapshots ORDER BY id DESC LIMIT 30)")
                new_revision = current_revision + 1
                conn.execute("UPDATE app_state SET state_json=?, revision=?, updated_at=? WHERE id=1", (serialized, new_revision, now))
            else:
                new_revision = 1
                conn.execute("INSERT INTO app_state(id, state_json, revision, updated_at) VALUES(1,?,?,?)", (serialized, new_revision, now))
            conn.commit()
            conn.close()
        except sqlite3.Error as exc:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            json_response(self, 500, {"error": f"Ошибка SQLite: {exc}"})
            return
        json_response(self, 200, {"ok": True, "revision": new_revision, "updatedAt": now})

    def do_OPTIONS(self):
        json_response(self, 405, {"error": "CORS и внешние источники не поддерживаются. Открой Orbit с адреса локального сервера."})


class OrbitHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def lan_addresses() -> list[str]:
    found = set()
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_STREAM):
            ip = item[4][0]
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                found.add(ip)
    except OSError:
        pass
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("192.0.2.1", 80))
        ip = sock.getsockname()[0]
        sock.close()
        if ip and not ip.startswith("127."):
            found.add(ip)
    except OSError:
        pass
    return sorted(found)


def main() -> None:
    parser = argparse.ArgumentParser(description="Orbit — сервер локальной сети")
    parser.add_argument("--host", default="0.0.0.0", help="Адрес привязки (по умолчанию доступен в локальной сети)")
    parser.add_argument("--port", type=int, default=8765, help="Порт сервера (по умолчанию 8765)")
    parser.add_argument("--password", help="Пароль для первого запуска")
    parser.add_argument("--set-password", help="Заменить сохранённый пароль")
    args = parser.parse_args()
    if not (1 <= args.port <= 65535):
        parser.error("Порт должен быть в диапазоне 1–65535.")
    config, generated_password = load_or_create_config(args.password, args.set_password)
    init_db()
    httpd = OrbitHTTPServer((args.host, args.port), OrbitHandler)
    httpd.password_config = config
    print("\nOrbit Server запущен.")
    print(f"На этом компьютере: http://127.0.0.1:{args.port}")
    for ip in lan_addresses():
        print(f"В локальной сети:   http://{ip}:{args.port}")
    if generated_password:
        print("\nСОХРАНИ ПАРОЛЬ СЕЙЧАС — он больше не будет показан автоматически:")
        print(f"  {generated_password}\n")
    print(f"База данных: {DB_PATH}")
    print("Останавливай сервер сочетанием Ctrl+C. Не открывай порт на роутере и не выставляй этот сервер в интернет.\n")
    try:
        httpd.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\nОстановка Orbit Server...")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
