# ============================================
# ОСНОВНОЙ БОТ
# ============================================

import telebot
from telebot import types
from config import *
from database import db
from datetime import datetime, timedelta
import json
import os

# Инициализируем бот
bot = telebot.TeleBot(BOT_TOKEN)

# ========== СТАРТОВОЕ МЕНЮ ==========

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    first_name = message.from_user.first_name or "User"
    
    user = db.get_user(user_id)
    if not user:
        db.add_user(user_id, username, first_name)
    
    show_main_menu(message.chat.id, first_name)

def show_main_menu(chat_id, first_name):
    msg = f"👋 Привет, {first_name}!\n\n"
    msg += "🎯 **Spanix Market** - маркетплейс объявлений\n\n"
    msg += "Выбери действие:"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📝 Создать объявление", callback_data="create_post"))
    markup.add(types.InlineKeyboardButton("💰 Пополнить баланс", callback_data="top_up"))
    markup.add(types.InlineKeyboardButton("📊 Мои объявления", callback_data="my_posts"))
    markup.add(types.InlineKeyboardButton("💬 Поддержка", callback_data="support"))
    markup.add(types.InlineKeyboardButton("📈 Статистика", callback_data="stats"))
    
    bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="Markdown")

# ========== СОЗДАНИЕ ОБЪЯВЛЕНИЯ ==========

@bot.callback_query_handler(func=lambda call: call.data == "create_post")
def create_post_type(call):
    msg = "📋 **Выбери тип объявления:**\n\n"
    msg += "💜 **Regular** - 0.26 TON / 0.44 USDT\n"
    msg += "👑 **VIP** - 0.9 TON / 1.35 USDT (24ч пин)\n"
    msg += "⚡ **Turbo** - 1.5 TON / 2.2 USDT (переповтор)\n"
    msg += "📢 **Advertising** - 2 TON / 2.9 USDT\n"
    msg += "🌟 **VIP Advertising** - 3 TON / 4.5 USDT\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💜 Regular", callback_data="type_regular"),
        types.InlineKeyboardButton("👑 VIP", callback_data="type_vip")
    )
    markup.add(
        types.InlineKeyboardButton("⚡ Turbo", callback_data="type_turbo"),
        types.InlineKeyboardButton("📢 Advertising", callback_data="type_advertising")
    )
    markup.add(types.InlineKeyboardButton("🌟 VIP Adv", callback_data="type_vip_advertising"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, 
                         reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("type_"))
def check_balance_for_post(call):
    user_id = call.from_user.id
    post_type = call.data.replace("type_", "")
    
    user = db.get_user(user_id)
    ton_price = PRICES[post_type]["ton"]
    usdt_price = PRICES[post_type]["usdt"]
    
    ton_balance = user['balance_ton']
    usdt_balance = user['balance_usdt']
    
    msg = f"💰 **Проверка баланса**\n\n"
    msg += f"Стоимость: {ton_price} TON или {usdt_price} USDT\n\n"
    msg += f"🪙 TON баланс: {ton_balance}\n"
    msg += f"💵 USDT баланс: {usdt_balance}\n\n"
    
    can_pay_ton = ton_balance >= ton_price
    can_pay_usdt = usdt_balance >= usdt_price
    
    if not can_pay_ton and not can_pay_usdt:
        msg += "❌ **Недостаточно средств!**\n\n"
        msg += "Пополните баланс:"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💰 Пополнить", callback_data="top_up"))
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                             reply_markup=markup, parse_mode="Markdown")
    else:
        msg += "✅ **Баланс достаточен!**\n\n"
        msg += "Выбери валюту:"
        
        markup = types.InlineKeyboardMarkup()
        if can_pay_ton:
            markup.add(types.InlineKeyboardButton(f"🪙 TON ({ton_price})", 
                                                 callback_data=f"pay_ton_{post_type}"))
        if can_pay_usdt:
            markup.add(types.InlineKeyboardButton(f"💵 USDT ({usdt_price})", 
                                                 callback_data=f"pay_usdt_{post_type}"))
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                             reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def start_post_creation(call):
    user_id = call.from_user.id
    data = call.data.split("_")
    currency = data[1]
    post_type = data[2]
    
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id] = {
        'post_type': post_type,
        'currency': currency,
        'step': 'title'
    }
    
    msg = "📝 **Введи заголовок** объявления:"
    sent = bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                         parse_mode="Markdown")
    
    bot.register_next_step_handler(call.message, handle_post_title, user_id)

def handle_post_title(message, user_id):
    if user_id not in user_data:
        bot.send_message(message.chat.id, "❌ Ошибка. Начни заново /start")
        return
    
    user_data[user_id]['title'] = message.text
    
    msg = "📄 **Введи описание** объявления:"
    m = bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    bot.register_next_step_handler(m, handle_post_description, user_id)

def handle_post_description(message, user_id):
    if user_id not in user_data:
        bot.send_message(message.chat.id, "❌ Ошибка. Начни заново /start")
        return
    
    user_data[user_id]['description'] = message.text
    
    msg = "👤 **Введи контакт** (username или номер):"
    m = bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    bot.register_next_step_handler(m, handle_post_contact, user_id)

def handle_post_contact(message, user_id):
    if user_id not in user_data:
        bot.send_message(message.chat.id, "❌ Ошибка. Начни заново /start")
        return
    
    user_data[user_id]['contact'] = message.text
    user_data[user_id]['photos'] = []
    user_data[user_id]['videos'] = []
    
    msg = "🖼️ **Отправь фото** (макс 2).\n\n"
    msg += "Или напиши **'Пропустить'** чтобы продолжить:"
    m = bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    bot.register_next_step_handler(m, handle_post_photos, user_id)

def handle_post_photos(message, user_id):
    if user_id not in user_data:
        bot.send_message(message.chat.id, "❌ Ошибка. Начни заново /start")
        return
    
    if message.text and message.text.lower() == "пропустить":
        handle_post_videos_prompt(message, user_id)
    elif message.photo:
        photos = user_data[user_id]['photos']
        if len(photos) < MAX_PHOTOS:
            photos.append(message.photo[-1].file_id)
            bot.send_message(message.chat.id, f"✅ Фото добавлено ({len(photos)}/{MAX_PHOTOS})")
            m = bot.send_message(message.chat.id, "Отправь ещё или напиши 'Продолжить':")
            bot.register_next_step_handler(m, handle_post_photos, user_id)
        else:
            bot.send_message(message.chat.id, f"❌ Максимум {MAX_PHOTOS} фото")
            handle_post_videos_prompt(message, user_id)
    elif message.text and message.text.lower() == "продолжить":
        handle_post_videos_prompt(message, user_id)
    else:
        m = bot.send_message(message.chat.id, "❌ Отправь фото или напиши 'Пропустить':")
        bot.register_next_step_handler(m, handle_post_photos, user_id)

def handle_post_videos_prompt(message, user_id):
    msg = "🎥 **Отправь видео** (макс 2).\n\n"
    msg += "Или напиши **'Пропустить'** чтобы завершить:"
    m = bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    bot.register_next_step_handler(m, handle_post_videos, user_id)

def handle_post_videos(message, user_id):
    if user_id not in user_data:
        bot.send_message(message.chat.id, "❌ Ошибка. Начни заново /start")
        return
    
    if message.text and message.text.lower() == "пропустить":
        finalize_post(message, user_id)
    elif message.video:
        videos = user_data[user_id]['videos']
        if len(videos) < MAX_VIDEOS:
            videos.append(message.video.file_id)
            bot.send_message(message.chat.id, f"✅ Видео добавлено ({len(videos)}/{MAX_VIDEOS})")
            m = bot.send_message(message.chat.id, "Отправь ещё или напиши 'Продолжить':")
            bot.register_next_step_handler(m, handle_post_videos, user_id)
        else:
            bot.send_message(message.chat.id, f"❌ Максимум {MAX_VIDEOS} видео")
            finalize_post(message, user_id)
    elif message.text and message.text.lower() == "продолжить":
        finalize_post(message, user_id)
    else:
        m = bot.send_message(message.chat.id, "❌ Отправь видео или напиши 'Пропустить':")
        bot.register_next_step_handler(m, handle_post_videos, user_id)

def finalize_post(message, user_id):
    if user_id not in user_data:
        bot.send_message(message.chat.id, "❌ Ошибка. Начни заново /start")
        return
    
    data = user_data[user_id]
    
    post_type = data['post_type']
    title = data['title']
    description = data['description']
    contact = data['contact']
    photos = json.dumps(data.get('photos', []))
    videos = json.dumps(data.get('videos', []))
    
    currency = data['currency']
    price_ton = PRICES[post_type]["ton"] if currency == "ton" else 0
    price_usdt = PRICES[post_type]["usdt"] if currency == "usdt" else 0
    
    post_id = db.create_post(user_id, post_type, title, description, contact, 
                            photos, videos, price_ton, price_usdt)
    
    if currency == "ton":
        db.subtract_balance(user_id, price_ton, "ton")
    else:
        db.subtract_balance(user_id, price_usdt, "usdt")
    
    send_to_moderation(post_id, user_id)
    
    msg = f"✅ **Объявление #{post_id} создано!**\n\n"
    msg += "📤 Отправляется на модерацию...\n\n"
    msg += "⏱️ Обычно рассмотрим за 10-15 минут"
    
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    
    if user_id in user_data:
        del user_data[user_id]
    
    show_main_menu(message.chat.id, message.from_user.first_name)

def send_to_moderation(post_id, user_id):
    post = db.get_post(post_id)
    user = db.get_user(user_id)
    
    msg = f"🔍 **НОВОЕ ОБЪЯВЛЕНИЕ НА МОДЕРАЦИЮ**\n\n"
    msg += f"ID: #{post_id}\n"
    msg += f"Тип: {post['post_type'].upper()}\n"
    msg += f"Пользователь: @{user['username']} (ID: {user_id})\n\n"
    msg += f"**Заголовок:** {post['title']}\n\n"
    msg += f"**Описание:** {post['description']}\n\n"
    msg += f"**Контакт:** {post['contact']}\n\n"
    msg += f"**Стоимость:** {post['price_ton']} TON / {post['price_usdt']} USDT"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{post_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{post_id}")
    )
    
    bot.send_message(ADMIN_ID, msg, reply_markup=markup, parse_mode="Markdown")

# ========== ПОПОЛНЕНИЕ БАЛАНСА ==========

@bot.callback_query_handler(func=lambda call: call.data == "top_up")
def top_up_menu(call):
    user_id = call.from_user.id
    user = db.get_user(user_id)
    
    msg = f"💰 **Пополнение баланса**\n\n"
    msg += f"🪙 TON баланс: {user['balance_ton']}\n"
    msg += f"💵 USDT баланс: {user['balance_usdt']}\n\n"
    msg += "Выбери валюту:"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🪙 TON", callback_data="topup_ton"),
        types.InlineKeyboardButton("💵 USDT", callback_data="topup_usdt")
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                         reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "topup_ton")
def topup_ton(call):
    user_id = call.from_user.id
    
    msg = f"🪙 **Пополнение TON**\n\n"
    msg += f"💳 **Кошелёк:** `{TON_WALLET}`\n\n"
    msg += "Введи сумму TON для пополнения:"
    
    m = bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                             parse_mode="Markdown")
    
    bot.register_next_step_handler(call.message, process_ton_amount, user_id)

def process_ton_amount(message, user_id):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
        
        msg = f"✅ **Отправь {amount} TON на адрес:**\n\n"
        msg += f"`{TON_WALLET}`\n\n"
        msg += "После перевода баланс пополнится автоматически (обычно 1-5 минут)\n\n"
        msg += "⏳ Ожидаю подтверждение..."
        
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        
        payment_id = db.create_payment(user_id, amount, "TON", "tonkeeper")
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введи корректную сумму")
        m = bot.send_message(message.chat.id, "Введи сумму TON:")
        bot.register_next_step_handler(m, process_ton_amount, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "topup_usdt")
def topup_usdt(call):
    user_id = call.from_user.id
    
    msg = "💵 **Пополнение USDT**\n\n"
    msg += "Введи сумму USDT для пополнения:"
    
    m = bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                             parse_mode="Markdown")
    
    bot.register_next_step_handler(call.message, process_usdt_amount, user_id)

def process_usdt_amount(message, user_id):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
        
        msg = f"✅ **Пополнение на {amount} USDT**\n\n"
        msg += "Счёт создан. Используй одну из платёжных систем:\n\n"
        msg += "1. 💳 Крипто Бот\n"
        msg += "2. 🪙 TON\n"
        msg += "3. 💵 USDT (TRC20)\n\n"
        msg += "Свяжись с поддержкой для деталей"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 Поддержка", callback_data="support"))
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="top_up"))
        
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")
        
        db.create_payment(user_id, amount, "USDT", "manual")
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введи корректную сумму")
        m = bot.send_message(message.chat.id, "Введи сумму USDT:")
        bot.register_next_step_handler(m, process_usdt_amount, user_id)

# ========== МОИ ОБЪЯВЛЕНИЯ ==========

@bot.callback_query_handler(func=lambda call: call.data == "my_posts")
def my_posts(call):
    user_id = call.from_user.id
    posts = db.get_user_posts(user_id)
    
    if not posts:
        msg = "📭 У тебя нет объявлений"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Создать", callback_data="create_post"))
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                             reply_markup=markup)
    else:
        msg = "📊 **Твои объявления:**\n\n"
        
        markup = types.InlineKeyboardMarkup()
        
        for post in posts:
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌',
                'published': '📤'
            }
            
            emoji = status_emoji.get(post['status'], '❓')
            msg += f"{emoji} #{post['post_id']} - {post['title'][:30]}\n"
            msg += f"   Статус: {post['status']}\n\n"
            
            markup.add(types.InlineKeyboardButton(
                f"#{post['post_id']}", 
                callback_data=f"view_post_{post['post_id']}"
            ))
        
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                             reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_post_"))
def view_post(call):
    post_id = int(call.data.replace("view_post_", ""))
    post = db.get_post(post_id)
    
    msg = f"📋 **Объявление #{post_id}**\n\n"
    msg += f"Тип: {post['post_type'].upper()}\n"
    msg += f"Статус: {post['status']}\n\n"
    msg += f"**{post['title']}**\n\n"
    msg += f"{post['description']}\n\n"
    msg += f"👤 Контакт: {post['contact']}\n"
    msg += f"💰 Стоимость: {post['price_ton']} TON / {post['price_usdt']} USDT"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="my_posts"))
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                         reply_markup=markup, parse_mode="Markdown")

# ========== ПОДДЕРЖКА ==========

@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    msg = "💬 **Техническая поддержка**\n\n"
    msg += "Напиши своё сообщение, оно будет отправлено администратору:"
    
    m = bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                             parse_mode="Markdown")
    
    bot.register_next_step_handler(call.message, send_support_message)

def send_support_message(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    msg = f"📬 **СООБЩЕНИЕ ОТ ПОЛЬЗОВАТЕЛЯ**\n\n"
    msg += f"@{username} (ID: {user_id})\n\n"
    msg += f"{message.text}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Ответить", callback_data=f"reply_{user_id}"))
    
    bot.send_message(ADMIN_ID, msg, reply_markup=markup, parse_mode="Markdown")
    
    bot.send_message(message.chat.id, "✅ Сообщение отправлено администратору")
    show_main_menu(message.chat.id, message.from_user.first_name)

# ========== СТАТИСТИКА ==========

@bot.callback_query_handler(func=lambda call: call.data == "stats")
def stats(call):
    stats_data = db.get_statistics()
    
    msg = f"📈 **Статистика Spanix Market**\n\n"
    msg += f"👥 Пользователей: {stats_data['total_users']}\n"
    msg += f"📝 Постов опубликовано: {stats_data['total_posts']}\n"
    msg += f"✅ Одобрено: {stats_data['approved']}\n"
    msg += f"❌ Отклонено: {stats_data['rejected']}\n\n"
    msg += f"💰 **Доход:**\n"
    msg += f"🪙 TON: {stats_data['total_ton']}\n"
    msg += f"💵 USDT: {stats_data['total_usdt']}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                         reply_markup=markup, parse_mode="Markdown")

# ========== ВСПОМОГАТЕЛЬНЫЕ ==========

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    show_main_menu(call.message.chat.id, call.from_user.first_name)

# ========== АДМИН КОМАНДА ==========

@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет доступа")
        return
    
    msg = "🎛️ **АДМИН ПАНЕЛЬ**\n\n"
    msg += "Выбери действие:"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📝 Модерация", callback_data="admin_moderation"))
    markup.add(types.InlineKeyboardButton("💰 Балансы", callback_data="admin_balances"))
    markup.add(types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"))
    markup.add(types.InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings"))
    
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_moderation")
def admin_moderation(call):
    if call.from_user.id != ADMIN_ID:
        bot.send_message(call.message.chat.id, "❌ У вас нет доступа")
        return
    
    pending_posts = db.get_pending_posts()
    
    if not pending_posts:
        msg = "✅ Все посты рассмотрены!"
        bot.send_message(call.message.chat.id, msg)
    else:
        for post in pending_posts:
            user = db.get_user(post['user_id'])
            
            msg = f"📋 **Пост #{post['post_id']}**\n\n"
            msg += f"Тип: {post['post_type'].upper()}\n"
            msg += f"Пользователь: @{user['username']}\n\n"
            msg += f"**{post['title']}**\n\n"
            msg += f"{post['description']}\n\n"
            msg += f"👤 Контакт: {post['contact']}"
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{post['post_id']}"),
                types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{post['post_id']}")
            )
            
            bot.send_message(call.message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_post(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    post_id = int(call.data.replace("approve_", ""))
    post = db.get_post(post_id)
    
    db.approve_post(post_id)
    
    if post['price_ton'] > 0:
        db.subtract_balance(post['user_id'], post['price_ton'], "ton")
    else:
        db.subtract_balance(post['user_id'], post['price_usdt'], "usdt")
    
    # Публикуем в канал
    user = db.get_user(post['user_id'])
    
    msg = f"**{post['title']}**\n\n"
    msg += f"{post['description']}\n\n"
    msg += f"👤 Контакт: {post['contact']}\n\n"
    msg += f"---\n"
    msg += f"Гарантор: {GUARANTOR_LINK}\n"
    msg += f"Бот: {BOT_LINK}"
    
    try:
        photos = json.loads(post['photos']) if post['photos'] else []
        videos = json.loads(post['videos']) if post['videos'] else []
        
        if photos:
            result = bot.send_photo(CHANNEL_ID, photos[0], caption=msg, parse_mode="Markdown")
        elif videos:
            result = bot.send_video(CHANNEL_ID, videos[0], caption=msg, parse_mode="Markdown")
        else:
            result = bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
        
        db.publish_post(post_id, result.message_id)
        
        # Уведомляем пользователя
        bot.send_message(post['user_id'], 
            f"✅ **Ваше объявление #{post_id} одобрено и опубликовано!**")
        
        bot.edit_message_text("✅ Пост одобрен и опубликован", 
                             call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_post(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    post_id = int(call.data.replace("reject_", ""))
    post = db.get_post(post_id)
    
    if post['price_ton'] > 0:
        db.add_balance(post['user_id'], post['price_ton'], "ton")
    else:
        db.add_balance(post['user_id'], post['price_usdt'], "usdt")
    
    db.reject_post(post_id)
    
    bot.send_message(post['user_id'],
        f"❌ **Ваше объявление #{post_id} отклонено.**\n\n"
        f"Баланс вернён.")
    
    bot.edit_message_text("❌ Пост отклонён", 
                         call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_balances")
def admin_balances(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    users = db.get_all_users()
    
    msg = "💰 **БАЛАНСЫ ПОЛЬЗОВАТЕЛЕЙ**\n\n"
    
    for user in users[:10]:
        msg += f"@{user['username']} (ID: {user['user_id']})\n"
        msg += f"  TON: {user['balance_ton']}\n"
        msg += f"  USDT: {user['balance_usdt']}\n\n"
    
    msg += f"**Всего:** {len(users)} пользователей"
    
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    stats_data = db.get_statistics()
    
    msg = "📊 **СТАТИСТИКА**\n\n"
    msg += f"👥 Пользователей: {stats_data['total_users']}\n"
    msg += f"📝 Постов: {stats_data['total_posts']}\n"
    msg += f"✅ Одобрено: {stats_data['approved']}\n"
    msg += f"❌ Отклонено: {stats_data['rejected']}\n\n"
    msg += f"💰 **Доход:**\n"
    msg += f"🪙 TON: {stats_data['total_ton']}\n"
    msg += f"💵 USDT: {stats_data['total_usdt']}"
    
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")

# ========== ЗАПУСК ==========

if __name__ == "__main__":
    print("🚀 Spanix Market Bot запущен!")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
