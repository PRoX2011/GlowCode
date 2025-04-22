@echo off
chcp 1251 >nul

REM Проверка доступности файла открытия
openfiles >nul 2>&1
if %errorlevel% NEQ 0 (
    echo Please run this script as administrator!
    pause
    exit /b 1
)

set "INSTALL_DIR=%ProgramFiles%\GlowCode"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\GlowCode.lnk"

echo Removing GlowCode from %INSTALL_DIR% ...
del /F /Q "%INSTALL_DIR%\glowcode.exe"
del /F /Q "%INSTALL_DIR%\glowcode.png"

echo Removing a shortcut from the desktop ...
del /F /Q "%SHORTCUT%"

REM Удаление папки, если она пуста или существует
rmdir "%INSTALL_DIR%" 2>nul

echo Removal completed!
pause
