@echo off
setlocal
cd /d "%~dp0"

rem Prefer the Python launcher, then fall back to python.exe.
where.exe py.exe >nul 2>nul
if not errorlevel 1 goto use_py
where.exe python.exe >nul 2>nul
if not errorlevel 1 goto use_python
goto no_python

:use_py
py.exe -3 "%~dp0server.py" %*
goto finished

:use_python
python.exe "%~dp0server.py" %*
goto finished

:no_python
echo Python 3.9 or newer was not found.
echo Install Python from python.org and enable "Add Python to PATH".
set "ORBIT_EXIT_CODE=1"
goto show_result

:finished
set "ORBIT_EXIT_CODE=%ERRORLEVEL%"

:show_result
echo.
echo Orbit server process has stopped.
pause
exit /b %ORBIT_EXIT_CODE%
