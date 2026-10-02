# ============================================
# КОНФИГУРАЦИЯ SPANIX MARKET BOT
# ============================================

import os
from datetime import datetime

# ========== ОСНОВНОЕ ==========
BOT_TOKEN = "7314564567:AAExampleToken123456789"  # ЗАМЕНИ НА СВОЙ!
ADMIN_ID = 922647390
CHANNEL_ID = -1004350110025
CHANNEL_USERNAME = "@MarketSpanix"

# ========== КОШЕЛЬКИ ==========
TON_WALLET = "UQDvMrYLKRnCgYoH1BnD_oFVZCtkEqBXNkKPIv9ddaYlRpaI"
USDT_WALLET = "0x1234567890abcdef"

# ========== CRYPTO BOT ==========
CRYPTO_BOT_TOKEN = "641245:AAwKptjLTm3ragXEPvLOtSPB8LNeqPCKxfW"
CRYPTO_BOT_API = "https://pay.crypt.bot/api/"

# ========== ЦЕНЫ ==========
PRICES = {
    "regular": {"ton": 0.26, "usdt": 0.44},
    "vip": {"ton": 0.9, "usdt": 1.35},
    "turbo": {"ton": 1.5, "usdt": 2.2},
    "advertising": {"ton": 2.0, "usdt": 2.9},
    "vip_advertising": {"ton": 3.0, "usdt": 4.5}
}

# ========== ЛИМИТЫ ==========
MAX_VIP_PINS = 7
TURBO_REPEAT_HOURS = 24
VIP_PIN_HOURS = 24
MAX_PHOTOS = 2
MAX_VIDEOS = 2

# ========== БАЗА ДАННЫХ ==========
DATABASE_PATH = "spanix_market.db"

# ========== ГАРАНТОР ==========
GUARANTOR_LINK = "@vhcod"
BOT_LINK = "@MarketSpanix_bot"

# ========== ДРУГОЕ ==========
SUPPORT_CHAT_ID = -1001234567890
DEBUG = True

# Словари для хранения состояния пользователей
user_states = {}
user_data = {}
