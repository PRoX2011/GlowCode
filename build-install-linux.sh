#!/bin/bash

# Сборка
pyinstaller -D -F -n glowcode -w --onefile --noconsole "GlowCode.py"
if [ $? -ne 0 ]; then
    echo "Ошибка сборки!"
    exit 1
fi

# Установка (требует root)
if [ "$(id -u)" -ne 0 ]; then
    echo "Этот скрипт должен быть запущен с правами root (sudo)"
    exit 1
fi

GLOWCODE_BIN="dist/glowcode"
GLOWCODE_ICON="glowcode.png"
INSTALL_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/"

if [ ! -f "$GLOWCODE_BIN" ]; then
    echo "Ошибка: Файл $GLOWCODE_BIN не найден после сборки"
    exit 1
fi

echo "Устанавливаю glowcode в $INSTALL_DIR..."
cp "$GLOWCODE_BIN" "$INSTALL_DIR/glowcode"
chmod +x "$INSTALL_DIR/glowcode"

echo "Устанавливаю иконку программы..."
cp "$GLOWCODE_ICON" "$ICON_DIR/glowcode.png"

echo "Создаю ярлык для рабочего стола..."
cat > "$DESKTOP_DIR/glowcode.desktop" <<EOL
[Desktop Entry]
Name=GlowCode
Comment=Code Editor with Syntax Highlighting
Exec=glowcode
Icon=/usr/share/icons/glowcode.png
Terminal=false
Type=Application
Categories=Development;TextEditor;
EOL

echo "Сборка и установка завершены!"
