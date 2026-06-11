# add_columns.py
import psycopg2
from psycopg2.extras import RealDictCursor

# Ваши данные для подключения
DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0"

def add_columns():
    try:
        # Подключаемся к базе данных
        print("🔌 Подключение к базе данных...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        print("✅ Подключено успешно!")
        
        # Добавляем колонку rating
        print("\n📝 Добавляем колонку rating...")
        cursor.execute("""
            ALTER TABLE surprise_bags 
            ADD COLUMN IF NOT EXISTS rating DOUBLE PRECISION DEFAULT 0
        """)
        print("✅ Колонка rating добавлена")
        
        # Добавляем колонку total_reviews
        print("\n📝 Добавляем колонку total_reviews...")
        cursor.execute("""
            ALTER TABLE surprise_bags 
            ADD COLUMN IF NOT EXISTS total_reviews INTEGER DEFAULT 0
        """)
        print("✅ Колонка total_reviews добавлена")
        
        # Создаём таблицу отзывов для сюрпризов (если нет)
        print("\n📝 Создаём таблицу surprise_bag_reviews...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS surprise_bag_reviews (
                id SERIAL PRIMARY KEY,
                surprise_bag_id INTEGER NOT NULL REFERENCES surprise_bags(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Таблица surprise_bag_reviews создана")
        
        # Добавляем индексы
        print("\n📝 Добавляем индексы...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_surprise_bag_reviews_bag_id 
            ON surprise_bag_reviews(surprise_bag_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_surprise_bag_reviews_user_id 
            ON surprise_bag_reviews(user_id)
        """)
        print("✅ Индексы добавлены")
        
        # Сохраняем изменения
        conn.commit()
        print("\n" + "="*50)
        print("✅ ВСЕ ИЗМЕНЕНИЯ УСПЕШНО ПРИМЕНЕНЫ!")
        print("="*50)
        
        # Проверяем результат
        print("\n🔍 Проверяем структуру таблицы...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'surprise_bags'
            AND column_name IN ('rating', 'total_reviews')
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[0]}: {col[1]}, nullable={col[2]}")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("\n🔌 Соединение закрыто")

if __name__ == "__main__":
    add_columns()