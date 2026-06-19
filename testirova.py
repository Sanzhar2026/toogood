# recreate_tables.py - ПЕРЕСОЗДАНИЕ ТАБЛИЦ БЕЗ ENUM

import psycopg2

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0?sslmode=require"

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def drop_all_tables():
    """Удалить все таблицы"""
    conn = get_connection()
    cur = conn.cursor()
    
    print("🚀 Удаление всех таблиц...")
    
    tables = [
        "temporary_reservations", "assigned_orders", "supplier_couriers",
        "courier_profiles", "order_tracking", "orders",
        "cart_items", "surprise_bag_reviews", "supplier_reviews",
        "surprise_bag_items", "surprise_bags", "foods",
        "supplier_products", "suppliers", "users", "admins"
    ]
    
    for table in tables:
        try:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            print(f"  ✅ Удалена таблица {table}")
        except Exception as e:
            print(f"  ❌ Ошибка при удалении {table}: {e}")
    
    # Удаляем ENUM если есть
    try:
        cur.execute("DROP TYPE IF EXISTS userrole CASCADE;")
        print("  ✅ Удален ENUM userrole")
    except Exception as e:
        print(f"  ❌ Ошибка при удалении ENUM: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ ВСЕ ТАБЛИЦЫ УДАЛЕНЫ!")

def create_all_tables():
    """Создать все таблицы заново (БЕЗ ENUM)"""
    conn = get_connection()
    cur = conn.cursor()
    
    print("🚀 Создание таблиц...")
    
    # ============================================================
    # 1. ТАБЛИЦА users (БЕЗ ENUM)
    # ============================================================
    cur.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE,
            phone VARCHAR(50) UNIQUE NOT NULL,
            phone_verified BOOLEAN DEFAULT FALSE,
            password VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            full_name VARCHAR(255),
            role VARCHAR(50) DEFAULT 'customer',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  ✅ Таблица users создана")
    
    # ============================================================
    # 2. ТАБЛИЦА suppliers
    # ============================================================
    cur.execute("""
        CREATE TABLE suppliers (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            business_name VARCHAR(255) NOT NULL,
            business_type VARCHAR(100),
            description TEXT,
            logo VARCHAR(500),
            cover_image VARCHAR(500),
            address VARCHAR(500),
            city VARCHAR(100),
            lat FLOAT,
            lon FLOAT,
            phone VARCHAR(50),
            email VARCHAR(255),
            rating FLOAT DEFAULT 0,
            total_reviews INTEGER DEFAULT 0,
            is_verified BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pickup_start_time VARCHAR(50),
            pickup_end_time VARCHAR(50)
        );
    """)
    print("  ✅ Таблица suppliers создана")
    
    # ============================================================
    # 3. ТАБЛИЦА supplier_products
    # ============================================================
    cur.execute("""
        CREATE TABLE supplier_products (
            id SERIAL PRIMARY KEY,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
            name_ru VARCHAR(255) NOT NULL,
            name_kz VARCHAR(255) NOT NULL,
            name_en VARCHAR(255),
            description_ru TEXT,
            description_kz TEXT,
            price FLOAT NOT NULL,
            category VARCHAR(100),
            image_url VARCHAR(500),
            is_available BOOLEAN DEFAULT TRUE,
            preparation_time INTEGER DEFAULT 15,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  ✅ Таблица supplier_products создана")
    
    # ============================================================
    # 4. ТАБЛИЦА foods
    # ============================================================
    cur.execute("""
        CREATE TABLE foods (
            id SERIAL PRIMARY KEY,
            name_ru VARCHAR(255),
            name_kz VARCHAR(255),
            price FLOAT,
            image VARCHAR(500),
            discount INTEGER DEFAULT 0
        );
    """)
    print("  ✅ Таблица foods создана")
    
    # ============================================================
    # 5. ТАБЛИЦА surprise_bags
    # ============================================================
    cur.execute("""
        CREATE TABLE surprise_bags (
            id SERIAL PRIMARY KEY,
            supplier_id INTEGER REFERENCES suppliers(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            original_price FLOAT NOT NULL,
            discounted_price FLOAT NOT NULL,
            discount_percentage INTEGER,
            image_url VARCHAR(500),
            available_quantity INTEGER DEFAULT 1,
            total_quantity INTEGER DEFAULT 1,
            pickup_start_time VARCHAR(50),
            pickup_end_time VARCHAR(50),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            possible_items TEXT,
            city VARCHAR(100),
            hide_contents BOOLEAN DEFAULT FALSE,
            rating FLOAT DEFAULT 0,
            total_reviews INTEGER DEFAULT 0
        );
    """)
    print("  ✅ Таблица surprise_bags создана")
    
    # ============================================================
    # 6. ТАБЛИЦА surprise_bag_items
    # ============================================================
    cur.execute("""
        CREATE TABLE surprise_bag_items (
            id SERIAL PRIMARY KEY,
            surprise_bag_id INTEGER REFERENCES surprise_bags(id) ON DELETE CASCADE,
            supplier_product_id INTEGER REFERENCES supplier_products(id) ON DELETE CASCADE,
            product_id INTEGER,
            product_name VARCHAR(255),
            product_price INTEGER,
            quantity INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  ✅ Таблица surprise_bag_items создана")
    
    # ============================================================
    # 7. ТАБЛИЦА supplier_reviews
    # ============================================================
    cur.execute("""
        CREATE TABLE supplier_reviews (
            id SERIAL PRIMARY KEY,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  ✅ Таблица supplier_reviews создана")
    
    # ============================================================
    # 8. ТАБЛИЦА surprise_bag_reviews
    # ============================================================
    cur.execute("""
        CREATE TABLE surprise_bag_reviews (
            id SERIAL PRIMARY KEY,
            surprise_bag_id INTEGER NOT NULL REFERENCES surprise_bags(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  ✅ Таблица surprise_bag_reviews создана")
    
    # ============================================================
    # 9. ТАБЛИЦА cart_items
    # ============================================================
    cur.execute("""
        CREATE TABLE cart_items (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            surprise_bag_id INTEGER REFERENCES surprise_bags(id) ON DELETE CASCADE,
            quantity INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  ✅ Таблица cart_items создана")
    
    # ============================================================
    # 10. ТАБЛИЦА orders
    # ============================================================
    cur.execute("""
        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            food_id INTEGER REFERENCES foods(id) ON DELETE SET NULL,
            supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
            surprise_bag_id INTEGER REFERENCES surprise_bags(id) ON DELETE SET NULL,
            items TEXT,
            total_amount FLOAT,
            order_number VARCHAR(50) UNIQUE,
            status VARCHAR(50) DEFAULT 'pending',
            payment_id VARCHAR(100),
            payment_status VARCHAR(50) DEFAULT 'pending',
            payment_method VARCHAR(50),
            paid_at TIMESTAMP,
            payment_amount FLOAT,
            transaction_id VARCHAR(100),
            customer_lat FLOAT,
            customer_lon FLOAT,
            customer_address VARCHAR(500),
            lat FLOAT,
            lon FLOAT,
            address VARCHAR(500),
            driver_lat FLOAT,
            driver_lon FLOAT,
            last_location_update TIMESTAMP,
            delivery_started_at TIMESTAMP,
            delivery_deadline TIMESTAMP,
            auto_refund_processed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confirmed_at TIMESTAMP,
            ready_at TIMESTAMP,
            delivered_at TIMESTAMP,
            cancelled_at TIMESTAMP,
            pickup_time VARCHAR(50),
            amount_paid FLOAT,
            assigned_courier_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            delivery_type VARCHAR(50) DEFAULT 'delivery'
        );
    """)
    print("  ✅ Таблица orders создана")
    
    # ============================================================
    # 11. ТАБЛИЦА order_tracking
    # ============================================================
    cur.execute("""
        CREATE TABLE order_tracking (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
            status VARCHAR(50),
            lat FLOAT,
            lon FLOAT,
            message VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  ✅ Таблица order_tracking создана")
    
    # ============================================================
    # 12. ТАБЛИЦА courier_profiles
    # ============================================================
    cur.execute("""
        CREATE TABLE courier_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            phone VARCHAR(50) UNIQUE NOT NULL,
            courier_type VARCHAR(20) DEFAULT 'pedestrian',
            car_model VARCHAR(100),
            car_number VARCHAR(50),
            speed_kmh FLOAT DEFAULT 5.0,
            delivery_radius_km FLOAT DEFAULT 3.0,
            is_online BOOLEAN DEFAULT FALSE,
            is_available BOOLEAN DEFAULT TRUE,
            is_verified BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            rating FLOAT DEFAULT 5.0,
            total_deliveries INTEGER DEFAULT 0,
            completed_orders_today INTEGER DEFAULT 0,
            current_lat FLOAT,
            current_lon FLOAT,
            last_location_update TIMESTAMP,
            current_order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
            current_order_status VARCHAR(50),
            proposed_order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
            proposed_order_expires_at TIMESTAMP,
            last_online_at TIMESTAMP,
            last_offline_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified_at TIMESTAMP
        );
    """)
    print("  ✅ Таблица courier_profiles создана")
    
    # ============================================================
    # 13. ТАБЛИЦА supplier_couriers
    # ============================================================
    cur.execute("""
        CREATE TABLE supplier_couriers (
            id SERIAL PRIMARY KEY,
            supplier_id INTEGER REFERENCES suppliers(id) ON DELETE CASCADE,
            courier_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  ✅ Таблица supplier_couriers создана")
    
    # ============================================================
    # 14. ТАБЛИЦА assigned_orders
    # ============================================================
    cur.execute("""
        CREATE TABLE assigned_orders (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
            courier_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            status VARCHAR(50) DEFAULT 'assigned',
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            delivered_at TIMESTAMP
        );
    """)
    print("  ✅ Таблица assigned_orders создана")
    
    # ============================================================
    # 15. ТАБЛИЦА admins
    # ============================================================
    cur.execute("""
        CREATE TABLE admins (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  ✅ Таблица admins создана")
    
    # ============================================================
    # 16. ТАБЛИЦА temporary_reservations
    # ============================================================
    cur.execute("""
        CREATE TABLE temporary_reservations (
            id SERIAL PRIMARY KEY,
            bag_id INTEGER NOT NULL REFERENCES surprise_bags(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            quantity INTEGER DEFAULT 1,
            reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_paid BOOLEAN DEFAULT FALSE
        );
    """)
    print("  ✅ Таблица temporary_reservations создана")
    
    # ============================================================
    # 17. ИНДЕКСЫ
    # ============================================================
    print("📊 Создание индексов...")
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_supplier_products_supplier_id ON supplier_products(supplier_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_supplier_products_category ON supplier_products(category);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_supplier_products_is_available ON supplier_products(is_available);")
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_surprise_bags_supplier_id ON surprise_bags(supplier_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_surprise_bags_is_active ON surprise_bags(is_active);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_surprise_bags_city ON surprise_bags(city);")
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_supplier_id ON orders(supplier_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);")
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_courier_profiles_is_online ON courier_profiles(is_online);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_courier_profiles_is_available ON courier_profiles(is_available);")
    
    print("  ✅ Индексы созданы")
    
    # ============================================================
    # 18. ТРИГГЕР
    # ============================================================
    cur.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    cur.execute("""
        DROP TRIGGER IF EXISTS update_supplier_products_updated_at ON supplier_products;
        CREATE TRIGGER update_supplier_products_updated_at
            BEFORE UPDATE ON supplier_products
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)
    print("  ✅ Триггер создан")
    
    # ============================================================
    # 19. ТЕСТОВЫЕ ДАННЫЕ
    # ============================================================
    print("📝 Добавление тестовых продуктов...")
    cur.execute("""
        INSERT INTO foods (name_ru, name_kz, price, image, discount) VALUES
        ('Маргарита Пицца', 'Маргарита Пицца', 2500, '', 0),
        ('Пепперони Пицца', 'Пепперони Пицца', 3200, '', 0),
        ('Гамбургер', 'Гамбургер', 1800, '', 0),
        ('Кока-Кола', 'Кока-Кола', 500, '', 0),
        ('Чизкейк', 'Чизкейк', 1200, '', 0),
        ('Картошка Фри', 'Картоп Фри', 800, '', 0)
        ON CONFLICT DO NOTHING;
    """)
    print("  ✅ Тестовые продукты добавлены")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("=" * 50)
    print("🎉 ВСЕ ТАБЛИЦЫ УСПЕШНО ПЕРЕСОЗДАНЫ!")
    print("=" * 50)

if __name__ == "__main__":
    print("=" * 50)
    print("⚠️ ВНИМАНИЕ! Это удалит ВСЕ данные!")
    print("=" * 50)
    confirm = input("Продолжить? (yes/no): ")
    
    if confirm.lower() == "yes":
        drop_all_tables()
        create_all_tables()
    else:
        print("❌ Отменено")