# check_delivery_type_column.py
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=" * 60)
    print("🔍 ПРОВЕРКА КОЛОНКИ delivery_type В ТАБЛИЦЕ orders")
    print("=" * 60)
    
    # 1. Проверяем существует ли колонка
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'orders' AND column_name = 'delivery_type'
    """))
    
    column = result.fetchone()
    
    if column:
        print(f"\n✅ Колонка 'delivery_type' СУЩЕСТВУЕТ!")
        print(f"   Тип данных: {column[1]}")
        print(f"   Может быть NULL: {column[2]}")
    else:
        print(f"\n❌ Колонка 'delivery_type' НЕ СУЩЕСТВУЕТ!")
        print("\n   Нужно добавить:")
        print("   ALTER TABLE orders ADD COLUMN delivery_type VARCHAR(50) DEFAULT 'delivery';")
    
    # 2. Проверяем значения
    print("\n" + "=" * 60)
    print("📊 ПРОВЕРКА ЗНАЧЕНИЙ delivery_type")
    print("=" * 60)
    
    result = conn.execute(text("""
        SELECT delivery_type, COUNT(*) 
        FROM orders 
        GROUP BY delivery_type
    """))
    
    rows = result.fetchall()
    if rows:
        print("\n📋 Текущие значения:")
        for row in rows:
            print(f"   - {row[0]}: {row[1]} заказов")
    else:
        print("\n⚠️ Нет данных или колонка отсутствует")
    
    # 3. Показываем примеры заказов
    print("\n" + "=" * 60)
    print("📋 ПРИМЕРЫ ЗАКАЗОВ")
    print("=" * 60)
    
    result = conn.execute(text("""
        SELECT id, order_number, status, delivery_type, delivery_deadline, customer_lat
        FROM orders 
        ORDER BY id DESC 
        LIMIT 5
    """))
    
    print("\nID | № заказа | Статус | Тип доставки | Дедлайн | Координаты клиента")
    print("-" * 80)
    for row in result:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
    
    print("\n" + "=" * 60)