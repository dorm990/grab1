# Duck Business Game - Telegram Mini App

## 🎮 Описание
Idle-игра для Telegram с бизнесами, магазином, маркетплейсом и боксами.

## ⚙️ Возможности
- ✅ Автоматический заработок от бизнесов (4 часа)
- ✅ Покупка и улучшение бизнесов
- ✅ Магазин предметов (машины, квартиры, другое)
- ✅ Маркетплейс для торговли между игроками
- ✅ Боксы с наградами
- ✅ База данных SQLite
- ✅ Таймеры работы бизнесов
- ✅ Реферальная система
- ✅ Админ-панель

## 📦 Установка

### 1. Установите зависимости
```bash
pip install -r requirements.txt
```

### 2. Настройте бота

В файле `bot.py` уже указан ваш токен бота:
```python
BOT_TOKEN = "8302634702:AAELmL4jv_yx9jRcvbrGBGQBKD4rcbET4fI"
```

Вам нужно заменить `WEBAPP_URL` и `ADMIN_IDS`:
```python
WEBAPP_URL = "https://your-domain.com"  # Ваш домен/ngrok URL
ADMIN_IDS = [YOUR_TELEGRAM_ID]  # Ваш Telegram ID
```

### 3. Запуск

#### Вариант 1: Локальный запуск с ngrok (для тестирования)

1. Установите ngrok: https://ngrok.com/download
2. Запустите веб-сервер:
```bash
python webapp.py
```

3. В другом терминале запустите ngrok:
```bash
ngrok http 5000
```

4. Скопируйте HTTPS URL из ngrok (например: https://abc123.ngrok.io)
5. Замените `WEBAPP_URL` в bot.py на этот URL
6. Запустите бота:
```bash
python bot.py
```

#### Вариант 2: Деплой на сервер

Для продакшна нужно развернуть на сервере с доменом и HTTPS:
- VPS (DigitalOcean, Hetzner, etc.)
- Nginx как reverse proxy
- SSL сертификат (Let's Encrypt)
- Systemd для автозапуска

## 🎯 Как играть

1. Откройте бота: https://t.me/YOUR_BOT_NAME
2. Нажмите /start
3. Нажмите кнопку "🎮 Играть"

### Механика:
- **Бизнесы**: Нажмите "Начать работу", подождите 4 часа, соберите прибыль
- **Магазин**: Покупайте предметы за игровую валюту
- **Маркетплейс**: Продавайте свои предметы другим игрокам
- **Боксы**: Открывайте боксы для получения случайных наград

## 🔧 Админ-панель

Команда `/admin` (доступна только для ID из ADMIN_IDS):
- 👥 Статистика игроков
- 🎁 Выдать бонус
- 🚫 Забанить игрока
- ✅ Разбанить игрока

## 💰 Монетизация (TODO)

Для добавления платежей нужно:

### TON:
1. Интегрировать TON Connect
2. Создать кошелек для приема платежей
3. Добавить обработчики платежей в webapp.py

### Telegram Stars:
1. Получить токен провайдера в @BotFather
2. Добавить в bot.py:
```python
PROVIDER_TOKEN = "your_provider_token"
```
3. Добавить обработчики PreCheckoutQuery и SuccessfulPayment

## 📁 Структура проекта

```
duck_game_bot/
├── bot.py              # Telegram бот
├── webapp.py           # Flask веб-сервер + API
├── templates/
│   └── game.html       # Интерфейс игры
├── game.db             # База данных (создается автоматически)
├── requirements.txt    # Зависимости
└── README.md          # Документация
```

## 🗄️ База данных

SQLite база с таблицами:
- `players` - игроки
- `player_businesses` - бизнесы игроков
- `player_items` - предметы игроков
- `marketplace` - маркетплейс
- `transactions` - транзакции
- `box_openings` - открытия боксов

## ⚡ API Endpoints

- `GET /api/player/<user_id>` - данные игрока
- `POST /api/business/start` - запустить бизнес
- `POST /api/business/claim` - собрать прибыль
- `POST /api/business/buy` - купить бизнес
- `POST /api/item/buy` - купить предмет
- `GET /api/marketplace/list` - список продаж
- `POST /api/marketplace/sell` - продать предмет
- `POST /api/marketplace/buy` - купить с маркетплейса
- `POST /api/box/open` - открыть бокс
- `GET /api/config` - конфигурация игры

## 🎨 Кастомизация

### Изменить бизнесы:
Отредактируйте `BUSINESSES` в `webapp.py`:
```python
BUSINESSES = {
    1: {"name": "🏪 Название", "price": 0, "income": 10, "time": 4},
    # ...
}
```

### Изменить предметы:
Отредактируйте `ITEMS` в `webapp.py`

### Изменить боксы:
Отредактируйте `BOXES` в `webapp.py`

## 🐛 Troubleshooting

**Ошибка "Table not found":**
Удалите `game.db` и перезапустите - база создастся заново

**Бот не отвечает:**
- Проверьте токен бота
- Убедитесь что бот запущен

**WebApp не открывается:**
- Проверьте WEBAPP_URL
- URL должен быть HTTPS
- Проверьте что Flask запущен

## 📝 TODO для улучшения

- [ ] Добавить платежи TON/Stars
- [ ] Улучшения бизнесов
- [ ] Ачивки и лидерборд
- [ ] Ежедневные бонусы
- [ ] Задания
- [ ] Друзья и кланы
- [ ] Больше предметов
- [ ] Анимации

## 🤝 Поддержка

Если нужна помощь с настройкой или доработкой - пишите!
