@echo off
setlocal
cd /d "%~dp0..\.."
set "QUIET="
if /i "%~1"=="/quiet" set "QUIET=1"

where winget >nul 2>&1
if errorlevel 1 (
  echo winget not found. Install "App Installer" from the Microsoft Store, or install
  echo Python 3, Pandoc, and wkhtmltopdf manually.
  goto :fail
)

echo Installing Python, Pandoc, and wkhtmltopdf...
call :install Python.Python.3.12
call :install JohnMacFarlane.Pandoc
call :install wkhtmltopdf.wkhtmltopdf

echo.
echo Done. Close and reopen your terminal so PATH updates take effect,
echo then run serve-resume-editor.bat.
if not defined QUIET pause
exit /b 0

:install
winget list --id %1 -e >nul 2>&1
if not errorlevel 1 (
  echo %1 already installed.
  exit /b 0
)
winget install --id %1 -e --accept-package-agreements --accept-source-agreements
exit /b 0

:fail
if not defined QUIET pause
exit /b 1
