from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import aiosqlite
import asyncio
from datetime import datetime, timedelta
import json
import random

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Добавьте эту строку!

DATABASE = "game.db"

# Конфигурация игры
BUSINESSES = {
    1: {"name": "🏪 Киоск", "price": 0, "income": 10, "time": 4},
    2: {"name": "🍔 Кафе", "price": 500, "income": 50, "time": 4},
    3: {"name": "🏪 Магазин", "price": 2000, "income": 150, "time": 4},
    4: {"name": "🏭 Завод", "price": 10000, "income": 500, "time": 4},
    5: {"name": "🏢 Офис", "price": 50000, "income": 2000, "time": 4},
    6: {"name": "🏦 Банк", "price": 200000, "income": 8000, "time": 4},
}

ITEMS = {
    "cars": {
        1: {"name": "🚗 ВАЗ 2107", "price": 300},
        2: {"name": "🚙 Toyota Camry", "price": 1500},
        3: {"name": "🏎️ BMW M5", "price": 5000},
        4: {"name": "🚘 Mercedes S-Class", "price": 15000},
        5: {"name": "🏎️ Lamborghini", "price": 50000},
    },
    "apartments": {
        1: {"name": "🏠 Комната", "price": 800},
        2: {"name": "🏘️ Однушка", "price": 3000},
        3: {"name": "🏡 Двушка", "price": 8000},
        4: {"name": "🏰 Трешка", "price": 20000},
        5: {"name": "🏰 Пентхаус", "price": 100000},
    },
    "other": {
        1: {"name": "⌚ Часы Casio", "price": 200},
        2: {"name": "⌚ Rolex", "price": 5000},
        3: {"name": "💼 Портфель", "price": 500},
        4: {"name": "👔 Костюм", "price": 1000},
    }
}

BOXES = {
    "bronze": {"name": "📦 Бронзовый бокс", "price": 100, "rewards": [(10, 50), (20, 100), (30, 150)]},
    "silver": {"name": "📦 Серебряный бокс", "price": 500, "rewards": [(50, 300), (100, 500), (150, 800)]},
    "gold": {"name": "📦 Золотой бокс", "price": 2000, "rewards": [(500, 1500), (1000, 2500), (1500, 4000)]},
}

def run_async(coro):
    """Запуск асинхронной функции"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def get_player_data(user_id):
    """Получить данные игрока"""
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        
        # Игрок
        async with db.execute('SELECT * FROM players WHERE user_id = ?', (user_id,)) as cursor:
            player = await cursor.fetchone()
            if not player:
                return None
            player = dict(player)
        
        # Бизнесы
        async with db.execute('SELECT * FROM player_businesses WHERE user_id = ?', (user_id,)) as cursor:
            businesses = [dict(row) for row in await cursor.fetchall()]
        
        # Предметы
        async with db.execute('SELECT * FROM player_items WHERE user_id = ?', (user_id,)) as cursor:
            items = [dict(row) for row in await cursor.fetchall()]
        
        return {
            'player': player,
            'businesses': businesses,
            'items': items
        }

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/game')
def game():
    """Игровая страница"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return "User ID not provided", 400
    return render_template('game.html', user_id=user_id)

@app.route('/api/player/<int:user_id>')
def api_player(user_id):
    """API: получить данные игрока"""
    data = run_async(get_player_data(user_id))
    if not data:
        return jsonify({'error': 'Player not found'}), 404
    return jsonify(data)

@app.route('/api/business/start', methods=['POST'])
def api_business_start():
    """API: запустить бизнес"""
    data = request.json
    user_id = data.get('user_id')
    business_db_id = data.get('business_id')
    
    async def start_business():
        async with aiosqlite.connect(DATABASE) as db:
            # Проверяем, не работает ли уже
            async with db.execute('''
                SELECT * FROM player_businesses 
                WHERE id = ? AND user_id = ?
            ''', (business_db_id, user_id)) as cursor:
                business = await cursor.fetchone()
            
            if not business:
                return {'error': 'Business not found'}, 404
            
            if business[4]:  # is_working
                return {'error': 'Business already working'}, 400
            
            # Запускаем
            now = datetime.now().isoformat()
            await db.execute('''
                UPDATE player_businesses 
                SET is_working = 1, work_started_at = ? 
                WHERE id = ?
            ''', (now, business_db_id))
            await db.commit()
            
            return {'success': True, 'started_at': now}
    
    result = run_async(start_business())
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)

@app.route('/api/business/claim', methods=['POST'])
def api_business_claim():
    """API: собрать прибыль"""
    data = request.json
    user_id = data.get('user_id')
    business_db_id = data.get('business_id')
    
    async def claim_business():
        async with aiosqlite.connect(DATABASE) as db:
            # Получаем бизнес
            async with db.execute('''
                SELECT * FROM player_businesses 
                WHERE id = ? AND user_id = ?
            ''', (business_db_id, user_id)) as cursor:
                row = await cursor.fetchone()
            
            if not row:
                return {'error': 'Business not found'}, 404
            
            business_id = row[2]
            work_started = row[4]
            is_working = row[5]
            
            if not is_working or not work_started:
                return {'error': 'Business not working'}, 400
            
            # Проверяем время
            start_time = datetime.fromisoformat(work_started)
            now = datetime.now()
            hours_passed = (now - start_time).total_seconds() / 3600
            
            if hours_passed < 4:
                return {'error': f'Wait {4 - hours_passed:.1f} more hours'}, 400
            
            # Вычисляем прибыль
            business_config = BUSINESSES[business_id]
            income = business_config['income']
            
            # Обновляем баланс
            await db.execute('''
                UPDATE players 
                SET balance = balance + ? 
                WHERE user_id = ?
            ''', (income, user_id))
            
            # Обновляем бизнес
            await db.execute('''
                UPDATE player_businesses 
                SET is_working = 0, 
                    last_claim = ?, 
                    total_earned = total_earned + ?,
                    work_started_at = NULL
                WHERE id = ?
            ''', (now.isoformat(), income, business_db_id))
            
            await db.commit()
            
            return {'success': True, 'earned': income}
    
    result = run_async(claim_business())
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)

@app.route('/api/business/buy', methods=['POST'])
def api_business_buy():
    """API: купить новый бизнес"""
    data = request.json
    user_id = data.get('user_id')
    business_id = data.get('business_id')
    
    async def buy_business():
        async with aiosqlite.connect(DATABASE) as db:
            # Проверяем баланс
            async with db.execute('SELECT balance FROM players WHERE user_id = ?', (user_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return {'error': 'Player not found'}, 404
                balance = row[0]
            
            # Проверяем есть ли уже такой бизнес
            async with db.execute('''
                SELECT * FROM player_businesses 
                WHERE user_id = ? AND business_id = ?
            ''', (user_id, business_id)) as cursor:
                existing = await cursor.fetchone()
            
            if existing:
                return {'error': 'Already own this business'}, 400
            
            # Проверяем цену
            business_config = BUSINESSES.get(business_id)
            if not business_config:
                return {'error': 'Invalid business'}, 400
            
            price = business_config['price']
            if balance < price:
                return {'error': 'Not enough money'}, 400
            
            # Покупаем
            await db.execute('''
                UPDATE players SET balance = balance - ? WHERE user_id = ?
            ''', (price, user_id))
            
            await db.execute('''
                INSERT INTO player_businesses (user_id, business_id, level) 
                VALUES (?, ?, 1)
            ''', (user_id, business_id))
            
            await db.commit()
            
            return {'success': True, 'balance': balance - price}
    
    result = run_async(buy_business())
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)

@app.route('/api/item/buy', methods=['POST'])
def api_item_buy():
    """API: купить предмет"""
    data = request.json
    user_id = data.get('user_id')
    item_type = data.get('item_type')
    item_id = data.get('item_id')
    
    async def buy_item():
        async with aiosqlite.connect(DATABASE) as db:
            # Проверяем баланс
            async with db.execute('SELECT balance FROM players WHERE user_id = ?', (user_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return {'error': 'Player not found'}, 404
                balance = row[0]
            
            # Получаем предмет
            item_config = ITEMS.get(item_type, {}).get(item_id)
            if not item_config:
                return {'error': 'Invalid item'}, 400
            
            price = item_config['price']
            if balance < price:
                return {'error': 'Not enough money'}, 400
            
            # Покупаем
            await db.execute('''
                UPDATE players SET balance = balance - ? WHERE user_id = ?
            ''', (price, user_id))
            
            await db.execute('''
                INSERT INTO player_items (user_id, item_type, item_id, item_name, purchase_price) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, item_type, item_id, item_config['name'], price))
            
            await db.commit()
            
            return {'success': True, 'balance': balance - price}
    
    result = run_async(buy_item())
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)

@app.route('/api/marketplace/list', methods=['GET'])
def api_marketplace_list():
    """API: список предметов на продажу"""
    async def get_marketplace():
        async with aiosqlite.connect(DATABASE) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT m.*, pi.item_name, pi.item_type, p.username, p.first_name
                FROM marketplace m
                JOIN player_items pi ON m.item_id = pi.id
                JOIN players p ON m.seller_id = p.user_id
                WHERE m.sold = 0
                ORDER BY m.created_at DESC
                LIMIT 50
            ''') as cursor:
                items = [dict(row) for row in await cursor.fetchall()]
            return items
    
    items = run_async(get_marketplace())
    return jsonify(items)

@app.route('/api/marketplace/sell', methods=['POST'])
def api_marketplace_sell():
    """API: выставить предмет на продажу"""
    data = request.json
    user_id = data.get('user_id')
    item_db_id = data.get('item_id')
    price = data.get('price')
    
    async def sell_item():
        async with aiosqlite.connect(DATABASE) as db:
            # Проверяем предмет
            async with db.execute('''
                SELECT * FROM player_items WHERE id = ? AND user_id = ?
            ''', (item_db_id, user_id)) as cursor:
                item = await cursor.fetchone()
            
            if not item:
                return {'error': 'Item not found'}, 404
            
            # Проверяем, не продается ли уже
            async with db.execute('''
                SELECT * FROM marketplace WHERE item_id = ? AND sold = 0
            ''', (item_db_id,)) as cursor:
                existing = await cursor.fetchone()
            
            if existing:
                return {'error': 'Already on sale'}, 400
            
            # Выставляем
            await db.execute('''
                INSERT INTO marketplace (seller_id, item_id, price) 
                VALUES (?, ?, ?)
            ''', (user_id, item_db_id, price))
            
            await db.commit()
            
            return {'success': True}
    
    result = run_async(sell_item())
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)

@app.route('/api/marketplace/buy', methods=['POST'])
def api_marketplace_buy():
    """API: купить предмет с маркетплейса"""
    data = request.json
    user_id = data.get('user_id')
    marketplace_id = data.get('marketplace_id')
    
    async def buy_from_marketplace():
        async with aiosqlite.connect(DATABASE) as db:
            # Получаем предложение
            async with db.execute('''
                SELECT * FROM marketplace WHERE id = ? AND sold = 0
            ''', (marketplace_id,)) as cursor:
                offer = await cursor.fetchone()
            
            if not offer:
                return {'error': 'Offer not found'}, 404
            
            seller_id = offer[1]
            item_id = offer[2]
            price = offer[3]
            
            # Нельзя купить у себя
            if seller_id == user_id:
                return {'error': 'Cannot buy your own item'}, 400
            
            # Проверяем баланс
            async with db.execute('SELECT balance FROM players WHERE user_id = ?', (user_id,)) as cursor:
                row = await cursor.fetchone()
                if not row or row[0] < price:
                    return {'error': 'Not enough money'}, 400
            
            # Покупаем
            await db.execute('UPDATE players SET balance = balance - ? WHERE user_id = ?', (price, user_id))
            await db.execute('UPDATE players SET balance = balance + ? WHERE user_id = ?', (price * 0.95, seller_id))  # 5% комиссия
            await db.execute('UPDATE player_items SET user_id = ? WHERE id = ?', (user_id, item_id))
            await db.execute('UPDATE marketplace SET sold = 1 WHERE id = ?', (marketplace_id,))
            
            await db.commit()
            
            return {'success': True}
    
    result = run_async(buy_from_marketplace())
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)

@app.route('/api/box/open', methods=['POST'])
def api_box_open():
    """API: открыть бокс"""
    data = request.json
    user_id = data.get('user_id')
    box_type = data.get('box_type')
    
    async def open_box():
        async with aiosqlite.connect(DATABASE) as db:
            # Проверяем бокс
            box_config = BOXES.get(box_type)
            if not box_config:
                return {'error': 'Invalid box type'}, 400
            
            price = box_config['price']
            
            # Проверяем баланс
            async with db.execute('SELECT balance FROM players WHERE user_id = ?', (user_id,)) as cursor:
                row = await cursor.fetchone()
                if not row or row[0] < price:
                    return {'error': 'Not enough money'}, 400
            
            # Генерируем награду
            rewards = box_config['rewards']
            min_reward, max_reward = random.choice(rewards)
            reward = random.randint(min_reward, max_reward)
            
            # Обновляем баланс
            await db.execute('''
                UPDATE players 
                SET balance = balance - ? + ? 
                WHERE user_id = ?
            ''', (price, reward, user_id))
            
            # Записываем открытие
            await db.execute('''
                INSERT INTO box_openings (user_id, box_type, reward, reward_value) 
                VALUES (?, ?, 'coins', ?)
            ''', (user_id, box_type, reward))
            
            await db.commit()
            
            return {'success': True, 'reward': reward, 'reward_type': 'coins'}
    
    result = run_async(open_box())
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)

@app.route('/api/config')
def api_config():
    """API: конфигурация игры"""
    return jsonify({
        'businesses': BUSINESSES,
        'items': ITEMS,
        'boxes': BOXES
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
