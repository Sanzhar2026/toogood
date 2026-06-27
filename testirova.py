# create_templates_table.py
import psycopg2

DATABASE_URL = "postgresql://postgres:YHceVkBwWMtDTXqSbqQhsGrnIxeWlcwz@thomas.proxy.rlwy.net:27717/railway"

def create_table():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Создаем таблицу
    cur.execute("""
        CREATE TABLE IF NOT EXISTS supplier_templates (
            id SERIAL PRIMARY KEY,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            template_data TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    conn.commit()
    print("✅ Таблица supplier_templates создана!")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_table()