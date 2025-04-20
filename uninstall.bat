@echo off
chcp 1251 >nul
REM �������� ������� ���� ��������������
openfiles >nul 2>&1
if %errorlevel% NEQ 0 (
    echo ��������� ���� ������ �� ����� ��������������!
    pause
    exit /b 1
)

set "INSTALL_DIR=%ProgramFiles%\GlowCode"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\GlowCode.lnk"

echo ������ GlowCode �� %INSTALL_DIR% ...
del /F /Q "%INSTALL_DIR%\glowcode.exe"
del /F /Q "%INSTALL_DIR%\glowcode.png"

echo ������ ����� � �������� ����� ...
del /F /Q "%SHORTCUT%"

REM ������� �����, ���� ��� �����
rmdir "%INSTALL_DIR%" 2>nul

echo �������� ���������!
pause
