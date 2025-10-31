# 🚀 Деплой на сервер

## Вариант 1: VPS (Рекомендуется)

### Требования
- Ubuntu 20.04+ / Debian 11+
- Python 3.9+
- Nginx
- Домен с SSL

### Пошаговая инструкция

#### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git

# Создание пользователя
sudo useradd -m -s /bin/bash gamebot
sudo su - gamebot
```

#### 2. Загрузка проекта

```bash
# Клонирование (или загрузка файлов)
cd /home/gamebot
# Скопируйте все файлы проекта сюда

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/gamebot
```

Вставьте:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
# Активация конфига
sudo ln -s /etc/nginx/sites-available/gamebot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. SSL сертификат

```bash
sudo certbot --nginx -d your-domain.com
```

#### 5. Systemd сервисы

**Flask (webapp.service)**
```bash
sudo nano /etc/systemd/system/gamebot-webapp.service
```

```ini
[Unit]
Description=Duck Game WebApp
After=network.target

[Service]
Type=simple
User=gamebot
WorkingDirectory=/home/gamebot/duck_game_bot
Environment="PATH=/home/gamebot/duck_game_bot/venv/bin"
ExecStart=/home/gamebot/duck_game_bot/venv/bin/python webapp.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Bot (bot.service)**
```bash
sudo nano /etc/systemd/system/gamebot-bot.service
```

```ini
[Unit]
Description=Duck Game Telegram Bot
After=network.target

[Service]
Type=simple
User=gamebot
WorkingDirectory=/home/gamebot/duck_game_bot
Environment="PATH=/home/gamebot/duck_game_bot/venv/bin"
ExecStart=/home/gamebot/duck_game_bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Запуск сервисов**
```bash
sudo systemctl daemon-reload
sudo systemctl enable gamebot-webapp gamebot-bot
sudo systemctl start gamebot-webapp gamebot-bot

# Проверка статуса
sudo systemctl status gamebot-webapp
sudo systemctl status gamebot-bot

# Логи
sudo journalctl -u gamebot-webapp -f
sudo journalctl -u gamebot-bot -f
```

#### 6. Обновление bot.py

```python
WEBAPP_URL = "https://your-domain.com"
ADMIN_IDS = [YOUR_TELEGRAM_ID]
```

#### 7. Перезапуск

```bash
sudo systemctl restart gamebot-webapp
sudo systemctl restart gamebot-bot
```

## Вариант 2: Heroku (Бесплатно для начала)

### Установка

```bash
# Установка Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh
heroku login
```

### Подготовка проекта

**Procfile**
```
web: python webapp.py
worker: python bot.py
```

**runtime.txt**
```
python-3.11.0
```

**Обновление webapp.py**
```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

### Деплой

```bash
git init
heroku create your-app-name
git add .
git commit -m "Initial commit"
git push heroku main

# Запуск worker
heroku ps:scale web=1 worker=1

# Логи
heroku logs --tail
```

### Настройка переменных

```bash
heroku config:set BOT_TOKEN=your_token
heroku config:set WEBAPP_URL=https://your-app-name.herokuapp.com
```

## Вариант 3: Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  webapp:
    build: .
    command: python webapp.py
    ports:
      - "5000:5000"
    volumes:
      - ./game.db:/app/game.db
    restart: always

  bot:
    build: .
    command: python bot.py
    volumes:
      - ./game.db:/app/game.db
    depends_on:
      - webapp
    restart: always
    environment:
      - WEBAPP_URL=https://your-domain.com

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on:
      - webapp
    restart: always
```

### Запуск

```bash
docker-compose up -d
docker-compose logs -f
```

## Вариант 4: Railway.app (Простой)

1. Создайте аккаунт на railway.app
2. Подключите GitHub репозиторий
3. Railway автоматически определит Python проект
4. Добавьте переменные окружения:
   - `BOT_TOKEN`
   - `WEBAPP_URL` (будет сгенерирован Railway)
5. Деплой произойдет автоматически

## Вариант 5: Render.com

1. Создайте аккаунт на render.com
2. Создайте новый Web Service
3. Подключите репозиторий
4. Настройки:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python webapp.py`
5. Создайте Background Worker для бота:
   - Start Command: `python bot.py`

## Мониторинг и обслуживание

### Логирование

Добавьте в bot.py и webapp.py:

```python
import logging
from logging.handlers import RotatingFileHandler

# Настройка логирования
handler = RotatingFileHandler('app.log', maxBytes=10000000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Backup базы данных

```bash
# Создайте cron задачу
crontab -e

# Добавьте (backup каждый день в 3:00)
0 3 * * * cp /home/gamebot/duck_game_bot/game.db /home/gamebot/backups/game_$(date +\%Y\%m\%d).db
```

### Мониторинг с Prometheus (опционально)

**requirements.txt**
```
prometheus-client==0.18.0
```

**В webapp.py**
```python
from prometheus_client import Counter, Histogram, generate_latest

# Метрики
requests_total = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

## Проверка работоспособности

### Health check

Добавьте в webapp.py:

```python
@app.route('/health')
def health():
    # Проверка БД
    try:
        async with aiosqlite.connect(DATABASE) as db:
            await db.execute('SELECT 1')
        return {'status': 'ok', 'database': 'connected'}
    except:
        return {'status': 'error', 'database': 'disconnected'}, 500
```

### Uptime monitoring

Используйте сервисы:
- UptimeRobot (бесплатный)
- StatusCake
- Pingdom

Добавьте URL для мониторинга:
```
https://your-domain.com/health
```

## Масштабирование

### PostgreSQL вместо SQLite

```bash
pip install asyncpg
```

```python
import asyncpg

async def init_db():
    conn = await asyncpg.connect(
        host='localhost',
        database='gamebot',
        user='gamebot',
        password='password'
    )
    # ... создание таблиц
```

### Redis для кэширования

```bash
pip install redis aioredis
```

```python
import aioredis

redis = await aioredis.create_redis_pool('redis://localhost')

# Кэширование данных игрока
await redis.setex(f'player:{user_id}', 300, json.dumps(player_data))
```

### Load Balancer

Используйте несколько инстансов webapp.py за nginx/haproxy.

## Безопасность

### Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Fail2ban

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### Rate limiting в Nginx

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api {
    limit_req zone=api burst=20;
    proxy_pass http://127.0.0.1:5000;
}
```

## Troubleshooting

**502 Bad Gateway**
- Проверьте статус webapp: `sudo systemctl status gamebot-webapp`
- Проверьте логи: `sudo journalctl -u gamebot-webapp`

**База данных заблокирована**
- SQLite не подходит для высокой нагрузки
- Переходите на PostgreSQL

**Бот не отвечает**
- Проверьте статус: `sudo systemctl status gamebot-bot`
- Проверьте интернет соединение
- Проверьте токен бота

**HTTPS не работает**
- Проверьте сертификат: `sudo certbot certificates`
- Обновите сертификат: `sudo certbot renew`
