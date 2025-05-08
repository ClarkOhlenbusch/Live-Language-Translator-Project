@echo off
echo Starting Live Language Translator...

:: Check if npm is installed
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: npm is not installed. Please install Node.js and npm.
    pause
    exit /b 1
)

:: Change to the project directory
cd %~dp0

:: Run the setup script if first time or if requested
if "%1"=="--setup" (
    echo Running setup...
    call npm run setup
) else (
    :: Check if node_modules exists, if not, run setup
    if not exist "node_modules" (
        echo First-time setup detected, installing dependencies...
        call npm run setup
    )
)

:: Run the application
echo Starting the application...
call npm start

pause 