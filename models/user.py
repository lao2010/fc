from datetime import datetime, timedelta
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from . import db  # 假设存在数据库实例

DB_PATH = 'e:\\fc\\data\\users.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            daily_usage INTEGER DEFAULT 0,
            last_reset_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.Date)

    def __init__(self, username, email, password, is_admin=False):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.is_admin = is_admin
        self.daily_usage = 0
        self.last_reset_date = datetime.now().date().isoformat()
        self.usage_count = 0
        self.last_used = datetime.now().date()
        
    def save(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin, daily_usage, last_reset_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.username, self.email, self.password_hash, self.is_admin, self.daily_usage, self.last_reset_date))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_username(username):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()
        if user_data:
            user = User(user_data[1], user_data[2], '')
            user.id = user_data[0]
            user.password_hash = user_data[3]
            user.is_admin = bool(user_data[4])
            user.daily_usage = user_data[5]
            user.last_reset_date = user_data[6]
            return user
        return None

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def check_usage_limit(self):
        today = datetime.now().date()
        last_reset = datetime.strptime(self.last_reset_date, '%Y-%m-%d').date()
        
        if today > last_reset:
            self.daily_usage = 0
            self.last_reset_date = today.isoformat()
            self.update_usage()
            return True
        return self.daily_usage < 100 or self.is_admin

    def increment_usage(self):
        self.daily_usage += 1
        self.update_usage()

    def update_usage(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET daily_usage = ?, last_reset_date = ? WHERE id = ?
        ''', (self.daily_usage, self.last_reset_date, self.id))
        conn.commit()
        conn.close()

    def update_password(self, new_password):
        self.password_hash = generate_password_hash(new_password)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (self.password_hash, self.id))
        conn.commit()
        conn.close()

    def update_email(self, new_email):
        self.email = new_email
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET email = ? WHERE id = ?', (self.email, self.id))
        conn.commit()
        conn.close()

    def check_usage(self):
        print(f"Checking usage for user: {self.username}")  # 调试日志
        today = datetime.now().date()
        
        if isinstance(self.last_used, str):
            print(f"Original last_used: {self.last_used}")  # 调试日期转换
            try:
                self.last_used = datetime.strptime(self.last_used, '%Y-%m-%d').date()
            except Exception as e:
                print(f"Date conversion error: {e}")
        
        print(f"Today: {today}, Last used: {self.last_used}")  # 调试日期对比
        
        if self.last_used != today:
            print("Resetting daily usage")  # 调试重置逻辑
            self.usage_count = 0
            self.last_used = today
            try:
                db.session.commit()
                print("Reset successful")
            except Exception as e:
                print(f"Commit error: {e}")
        
        return 50 - self.usage_count
        
    def record_usage(self):
        self.usage_count +=1
        self.save()

    
    @classmethod
    def get_by_id(cls, user_id):
        return cls.query.get(user_id)
    
    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    # 在User类中添加重置方法
    @classmethod
    def reset_usage_stats(cls):
        """清空所有用户的使用计数"""
        cls.query.update({'usage_count': 0, 'last_used': datetime.now().date()})
        db.session.commit()