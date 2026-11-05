@echo off
setlocal
cd /d "%~dp0..\.."

call "%~dp0deps.bat" || goto :fail

set PYTHONUTF8=1
%PY% -c "import sys; sys.path.insert(0, 'src'); import resume_editor_server as server; server.ensure_resume_files(); server.render_resume()"
if errorlevel 1 goto :fail
exit /b 0

:fail
pause
exit /b 1
