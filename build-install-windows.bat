@echo off
cd /d %~dp0
chcp 1251 >nul
REM Сборка GlowCode для Windows
pyinstaller -D -F -n glowcode -w --onefile --noconsole "GlowCode.py" --distpath build/glowcode
if %errorlevel% NEQ 0 (
    echo Ошибка сборки!
    pause
    exit /b 1
)

REM Проверка наличия прав администратора
openfiles >nul 2>&1
if %errorlevel% NEQ 0 (
    echo Запустите этот скрипт от имени администратора!
    pause
    exit /b 1
)

set "GLOWCODE_BIN=build\glowcode\glowcode.exe"
set "GLOWCODE_ICON=glowcode.png"
set "GLOWCODE_ICO=glowcode.ico"
set "INSTALL_DIR=%ProgramFiles%\GlowCode"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\GlowCode.lnk"

if not exist "%GLOWCODE_BIN%" (
    echo Файл %GLOWCODE_BIN% не найден. Сборка не удалась.
    pause
    exit /b 1
)

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy /Y "%GLOWCODE_BIN%" "%INSTALL_DIR%\glowcode.exe" >nul
copy /Y "%GLOWCODE_ICON%" "%INSTALL_DIR%\glowcode.png" >nul
copy /Y "%GLOWCODE_ICO%" "%INSTALL_DIR%\glowcode.ico" >nul

REM Создание ярлыка на рабочем столе
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%');$s.TargetPath='%INSTALL_DIR%\glowcode.exe';$s.IconLocation='%INSTALL_DIR%\glowcode.ico';$s.Save()"

REM Добавление ярлыка в меню Пуск
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "STARTMENU_SHORTCUT=%STARTMENU%\GlowCode.lnk"
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTMENU_SHORTCUT%');$s.TargetPath='%INSTALL_DIR%\glowcode.exe';$s.IconLocation='%INSTALL_DIR%\glowcode.ico';$s.Save()"

echo Сборка и установка завершены.
pause
