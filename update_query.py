# update_enum.py
from sqlalchemy import create_engine, text

# Строка подключения к твоей базе данных на Render
DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'nearby';"))
    conn.commit()

print("✅ Значение 'nearby' успешно добавлено в enum orderstatus")