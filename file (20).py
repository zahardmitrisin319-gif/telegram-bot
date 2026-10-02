# ============================================
# ГЛАВНЫЙ ФАЙЛ ЗАПУСКА
# ============================================

import sys
import os

# Добавляем текущую папку в path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("=" * 50)
    print("🚀 SPANIX MARKET BOT")
    print("=" * 50)
    print()
    
    # Импортируем модули
    print("📦 Загружаю модули...")
    from database import db
    from config import BOT_TOKEN, ADMIN_ID
    from scheduler import start_scheduler
    print("✅ Модули загружены")
    print()
    
    # Проверяем BOT_TOKEN
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN":
        print("❌ ОШИБКА: Установи BOT_TOKEN в config.py!")
        print("Получи токен у @BotFather")
        sys.exit(1)
    
    print(f"✅ BOT_TOKEN: {BOT_TOKEN[:20]}...")
    print(f"✅ ADMIN_ID: {ADMIN_ID}")
    print()
    
    # Инициализируем БД
    print("💾 Инициализирую базу данных...")
    print("✅ База данных готова")
    print()
    
    # Запускаем планировщик
    start_scheduler()
    print()
    
    # Импортируем и запускаем бот
    print("🤖 Запускаю бота...")
    from main import bot
    
    print()
    print("=" * 50)
    print("✅ БОТ УСПЕШНО ЗАПУЩЕН!")
    print("=" * 50)
    print()
    print("📝 Команды:")
    print("  /start  - Главное меню")
    print("  /admin  - Админ панель")
    print()
    print("💬 Переходи на: https://t.me/MarketSpanix_bot")
    print()
    
    # Запускаем бота
    bot.infinity_polling(none_stop=True)
    
except ImportError as e:
    print(f"❌ ОШИБКА ИМПОРТА: {e}")
    print()
    print("Установи зависимости:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    sys.exit(1)
