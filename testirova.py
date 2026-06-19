# add_category_column.py
import psycopg2

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0?sslmode=require"

def add_column():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("🚀 Добавление колонки category_id...")
        
        cur.execute("""
            ALTER TABLE supplier_products 
            ADD COLUMN IF NOT EXISTS category_id INTEGER REFERENCES supplier_categories(id) ON DELETE SET NULL;
        """)
        print("✅ Колонка category_id добавлена")
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_supplier_products_category_id ON supplier_products(category_id);
        """)
        print("✅ Индекс создан")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("=" * 40)
        print("🎉 ГОТОВО!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    add_column()