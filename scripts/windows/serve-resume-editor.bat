@echo off
setlocal
cd /d "%~dp0..\.."

call "%~dp0deps.bat" || goto :fail

set PYTHONUTF8=1
echo Open http://127.0.0.1:8765 in your browser. Press Ctrl+C to stop.
%PY% src\resume_editor_server.py
exit /b %errorlevel%

:fail
pause
exit /b 1
