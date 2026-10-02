# ============================================
# ПЛАНИРОВЩИК
# ============================================

import schedule
import time
import threading
from datetime import datetime, timedelta
from database import db
from main import bot
from config import *

def job_vip_pins():
    """Управление VIP пинами"""
    try:
        active_pins = db.get_active_pins()
        
        for pin in active_pins:
            if datetime.fromisoformat(pin['expires_at']) < datetime.now():
                try:
                    bot.unpin_chat_message(CHANNEL_ID, pin['post_id'])
                except:
                    pass
                
                db.deactivate_pin(pin['pin_id'])
    except Exception as e:
        print(f"Ошибка: {e}")

def start_scheduler():
    """Запустить планировщик"""
    schedule.every(1).minute.do(job_vip_pins)
    
    def scheduler_loop():
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()
    print("⏱️ Планировщик запущен!")
