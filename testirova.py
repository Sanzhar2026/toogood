# Запустите этот скрипт один раз для обновления БД
# create_missing_columns.py

from backend.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Добавляем колонки first_name и last_name если их нет
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR(100)"))
        print("✅ Добавлена колонка first_name")
    except Exception as e:
        print(f"Колонка first_name уже существует: {e}")
    
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR(100)"))
        print("✅ Добавлена колонка last_name")
    except Exception as e:
        print(f"Колонка last_name уже существует: {e}")
    
    conn.commit()