@echo off
chcp 1251 >nul

REM Проверка доступности файла открытия
openfiles >nul 2>&1
if %errorlevel% NEQ 0 (
    echo Пожалуйста, запустите этот скрипт от имени администратора!
    pause
    exit /b 1
)

set "INSTALL_DIR=%ProgramFiles%\GlowCode"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\GlowCode.lnk"

echo Удаление GlowCode из %INSTALL_DIR% ...
del /F /Q "%INSTALL_DIR%\glowcode.exe"
del /F /Q "%INSTALL_DIR%\glowcode.png"

echo Удаление ярлыка с рабочего стола ...
del /F /Q "%SHORTCUT%"

REM Удаление папки, если она пуста или существует
rmdir "%INSTALL_DIR%" 2>nul

echo Удаление завершено!
pause
