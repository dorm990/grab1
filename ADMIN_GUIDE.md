# Админ функции

## Как стать админом

1. Узнайте свой Telegram ID:
   - Напишите боту @userinfobot
   - Скопируйте ваш ID

2. Добавьте ID в `bot.py`:
```python
ADMIN_IDS = [123456789, 987654321]  # Замените на свои ID
```

## Доступные команды

### /admin
Открывает админ-панель с кнопками:
- 👥 Статистика
- 🎁 Выдать бонус
- 🚫 Забанить
- ✅ Разбанить

### Статистика
Показывает:
- Общее количество игроков
- Активных сегодня
- Общая сумма заработанного

### Выдать бонус
Для реализации добавьте в bot.py:

```python
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_bonus = State()

@dp.callback_query(F.data == "admin_bonus")
async def admin_bonus_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.answer("Введите ID игрока:")
    await state.set_state(AdminStates.waiting_for_user_id)
    await callback.answer()

@dp.message(AdminStates.waiting_for_user_id)
async def admin_bonus_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(target_user_id=user_id)
        await message.answer("Введите сумму бонуса:")
        await state.set_state(AdminStates.waiting_for_bonus)
    except:
        await message.answer("❌ Неверный ID")
        await state.clear()

@dp.message(AdminStates.waiting_for_bonus)
async def admin_bonus_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        data = await state.get_data()
        user_id = data['target_user_id']
        
        async with aiosqlite.connect(DATABASE) as db:
            await db.execute('''
                UPDATE players SET balance = balance + ? WHERE user_id = ?
            ''', (amount, user_id))
            await db.commit()
        
        await message.answer(f"✅ Бонус {amount} выдан пользователю {user_id}")
        await state.clear()
    except:
        await message.answer("❌ Неверная сумма")
        await state.clear()
```

### Забанить игрока

```python
class AdminStates(StatesGroup):
    # ... предыдущие состояния
    waiting_for_ban_user = State()

@dp.callback_query(F.data == "admin_ban")
async def admin_ban_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.answer("Введите ID игрока для бана:")
    await state.set_state(AdminStates.waiting_for_ban_user)
    await callback.answer()

@dp.message(AdminStates.waiting_for_ban_user)
async def admin_ban_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        
        async with aiosqlite.connect(DATABASE) as db:
            await db.execute('''
                UPDATE players SET is_banned = 1 WHERE user_id = ?
            ''', (user_id,))
            await db.commit()
        
        await message.answer(f"✅ Пользователь {user_id} забанен")
        await state.clear()
    except:
        await message.answer("❌ Ошибка")
        await state.clear()
```

### Разбанить игрока

```python
class AdminStates(StatesGroup):
    # ... предыдущие состояния
    waiting_for_unban_user = State()

@dp.callback_query(F.data == "admin_unban")
async def admin_unban_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.answer("Введите ID игрока для разбана:")
    await state.set_state(AdminStates.waiting_for_unban_user)
    await callback.answer()

@dp.message(AdminStates.waiting_for_unban_user)
async def admin_unban_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        
        async with aiosqlite.connect(DATABASE) as db:
            await db.execute('''
                UPDATE players SET is_banned = 0 WHERE user_id = ?
            ''', (user_id,))
            await db.commit()
        
        await message.answer(f"✅ Пользователь {user_id} разбанен")
        await state.clear()
    except:
        await message.answer("❌ Ошибка")
        await state.clear()
```

## Дополнительные админ функции

### Массовая рассылка

```python
@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.answer("Введите текст для рассылки:")
    await state.set_state(AdminStates.waiting_for_broadcast)
    await callback.answer()

@dp.message(AdminStates.waiting_for_broadcast)
async def admin_broadcast_send(message: types.Message, state: FSMContext):
    text = message.text
    
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('SELECT user_id FROM players WHERE is_banned = 0') as cursor:
            users = await cursor.fetchall()
    
    sent = 0
    failed = 0
    
    for (user_id,) in users:
        try:
            await bot.send_message(user_id, text)
            sent += 1
            await asyncio.sleep(0.05)  # Избегаем флуда
        except:
            failed += 1
    
    await message.answer(f"✅ Рассылка завершена\nОтправлено: {sent}\nОшибок: {failed}")
    await state.clear()
```

### Статистика по бизнесам

```python
@dp.callback_query(F.data == "admin_business_stats")
async def admin_business_stats(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    async with aiosqlite.connect(DATABASE) as db:
        # Топ бизнесов по прибыли
        async with db.execute('''
            SELECT business_id, COUNT(*), SUM(total_earned)
            FROM player_businesses
            GROUP BY business_id
            ORDER BY SUM(total_earned) DESC
        ''') as cursor:
            businesses = await cursor.fetchall()
    
    text = "📊 Статистика бизнесов:\n\n"
    for business_id, count, total_earned in businesses:
        business_name = BUSINESSES.get(business_id, {}).get('name', f'Бизнес {business_id}')
        text += f"{business_name}\n"
        text += f"  Владельцев: {count}\n"
        text += f"  Всего заработано: {total_earned or 0:.2f}\n\n"
    
    await callback.message.answer(text)
    await callback.answer()
```

### Управление экономикой

```python
@dp.callback_query(F.data == "admin_economy")
async def admin_economy(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    async with aiosqlite.connect(DATABASE) as db:
        # Общая валюта в игре
        async with db.execute('SELECT SUM(balance) FROM players') as cursor:
            total_balance = (await cursor.fetchone())[0] or 0
        
        # Средний баланс
        async with db.execute('SELECT AVG(balance) FROM players') as cursor:
            avg_balance = (await cursor.fetchone())[0] or 0
        
        # Игроков с балансом > 10000
        async with db.execute('SELECT COUNT(*) FROM players WHERE balance > 10000') as cursor:
            rich_players = (await cursor.fetchone())[0]
    
    text = f"""
💰 Экономика игры:

💵 Всего валюты: {total_balance:.2f}
📊 Средний баланс: {avg_balance:.2f}
💎 Богатых игроков (>10k): {rich_players}
    """
    
    await callback.message.answer(text)
    await callback.answer()
```

## Мониторинг

### Логирование действий

```python
async def log_admin_action(admin_id: int, action: str, target_id: int = None, details: str = None):
    """Логирование админ-действий"""
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
            INSERT INTO admin_logs (admin_id, action, target_id, details)
            VALUES (?, ?, ?, ?)
        ''', (admin_id, action, target_id, details))
        await db.commit()

# Создайте таблицу в init_db():
await db.execute('''
    CREATE TABLE IF NOT EXISTS admin_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT,
        target_id INTEGER,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
```

### Просмотр логов

```python
@dp.callback_query(F.data == "admin_logs")
async def admin_logs(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('''
            SELECT admin_id, action, target_id, details, created_at
            FROM admin_logs
            ORDER BY created_at DESC
            LIMIT 20
        ''') as cursor:
            logs = await cursor.fetchall()
    
    text = "📋 Последние действия:\n\n"
    for admin_id, action, target_id, details, created_at in logs:
        text += f"👤 {admin_id} | {action}\n"
        if target_id:
            text += f"  Target: {target_id}\n"
        if details:
            text += f"  {details}\n"
        text += f"  {created_at}\n\n"
    
    await callback.message.answer(text)
    await callback.answer()
```
