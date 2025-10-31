#!/bin/bash

echo "🦆 Duck Business Game - Запуск"
echo "================================"
echo ""

# Проверка зависимостей
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не установлен"
    exit 1
fi

# Установка зависимостей если нужно
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo ""
echo "✅ Зависимости установлены"
echo ""

# Запуск Flask в фоне
echo "🌐 Запуск веб-сервера..."
python webapp.py &
FLASK_PID=$!

# Ждем запуска Flask
sleep 3

# Запуск бота
echo "🤖 Запуск Telegram бота..."
python bot.py &
BOT_PID=$!

echo ""
echo "================================"
echo "✅ Все запущено!"
echo ""
echo "📝 Процессы:"
echo "   Flask: PID $FLASK_PID"
echo "   Bot: PID $BOT_PID"
echo ""
echo "🛑 Для остановки нажмите Ctrl+C"
echo ""

# Обработка Ctrl+C
trap "echo ''; echo '🛑 Остановка...'; kill $FLASK_PID $BOT_PID; exit" INT

# Ждем
wait
