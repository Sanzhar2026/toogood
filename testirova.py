# create_deliverystatus_enum.py
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0?sslmode=require"

def create_deliverystatus_enum():
    """Создать enum deliverystatus в базе данных"""
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cur = conn.cursor()
        
        print("=" * 60)
        print("СОЗДАНИЕ ENUM deliverystatus")
        print("=" * 60)
        
        # 1. Проверяем существующие enum
        print("\n1) Проверка существующих enum:")
        cur.execute("""
            SELECT typname, enumlabel 
            FROM pg_type 
            JOIN pg_enum ON pg_type.oid = pg_enum.enumtypid 
            ORDER BY typname, enumsortorder
        """)
        
        existing_enums = cur.fetchall()
        print("   Существующие enum:")
        for enum in existing_enums:
            print(f"      {enum[0]}: {enum[1]}")
        
        # 2. Проверяем, существует ли deliverystatus
        cur.execute("""
            SELECT 1 FROM pg_type WHERE typname = 'deliverystatus'
        """)
        
        exists = cur.fetchone()
        
        if exists:
            print("\n2) ENUM deliverystatus уже существует!")
            
            # Показываем текущие значения
            cur.execute("SELECT enum_range(NULL::deliverystatus)")
            values = cur.fetchone()[0]
            print(f"   Текущие значения: {values}")
            
            # Спрашиваем, нужно ли обновить
            print("\n   Хотите добавить недостающие значения?")
            print("   at_supplier, en_route, nearby, arrived")
            
            # Добавляем недостающие значения
            current_values = str(values).strip('{}').split(',')
            current_values = [v.strip() for v in current_values]
            
            needed_values = ['at_supplier', 'en_route', 'nearby', 'arrived']
            missing_values = [v for v in needed_values if v not in current_values]
            
            if missing_values:
                print(f"\n   Добавляем недостающие значения: {missing_values}")
                for val in missing_values:
                    try:
                        cur.execute(f"ALTER TYPE deliverystatus ADD VALUE '{val}'")
                        print(f"      ✅ Добавлено: {val}")
                    except Exception as e:
                        print(f"      ⚠️ {e}")
                conn.commit()
                print("   ✅ Все значения добавлены!")
            else:
                print("   ✅ Все значения уже есть!")
            
        else:
            print("\n2) Создание ENUM deliverystatus...")
            
            # Создаем enum
            cur.execute("""
                CREATE TYPE deliverystatus AS ENUM (
                    'at_supplier',
                    'en_route', 
                    'nearby',
                    'arrived'
                )
            """)
            print("   ✅ ENUM deliverystatus создан!")
            
            conn.commit()
        
        # 3. Проверяем структуру таблицы orders
        print("\n3) Проверка таблицы orders:")
        cur.execute("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'orders' AND column_name = 'delivery_status'
        """)
        
        column_info = cur.fetchone()
        if column_info:
            print(f"   Колонка delivery_status существует")
            print(f"   Тип: {column_info[1]}, UDT: {column_info[2]}")
            
            # Проверяем, правильный ли тип
            if column_info[2] != 'deliverystatus' and column_info[1] == 'USER-DEFINED':
                print("   ⚠️ Колонка имеет другой тип. Пытаемся изменить...")
                try:
                    cur.execute("""
                        ALTER TABLE orders 
                        ALTER COLUMN delivery_status TYPE deliverystatus 
                        USING delivery_status::text::deliverystatus
                    """)
                    conn.commit()
                    print("   ✅ Тип колонки изменен на deliverystatus")
                except Exception as e:
                    print(f"   ❌ Ошибка: {e}")
                    print("   Возможно, нужно удалить колонку и создать заново")
        else:
            print("   Колонка delivery_status НЕ существует")
            print("   Добавляем колонку...")
            try:
                cur.execute("""
                    ALTER TABLE orders 
                    ADD COLUMN delivery_status deliverystatus DEFAULT 'at_supplier'
                """)
                conn.commit()
                print("   ✅ Колонка добавлена!")
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
        
        # 4. Проверяем структуру таблицы order_tracking
        print("\n4) Проверка таблицы order_tracking:")
        cur.execute("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'order_tracking' AND column_name = 'delivery_status'
        """)
        
        column_info = cur.fetchone()
        if column_info:
            print(f"   Колонка delivery_status существует")
            print(f"   Тип: {column_info[1]}, UDT: {column_info[2]}")
            
            if column_info[2] != 'deliverystatus' and column_info[1] == 'USER-DEFINED':
                print("   ⚠️ Колонка имеет другой тип. Пытаемся изменить...")
                try:
                    cur.execute("""
                        ALTER TABLE order_tracking 
                        ALTER COLUMN delivery_status TYPE deliverystatus 
                        USING delivery_status::text::deliverystatus
                    """)
                    conn.commit()
                    print("   ✅ Тип колонки изменен на deliverystatus")
                except Exception as e:
                    print(f"   ❌ Ошибка: {e}")
        else:
            print("   Колонка delivery_status НЕ существует")
            print("   Добавляем колонку...")
            try:
                cur.execute("""
                    ALTER TABLE order_tracking 
                    ADD COLUMN delivery_status deliverystatus
                """)
                conn.commit()
                print("   ✅ Колонка добавлена!")
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
        
        # 5. Финальная проверка
        print("\n5) Финальная проверка:")
        cur.execute("SELECT enum_range(NULL::deliverystatus)")
        final_values = cur.fetchone()[0]
        print(f"   ENUM deliverystatus: {final_values}")
        
        cur.execute("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name IN ('orders', 'order_tracking') 
              AND column_name = 'delivery_status'
        """)
        
        columns = cur.fetchall()
        print("\n   Колонки delivery_status:")
        for col in columns:
            print(f"      Таблица: {col[0]}, Тип: {col[1]}, UDT: {col[2]}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ ГОТОВО! ENUM deliverystatus создан и настроен!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        if conn:
            conn.rollback()
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_deliverystatus_enum()