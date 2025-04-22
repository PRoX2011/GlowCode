@echo off
cd /d %~dp0
chcp 1251 >nul

REM Компиляция GlowCode с помощью PyInstaller для Windows
pyinstaller -D -F -n glowcode -w --onefile --noconsole "GlowCode.py" --distpath build/glowcode
if %errorlevel% NEQ 0 (
    echo Compilation error!
    pause
    exit /b 1
)

REM Проверка доступности файла glowcode.exe
openfiles >nul 2>&1
if %errorlevel% NEQ 0 (
    echo Please unblock the file or close all programs using the files.
    pause
    exit /b 1
)

set "GLOWCODE_BIN=build\glowcode\glowcode.exe"
set "GLOWCODE_ICON=glowcode.png"
set "GLOWCODE_ICO=glowcode.ico"
set "INSTALL_DIR=%ProgramFiles%\GlowCode"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\GlowCode.lnk"

REM Проверка существования файла glowcode.exe
if not exist "%GLOWCODE_BIN%" (
    echo File %GLOWCODE_BIN% not found. Unable to install.
    pause
    exit /b 1
)

REM Создание папки для установки, если она не существует
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Копирование файлов в папку установки
copy /Y "%GLOWCODE_BIN%" "%INSTALL_DIR%\glowcode.exe" >nul
copy /Y "%GLOWCODE_ICON%" "%INSTALL_DIR%\glowcode.png" >nul
copy /Y "%GLOWCODE_ICO%" "%INSTALL_DIR%\glowcode.ico" >nul

REM Создание ярлыка на рабочем столе
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%');$s.TargetPath='%INSTALL_DIR%\glowcode.exe';$s.IconLocation='%INSTALL_DIR%\glowcode.ico';$s.Save()"

REM Создание ярлыка в меню Пуск
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "STARTMENU_SHORTCUT=%STARTMENU%\GlowCode.lnk"
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTMENU_SHORTCUT%');$s.TargetPath='%INSTALL_DIR%\glowcode.exe';$s.IconLocation='%INSTALL_DIR%\glowcode.ico';$s.Save()"

echo Installation and creation of shortcuts completed successfully.
pause
