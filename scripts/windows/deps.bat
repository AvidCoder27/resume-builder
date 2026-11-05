@echo off
rem Shared helper: ensures Python, Pandoc, and wkhtmltopdf are available,
rem running install.bat if any are missing. Sets PY on success.
rem Call without setlocal so PATH/PY changes reach the caller.

call :detect
if not defined MISSING exit /b 0

echo Missing dependencies detected. Running installer...
call "%~dp0install.bat" /quiet
call :refresh_path
call :detect
if defined MISSING (
  echo Still missing after install: %MISSING%
  echo Close this window, open a new terminal, and try again.
  exit /b 1
)
exit /b 0

:detect
set "MISSING="
set "PY="
python --version >nul 2>&1 && set "PY=python"
if not defined PY py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY set "MISSING=%MISSING% python"
where pandoc >nul 2>&1 || set "MISSING=%MISSING% pandoc"
where wkhtmltopdf >nul 2>&1
if errorlevel 1 (
  if exist "%ProgramFiles%\wkhtmltopdf\bin\wkhtmltopdf.exe" (
    set "PATH=%PATH%;%ProgramFiles%\wkhtmltopdf\bin"
  ) else (
    set "MISSING=%MISSING% wkhtmltopdf"
  )
)
exit /b 0

:refresh_path
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')"`) do set "PATH=%%P"
exit /b 0
