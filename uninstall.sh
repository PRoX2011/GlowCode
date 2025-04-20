#!/bin/bash

if [ "$(id -u)" -ne 0 ]; then
    echo "Этот скрипт должен быть запущен с правами root (sudo)"
    exit 1
fi

echo "Удаляю glowcode из /usr/local/bin..."
rm -f /usr/local/bin/glowcode

echo "Удаляю ярлык приложения..."
rm -f /usr/share/applications/glowcode.desktop

echo "Удаляю иконку..."
rm -f /usr/share/icons/glowcode.png

if [ -f "/usr/local/bin/glowcode" ] || [ -f "/usr/share/applications/glowcode.desktop" ]; then
    echo "Предупреждение: Не все файлы были удалены"
else
    echo "GlowCode успешно удалён из системы"
fi
