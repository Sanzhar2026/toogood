# check_enum_final.py
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Проверяем orderstatus
    result = conn.execute(text("SELECT enum_range(NULL::orderstatus);"))
    values = result.fetchone()[0]
    print("📊 Значения в enum orderstatus:")
    print(values)
    print()
    
    # Проверяем deliverystatus
    result2 = conn.execute(text("SELECT enum_range(NULL::deliverystatus);"))
    values2 = result2.fetchone()[0]
    print("📊 Значения в enum deliverystatus:")
    print(values2)