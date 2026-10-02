# ============================================
# CRYPTO BOT API
# ============================================

import requests
from config import CRYPTO_BOT_TOKEN, CRYPTO_BOT_API
from database import db

def create_invoice(user_id, amount):
    try:
        url = CRYPTO_BOT_API + "createInvoice"
        
        payload = {
            "asset": "USDT",
            "amount": str(amount),
            "description": f"Spanix Market - {user_id}",
            "payload": f"user_{user_id}",
        }
        
        headers = {
            "Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN,
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if data.get('ok'):
            invoice = data['result']['invoice']
            return {
                'invoice_id': invoice['invoice_id'],
                'pay_url': invoice['pay_url'],
                'amount': amount
            }
        
        return None
    except Exception as e:
        print(f"Ошибка Crypto Bot: {e}")
        return None
