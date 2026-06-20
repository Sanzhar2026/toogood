# remove_enum.py - СКРИПТ ДЛЯ УДАЛЕНИЯ ENUM

import psycopg2
from psycopg2.extras import RealDictCursor
import os

# ТВОЯ СТРОКА ПОДКЛЮЧЕНИЯ
DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0?sslmode=require"

def get_connection():
    """Подключение к базе данных"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Подключение к БД успешно!")
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return None

def check_enum_types():
    """Проверка существующих ENUM типов"""
    conn = get_connection()
    if not conn:
        return
    
    cur = conn.cursor()
    
    # Проверяем все ENUM типы
    cur.execute("""
        SELECT typname, typcategory 
        FROM pg_type 
        WHERE typcategory = 'E'
        ORDER BY typname;
    """)
    
    enums = cur.fetchall()
    cur.close()
    conn.close()
    
    if enums:
        print("📊 Найденные ENUM типы:")
        for enum in enums:
            print(f"  - {enum[0]}")
    else:
        print("ℹ️ ENUM типов не найдено")
    
    return enums

def check_columns_with_enum():
    """Проверка колонок, использующих ENUM"""
    conn = get_connection()
    if not conn:
        return
    
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            table_name, 
            column_name, 
            udt_name 
        FROM information_schema.columns 
        WHERE udt_name IN (
            SELECT typname 
            FROM pg_type 
            WHERE typcategory = 'E'
        )
        ORDER BY table_name, column_name;
    """)
    
    columns = cur.fetchall()
    cur.close()
    conn.close()
    
    if columns:
        print("📊 Колонки с ENUM типом:")
        for col in columns:
            print(f"  - {col[0]}.{col[1]} ({col[2]})")
    else:
        print("ℹ️ Колонок с ENUM типом не найдено")
    
    return columns

def convert_enum_to_varchar():
    """Преобразование ENUM колонок в VARCHAR"""
    conn = get_connection()
    if not conn:
        return False
    
    cur = conn.cursor()
    
    # Получаем все колонки с ENUM
    cur.execute("""
        SELECT 
            table_name, 
            column_name, 
            udt_name 
        FROM information_schema.columns 
        WHERE udt_name IN (
            SELECT typname 
            FROM pg_type 
            WHERE typcategory = 'E'
        )
        ORDER BY table_name, column_name;
    """)
    
    columns = cur.fetchall()
    
    if not columns:
        print("ℹ️ Нет колонок с ENUM для преобразования")
        cur.close()
        conn.close()
        return True
    
    print(f"🔄 Начинаем преобразование {len(columns)} колонок...")
    
    for table, column, enum_type in columns:
        try:
            # Преобразуем колонку в VARCHAR
            print(f"  - Преобразование {table}.{column} ({enum_type}) -> VARCHAR")
            cur.execute(f"""
                ALTER TABLE {table} 
                ALTER COLUMN {column} TYPE VARCHAR(50) 
                USING {column}::text;
            """)
            print(f"    ✅ {table}.{column} преобразован в VARCHAR")
        except Exception as e:
            print(f"    ❌ Ошибка при преобразовании {table}.{column}: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    return True

def drop_enum_types():
    """Удаление ENUM типов"""
    conn = get_connection()
    if not conn:
        return False
    
    cur = conn.cursor()
    
    # Получаем все ENUM типы
    cur.execute("""
        SELECT typname 
        FROM pg_type 
        WHERE typcategory = 'E'
        ORDER BY typname;
    """)
    
    enums = cur.fetchall()
    
    if not enums:
        print("ℹ️ Нет ENUM типов для удаления")
        cur.close()
        conn.close()
        return True
    
    print(f"🗑️ Удаляем {len(enums)} ENUM типов...")
    
    for enum in enums:
        enum_name = enum[0]
        try:
            print(f"  - Удаление {enum_name}...")
            cur.execute(f"DROP TYPE IF EXISTS {enum_name} CASCADE;")
            print(f"    ✅ {enum_name} удален")
        except Exception as e:
            print(f"    ❌ Ошибка при удалении {enum_name}: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    return True

def fix_user_roles():
    """Исправление ролей пользователей (приведение к нижнему регистру)"""
    conn = get_connection()
    if not conn:
        return False
    
    cur = conn.cursor()
    
    # Проверяем текущие роли
    cur.execute("""
        SELECT DISTINCT role FROM users;
    """)
    
    roles = cur.fetchall()
    print(f"📊 Текущие роли в таблице users: {[r[0] for r in roles]}")
    
    # Преобразуем все роли в нижний регистр
    cur.execute("""
        UPDATE users 
        SET role = LOWER(role) 
        WHERE role IS NOT NULL;
    """)
    
    affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Обновлено {affected} записей (роли приведены к нижнему регистру)")
    return True

def main():
    """Главная функция"""
    print("=" * 50)
    print("🔧 УДАЛЕНИЕ ENUM ИЗ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    # 1. Проверяем ENUM типы
    print("\n1️⃣ Проверка ENUM типов...")
    check_enum_types()
    
    # 2. Проверяем колонки с ENUM
    print("\n2️⃣ Проверка колонок с ENUM...")
    check_columns_with_enum()
    
    # 3. Преобразуем ENUM в VARCHAR
    print("\n3️⃣ Преобразование ENUM в VARCHAR...")
    if not convert_enum_to_varchar():
        print("❌ Ошибка при преобразовании")
        return
    
    # 4. Удаляем ENUM типы
    print("\n4️⃣ Удаление ENUM типов...")
    if not drop_enum_types():
        print("❌ Ошибка при удалении ENUM")
        return
    
    # 5. Исправляем роли пользователей
    print("\n5️⃣ Исправление ролей пользователей...")
    fix_user_roles()
    
    # 6. Проверяем результат
    print("\n6️⃣ Проверка результата...")
    check_enum_types()
    check_columns_with_enum()
    
    print("\n" + "=" * 50)
    print("🎉 ВСЕ ENUM УСПЕШНО УДАЛЕНЫ!")
    print("=" * 50)

if __name__ == "__main__":
    main()