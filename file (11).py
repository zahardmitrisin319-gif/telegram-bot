# ============================================
# БАЗА ДАННЫХ (SQLite)
# ============================================

import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance_ton REAL DEFAULT 0,
            balance_usdt REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_banned INTEGER DEFAULT 0
        )
        ''')

        # ТАБЛИЦА ПОСТОВ
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            post_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            contact TEXT NOT NULL,
            photos TEXT,
            videos TEXT,
            status TEXT DEFAULT 'pending',
            channel_message_id INTEGER,
            price_ton REAL,
            price_usdt REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            published_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')

        # ТАБЛИЦА ПЛАТЕЖЕЙ
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            crypto_bot_invoice_id INTEGER,
            ton_tx_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')

        # ТАБЛИЦА TURBO ПОСТОВ
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS turbo_posts (
            turbo_id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            last_repost_at TIMESTAMP,
            repost_count INTEGER DEFAULT 0,
            expires_at TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(post_id)
        )
        ''')

        # ТАБЛИЦА VIP ПИНОВ
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vip_pins (
            pin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            pinned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (post_id) REFERENCES posts(post_id)
        )
        ''')

        conn.commit()
        conn.close()

    # ========== ПОЛЬЗОВАТЕЛИ ==========

    def add_user(self, user_id, username, first_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO users (user_id, username, first_name) 
            VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    def get_balance(self, user_id, currency="ton"):
        user = self.get_user(user_id)
        if not user:
            return 0
        if currency.lower() == "ton":
            return user['balance_ton']
        elif currency.lower() == "usdt":
            return user['balance_usdt']
        return 0

    def add_balance(self, user_id, amount, currency="ton"):
        conn = self.get_connection()
        cursor = conn.cursor()
        if currency.lower() == "ton":
            cursor.execute('UPDATE users SET balance_ton = balance_ton + ? WHERE user_id = ?',
                         (amount, user_id))
        else:
            cursor.execute('UPDATE users SET balance_usdt = balance_usdt + ? WHERE user_id = ?',
                         (amount, user_id))
        conn.commit()
        conn.close()

    def subtract_balance(self, user_id, amount, currency="ton"):
        balance = self.get_balance(user_id, currency)
        if balance >= amount:
            self.add_balance(user_id, -amount, currency)
            return True
        return False

    def get_all_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE is_banned = 0')
        users = cursor.fetchall()
        conn.close()
        return [dict(u) for u in users]

    # ========== ПОСТЫ ==========

    def create_post(self, user_id, post_type, title, description, contact, photos, videos, price_ton, price_usdt):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO posts (user_id, post_type, title, description, contact, photos, videos, price_ton, price_usdt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, post_type, title, description, contact, photos, videos, price_ton, price_usdt))
        conn.commit()
        post_id = cursor.lastrowid
        conn.close()
        return post_id

    def get_post(self, post_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM posts WHERE post_id = ?', (post_id,))
        post = cursor.fetchone()
        conn.close()
        return dict(post) if post else None

    def get_pending_posts(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM posts WHERE status = ? ORDER BY created_at DESC', ('pending',))
        posts = cursor.fetchall()
        conn.close()
        return [dict(p) for p in posts]

    def get_user_posts(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        posts = cursor.fetchall()
        conn.close()
        return [dict(p) for p in posts]

    def approve_post(self, post_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE posts 
        SET status = ?, approved_at = CURRENT_TIMESTAMP 
        WHERE post_id = ?
        ''', ('approved', post_id))
        conn.commit()
        conn.close()

    def reject_post(self, post_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE posts 
        SET status = ? 
        WHERE post_id = ?
        ''', ('rejected', post_id))
        conn.commit()
        conn.close()

    def publish_post(self, post_id, channel_message_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE posts 
        SET status = ?, channel_message_id = ?, published_at = CURRENT_TIMESTAMP 
        WHERE post_id = ?
        ''', ('published', channel_message_id, post_id))
        conn.commit()
        conn.close()

    # ========== ПЛАТЕЖИ ==========

    def create_payment(self, user_id, amount, currency, payment_method):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO payments (user_id, amount, currency, payment_method)
        VALUES (?, ?, ?, ?)
        ''', (user_id, amount, currency, payment_method))
        conn.commit()
        payment_id = cursor.lastrowid
        conn.close()
        return payment_id

    def complete_payment(self, payment_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE payments 
        SET status = ?, completed_at = CURRENT_TIMESTAMP 
        WHERE payment_id = ?
        ''', ('completed', payment_id))
        conn.commit()
        conn.close()

    def get_payment(self, payment_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM payments WHERE payment_id = ?', (payment_id,))
        payment = cursor.fetchone()
        conn.close()
        return dict(payment) if payment else None

    # ========== TURBO ==========

    def create_turbo(self, post_id, expires_at):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO turbo_posts (post_id, expires_at)
        VALUES (?, ?)
        ''', (post_id, expires_at))
        conn.commit()
        conn.close()

    def get_turbo_by_post(self, post_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM turbo_posts WHERE post_id = ?', (post_id,))
        turbo = cursor.fetchone()
        conn.close()
        return dict(turbo) if turbo else None

    def update_turbo_repost(self, turbo_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE turbo_posts 
        SET last_repost_at = CURRENT_TIMESTAMP, repost_count = repost_count + 1 
        WHERE turbo_id = ?
        ''', (turbo_id,))
        conn.commit()
        conn.close()

    # ========== VIP ПИНЫ ==========

    def create_vip_pin(self, post_id, expires_at):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO vip_pins (post_id, expires_at)
        VALUES (?, ?)
        ''', (post_id, expires_at))
        conn.commit()
        conn.close()

    def get_active_pins(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM vip_pins 
        WHERE is_active = 1 AND expires_at > CURRENT_TIMESTAMP
        ''')
        pins = cursor.fetchall()
        conn.close()
        return [dict(p) for p in pins]

    def deactivate_pin(self, pin_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE vip_pins SET is_active = 0 WHERE pin_id = ?', (pin_id,))
        conn.commit()
        conn.close()

    # ========== СТАТИСТИКА ==========

    def get_statistics(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM posts WHERE status = ?', ('published',))
        total_posts = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM posts WHERE status = ?', ('approved',))
        approved = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM posts WHERE status = ?', ('rejected',))
        rejected = cursor.fetchone()['count']

        cursor.execute('SELECT SUM(price_ton) as sum FROM posts WHERE status = ?', ('published',))
        total_ton = cursor.fetchone()['sum'] or 0

        cursor.execute('SELECT SUM(price_usdt) as sum FROM posts WHERE status = ?', ('published',))
        total_usdt = cursor.fetchone()['sum'] or 0

        cursor.execute('SELECT COUNT(*) as count FROM users')
        total_users = cursor.fetchone()['count']

        conn.close()

        return {
            'total_posts': total_posts,
            'approved': approved,
            'rejected': rejected,
            'total_users': total_users,
            'total_ton': total_ton,
            'total_usdt': total_usdt
        }

# Создаём глобальный объект БД
db = Database()
