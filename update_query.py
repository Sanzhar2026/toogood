# update_enum_sa.py
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0"

def update_enum():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Добавляем значение 'nearby' в enum orderstatus
        try:
            conn.execute(text("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'nearby';"))
            conn.commit()
            print("✅ Значение 'nearby' добавлено в enum orderstatus")
        except Exception as e:
            print(f"⚠️ Ошибка при добавлении в orderstatus: {e}")
        
        # Добавляем значение 'nearby' в enum deliverystatus
        try:
            conn.execute(text("ALTER TYPE deliverystatus ADD VALUE IF NOT EXISTS 'nearby';"))
            conn.commit()
            print("✅ Значение 'nearby' добавлено в enum deliverystatus")
        except Exception as e:
            print(f"⚠️ Ошибка при добавлении в deliverystatus: {e}")

if __name__ == "__main__":
    update_enum()