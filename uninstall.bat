@echo off
chcp 1251 >nul
REM Проверка наличия прав администратора
openfiles >nul 2>&1
if %errorlevel% NEQ 0 (
    echo Запустите этот скрипт от имени администратора!
    pause
    exit /b 1
)

set "INSTALL_DIR=%ProgramFiles%\GlowCode"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\GlowCode.lnk"

echo Удаляю GlowCode из %INSTALL_DIR% ...
del /F /Q "%INSTALL_DIR%\glowcode.exe"
del /F /Q "%INSTALL_DIR%\glowcode.png"

echo Удаляю ярлык с рабочего стола ...
del /F /Q "%SHORTCUT%"

REM Удаляем папку, если она пуста
rmdir "%INSTALL_DIR%" 2>nul

echo Удаление завершено!
pause
