#!/bin/bash

if [ "$(id -u)" -ne 0 ]; then
    echo "Этот скрипт должен быть запущен с правами root (sudo)"
    exit 1
fi

GLOWCODE_BIN="dist/glowcode"
GLOWCODE_ICON="glowcode.png"

if [ ! -f "$GLOWCODE_BIN" ]; then
    echo "Ошибка: Файл $GLOWCODE_BIN не найден в текущей директории"
    echo "Поместите этот скрипт в ту же папку, где находится собранный glowcode"
    exit 1
fi

INSTALL_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/"

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

echo "Установка завершена!"
echo "Теперь вы можете запускать редактор командой: glowcode"
