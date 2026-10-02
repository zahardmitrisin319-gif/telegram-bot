# ============================================
# ФУНКЦИИ ПОЛЬЗОВАТЕЛЯ
# ============================================

from main import bot
from database import db
from config import *

def get_user_balance(user_id):
    """Получить баланс"""
    user = db.get_user(user_id)
    if user:
        return {
            'ton': user['balance_ton'],
            'usdt': user['balance_usdt']
        }
    return {'ton': 0, 'usdt': 0}

def get_user_posts_count(user_id):
    """Получить количество постов"""
    posts = db.get_user_posts(user_id)
    return len(posts)
