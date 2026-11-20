@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 server.py
) else (
  python server.py
)
echo.
echo Orbit Server завершил работу. Нажми любую клавишу для закрытия окна.
pause >nul
