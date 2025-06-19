@echo off
REM Build script for Clipboard Refresher

REM Create build directory if it doesn't exist
if not exist "build" mkdir build

REM Clean previous build
rmdir /s /q build\ClipboardRefresher 2>nul
rmdir /s /q dist 2>nul

echo Building Clipboard Refresher...

REM Run PyInstaller
pyinstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --onefile ^
    --distpath "build" ^
    --workpath "build\temp" ^
    --specpath "build" ^
    --name "ClipboardRefresher" ^
    run.py

if %ERRORLEVEL% NEQ 0 (
    echo Build failed with error %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Build completed successfully!
echo Executable is located at: build\ClipboardRefresher\ClipboardRefresher.exe
echo.

REM Optionally, create a zip of the application
REM echo Creating ZIP archive...
REM powershell -Command "Compress-Archive -Path 'build\ClipboardRefresher\*' -DestinationPath 'build\ClipboardRefresher.zip' -Force"

echo Done.
pause
