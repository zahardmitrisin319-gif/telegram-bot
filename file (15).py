# ============================================
# TONKEEPER - TON ПЛАТЕЖИ
# ============================================

from config import TON_WALLET
from database import db

# Здесь будет интеграция с TON blockchain
# Для теста используем ручное пополнение

def process_ton_payment(user_id, amount):
    """Пополнить баланс TON"""
    db.add_balance(user_id, amount, "ton")
    return True
