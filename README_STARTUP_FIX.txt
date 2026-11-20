Orbit LAN - Windows launcher fix
================================

This patch replaces only start-server.bat. It fixes Windows CMD parsing by:
- using Windows CRLF line endings;
- using ASCII-only batch commands and messages;
- avoiding parenthesized IF blocks;
- checking for py.exe first and falling back to python.exe.

Install:
1. Stop any running Orbit server (Ctrl+C).
2. Copy start-server.bat from this archive into the Orbit project folder,
   next to server.py and index.html.
3. Replace the existing start-server.bat when Windows asks.
4. Double-click the new start-server.bat.

The patch does not replace server.py, index.html, sw.js, the database,
MathJax files, icons, or other project files.

If Python is not found, install Python 3.9 or newer and enable
"Add Python to PATH" in the installer, then reopen the terminal/window.
