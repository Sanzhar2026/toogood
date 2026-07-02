# update_db.py - СКРИПТ ДЛЯ ДОБАВЛЕНИЯ ПОЛЯ

import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL = "postgresql://postgres:YHceVkBwWMtDTXqSbqQhsGrnIxeWlcwz@thomas.proxy.rlwy.net:27717/railway"

def add_last_surprise_view_column():
    """Добавить поле last_surprise_view в таблицу users"""
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Проверяем, существует ли колонка
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='last_surprise_view'
        """)
        
        if cur.fetchone():
            print("✅ Колонка last_surprise_view уже существует")
        else:
            # Добавляем колонку
            cur.execute("""
                ALTER TABLE users 
                ADD COLUMN last_surprise_view TIMESTAMP DEFAULT NULL
            """)
            conn.commit()
            print("✅ Колонка last_surprise_view добавлена")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_last_surprise_view_column()