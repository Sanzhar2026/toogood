# migrate_db.py
import psycopg2
from psycopg2 import sql
import sys

# Параметры подключения
DB_CONFIG = {
    "host": "dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com",
    "port": 5432,
    "database": "toogood_db_a3k0",
    "user": "toogood_db_a3k0_user",
    "password": "2tWztMrzy1VCriWHefthkLBK1EOeeYnG",
    "sslmode": "require"
}

# SQL команды для выполнения
SQL_COMMANDS = [
    # 1. Добавление колонок в surprise_bags
    """
    ALTER TABLE surprise_bags ADD COLUMN IF NOT EXISTS description TEXT
    """,
    """
    ALTER TABLE surprise_bags ADD COLUMN IF NOT EXISTS pickup_start_time VARCHAR(50)
    """,
    """
    ALTER TABLE surprise_bags ADD COLUMN IF NOT EXISTS pickup_end_time VARCHAR(50)
    """,
    """
    ALTER TABLE surprise_bags ADD COLUMN IF NOT EXISTS total_quantity INTEGER DEFAULT 1
    """,
    
    # 2. Создание таблицы surprise_bag_items
    """
    CREATE TABLE IF NOT EXISTS surprise_bag_items (
        id SERIAL PRIMARY KEY,
        surprise_bag_id INTEGER NOT NULL REFERENCES surprise_bags(id) ON DELETE CASCADE,
        product_id INTEGER NOT NULL,
        product_name VARCHAR(255) NOT NULL,
        product_price INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """,
    
    # 3. Создание индексов
    """
    CREATE INDEX IF NOT EXISTS idx_surprise_bag_items_bag_id 
    ON surprise_bag_items(surprise_bag_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_surprise_bag_items_product_id 
    ON surprise_bag_items(product_id)
    """,
    
    # 4. Проверка delivery_type в orders
    """
    ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_type VARCHAR(50) DEFAULT 'delivery'
    """,
    
    # 5. Добавление значений в enum (если нужно)
    """
    DO $$
    BEGIN
        BEGIN
            ALTER TYPE orderstatus ADD VALUE 'picked_up';
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END;
    END$$;
    """,
    """
    DO $$
    BEGIN
        BEGIN
            ALTER TYPE orderstatus ADD VALUE 'nearby';
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END;
    END$$;
    """
]

def run_migration():
    """Выполнить миграцию базы данных"""
    
    print("=" * 60)
    print("🚀 ЗАПУСК МИГРАЦИИ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    conn = None
    cur = None
    
    try:
        # Подключение к БД
        print("\n📡 Подключение к PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True  # Автоматический коммит
        cur = conn.cursor()
        print("✅ Подключено успешно!")
        
        # Выполнение каждой команды
        success_count = 0
        for i, sql_cmd in enumerate(SQL_COMMANDS, 1):
            try:
                print(f"\n[{i}/{len(SQL_COMMANDS)}] Выполнение...")
                cur.execute(sql_cmd)
                print(f"✅ OK")
                success_count += 1
            except Exception as e:
                print(f"⚠️ Ошибка (пропускаем): {e}")
        
        print("\n" + "=" * 60)
        print(f"✅ МИГРАЦИЯ ЗАВЕРШЕНА! (Успешно: {success_count}/{len(SQL_COMMANDS)})")
        print("=" * 60)
        
        # Проверка результатов
        print("\n📊 ПРОВЕРКА РЕЗУЛЬТАТОВ:")
        
        # Проверка таблиц
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('surprise_bags', 'surprise_bag_items')
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        print(f"   Таблицы: {[t[0] for t in tables]}")
        
        # Проверка колонок в surprise_bags
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'surprise_bags' 
            AND column_name IN ('description', 'pickup_start_time', 'pickup_end_time', 'total_quantity')
        """)
        columns = cur.fetchall()
        print(f"   Новые колонки в surprise_bags: {[c[0] for c in columns]}")
        
        # Проверка колонки delivery_type в orders
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'orders' AND column_name = 'delivery_type'
        """)
        delivery_type = cur.fetchone()
        print(f"   Колонка delivery_type в orders: {'✅ есть' if delivery_type else '❌ нет'}")
        
        # Количество записей
        cur.execute("SELECT COUNT(*) FROM surprise_bags")
        bags_count = cur.fetchone()[0]
        print(f"   Всего сюрприз-пакетов: {bags_count}")
        
        cur.execute("SELECT COUNT(*) FROM surprise_bag_items")
        items_count = cur.fetchone()[0]
        print(f"   Всего блюд в сюрпризах: {items_count}")
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("\n🔌 Соединение закрыто")

def check_database():
    """Проверить состояние базы данных"""
    
    print("\n" + "=" * 60)
    print("🔍 ДИАГНОСТИКА БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    conn = None
    cur = None
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Версия PostgreSQL
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        print(f"\n🐘 PostgreSQL версия: {version.split(',')[0]}")
        
        # 2. Список всех таблиц
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        print(f"\n📋 Таблицы в БД ({len(tables)}):")
        for table in tables:
            print(f"   - {table[0]}")
        
        # 3. Проверка surprise_bag_items структуры
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'surprise_bag_items'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        if columns:
            print(f"\n📋 Структура surprise_bag_items:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # 4. Проверка enum orderstatus
        cur.execute("SELECT enum_range(NULL::orderstatus)")
        enum_values = cur.fetchone()[0]
        print(f"\n📋 Enum orderstatus: {enum_values}")
        
        # 5. Статистика
        cur.execute("SELECT COUNT(*) FROM surprise_bags")
        bags_count = cur.fetchone()[0]
        print(f"\n📊 Статистика:")
        print(f"   Сюрприз-пакетов: {bags_count}")
        
        cur.execute("SELECT COUNT(*) FROM surprise_bag_items")
        items_count = cur.fetchone()[0]
        print(f"   Блюд в сюрпризах: {items_count}")
        
        cur.execute("SELECT COUNT(*) FROM orders")
        orders_count = cur.fetchone()[0]
        print(f"   Заказов: {orders_count}")
        
        cur.execute("SELECT COUNT(*) FROM users")
        users_count = cur.fetchone()[0]
        print(f"   Пользователей: {users_count}")
        
    except Exception as e:
        print(f"❌ Ошибка диагностики: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def fix_bag_quantities():
    """Восстановить количество товаров"""
    
    print("\n" + "=" * 60)
    print("🔄 ВОССТАНОВЛЕНИЕ КОЛИЧЕСТВА ТОВАРОВ")
    print("=" * 60)
    
    conn = None
    cur = None
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Обновляем товары с нулевым количеством
        cur.execute("""
            UPDATE surprise_bags 
            SET available_quantity = 10, is_active = true 
            WHERE available_quantity = 0 OR available_quantity IS NULL
        """)
        
        updated = cur.rowcount
        conn.commit()
        
        print(f"✅ Восстановлено {updated} товаров (available_quantity = 10)")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("\n" + "🔧 СКРИПТ УПРАВЛЕНИЯ БАЗОЙ ДАННЫХ")
    print("=" * 60)
    print("1 - Выполнить полную миграцию")
    print("2 - Только диагностика")
    print("3 - Восстановить количество товаров")
    print("4 - Выполнить всё")
    
    choice = input("\nВаш выбор (1-4): ").strip()
    
    if choice == "1":
        run_migration()
    elif choice == "2":
        check_database()
    elif choice == "3":
        fix_bag_quantities()
    elif choice == "4":
        run_migration()
        check_database()
        fix_bag_quantities()
    else:
        print("❌ Неверный выбор")