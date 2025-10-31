import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    WebAppInfo, MenuButtonWebApp
)
from aiogram.fsm.storage.memory import MemoryStorage
import aiosqlite
import json
from pathlib import Path

# Настройки
BOT_TOKEN = "8302634702:AAELmL4jv_yx9jRcvbrGBGQBKD4rcbET4fI"
WEBAPP_URL = "https://e10d344bb815f3.lhr.life"  # Новый URL! # Замените на ваш домен
ADMIN_IDS = [6827398433]  # ID администраторов

# Инициализация
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# База данных
DATABASE = "game.db"

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DATABASE) as db:
        # Таблица игроков
        await db.execute('''
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance REAL DEFAULT 0,
                stars INTEGER DEFAULT 0,
                ton_balance REAL DEFAULT 0,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned INTEGER DEFAULT 0,
                referrer_id INTEGER
            )
        ''')
        
        # Таблица бизнесов игрока
        await db.execute('''
            CREATE TABLE IF NOT EXISTS player_businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                business_id INTEGER,
                level INTEGER DEFAULT 1,
                last_claim TIMESTAMP,
                work_started_at TIMESTAMP,
                is_working INTEGER DEFAULT 0,
                total_earned REAL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        # Таблица предметов игрока
        await db.execute('''
            CREATE TABLE IF NOT EXISTS player_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_type TEXT,
                item_id INTEGER,
                item_name TEXT,
                purchase_price REAL,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        # Таблица маркетплейса
        await db.execute('''
            CREATE TABLE IF NOT EXISTS marketplace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER,
                item_id INTEGER,
                price REAL,
                currency TEXT DEFAULT 'game',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sold INTEGER DEFAULT 0,
                FOREIGN KEY (seller_id) REFERENCES players(user_id),
                FOREIGN KEY (item_id) REFERENCES player_items(id)
            )
        ''')
        
        # Таблица транзакций
        await db.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount REAL,
                currency TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        # Таблица боксов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS box_openings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                box_type TEXT,
                reward TEXT,
                reward_value REAL,
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        await db.commit()

async def get_or_create_player(user_id: int, username: str = None, first_name: str = None, referrer_id: int = None):
    """Получить или создать игрока"""
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('SELECT * FROM players WHERE user_id = ?', (user_id,)) as cursor:
            player = await cursor.fetchone()
        
        if not player:
            # Создаем нового игрока
            await db.execute('''
                INSERT INTO players (user_id, username, first_name, referrer_id) 
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, referrer_id))
            
            # Даем стартовый бизнес
            await db.execute('''
                INSERT INTO player_businesses (user_id, business_id, level) 
                VALUES (?, 1, 1)
            ''', (user_id,))
            
            await db.commit()
            
            # Если есть реферер, даем бонус
            if referrer_id:
                await db.execute('''
                    UPDATE players SET balance = balance + 100 
                    WHERE user_id = ?
                ''', (referrer_id,))
                await db.commit()
        
        # Обновляем активность
        await db.execute('''
            UPDATE players SET last_active = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        ''', (user_id,))
        await db.commit()

# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Проверяем реферальную ссылку
    referrer_id = None
    if message.text and len(message.text.split()) > 1:
        ref_code = message.text.split()[1]
        if ref_code.startswith('r'):
            try:
                referrer_id = int(ref_code[1:], 16)
            except:
                pass
    
    # Создаем или получаем игрока
    await get_or_create_player(user_id, username, first_name, referrer_id)
    
    # Создаем клавиатуру с Web App
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎮 Играть",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}/game?user_id={user_id}")
        )],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ])
    
    welcome_text = f"""
🦆 <b>Добро пожаловать в Duck Business!</b>

Привет, {first_name}! 

<b>Как играть:</b>
• Управляйте бизнесами
• Зарабатывайте игровую валюту
• Покупайте предметы (машины, квартиры)
• Торгуйте на маркетплейсе
• Открывайте боксы

Нажмите "🎮 Играть" чтобы начать!
    """
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data == "help")
async def help_callback(callback: types.CallbackQuery):
    """Справка"""
    help_text = """
📖 <b>Помощь</b>

<b>Бизнесы:</b>
• Каждый бизнес работает 4 часа
• После окончания собирайте прибыль
• Улучшайте бизнесы для большего дохода

<b>Предметы:</b>
• Покупайте машины, квартиры и другое
• Продавайте на маркетплейсе другим игрокам

<b>Боксы:</b>
• Открывайте боксы за игровую валюту
• Получайте случайные награды

<b>Валюта:</b>
• Игровая валюта - зарабатывайте в игре
• TON - пополняйте и выводите
• Stars - покупайте за Telegram Stars
    """
    await callback.message.answer(help_text, parse_mode="HTML")
    await callback.answer()

# Админ команды
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Админ панель"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🎁 Выдать бонус", callback_data="admin_bonus")],
        [InlineKeyboardButton(text="🚫 Забанить", callback_data="admin_ban")],
        [InlineKeyboardButton(text="✅ Разбанить", callback_data="admin_unban")]
    ])
    
    await message.answer("🔧 <b>Админ панель</b>", reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    """Статистика"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    async with aiosqlite.connect(DATABASE) as db:
        # Общее количество игроков
        async with db.execute('SELECT COUNT(*) FROM players') as cursor:
            total_players = (await cursor.fetchone())[0]
        
        # Активные сегодня
        async with db.execute('''
            SELECT COUNT(*) FROM players 
            WHERE date(last_active) = date('now')
        ''') as cursor:
            active_today = (await cursor.fetchone())[0]
        
        # Всего заработано
        async with db.execute('SELECT SUM(total_earned) FROM player_businesses') as cursor:
            total_earned = (await cursor.fetchone())[0] or 0
    
    stats_text = f"""
📊 <b>Статистика</b>

👥 Всего игроков: {total_players}
🟢 Активных сегодня: {active_today}
💰 Всего заработано: {total_earned:.2f}
    """
    
    await callback.message.answer(stats_text, parse_mode="HTML")
    await callback.answer()

# API для Web App
async def api_get_player(user_id: int):
    """Получить данные игрока"""
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute('SELECT * FROM players WHERE user_id = ?', (user_id,)) as cursor:
            player = await cursor.fetchone()
        
        if not player:
            return None
        
        # Получаем бизнесы
        async with db.execute('''
            SELECT * FROM player_businesses WHERE user_id = ?
        ''', (user_id,)) as cursor:
            businesses = await cursor.fetchall()
        
        # Получаем предметы
        async with db.execute('''
            SELECT * FROM player_items WHERE user_id = ?
        ''', (user_id,)) as cursor:
            items = await cursor.fetchall()
        
        return {
            'player': dict(player),
            'businesses': [dict(b) for b in businesses],
            'items': [dict(i) for i in items]
        }

async def main():
    """Запуск бота"""
    await init_db()
    print("✅ База данных инициализирована")
    print("🚀 Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
