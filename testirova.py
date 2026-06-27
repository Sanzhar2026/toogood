# fix_all.py - ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ С БД

import psycopg2
from psycopg2.extras import RealDictCursor

# ✅ ТВОЯ БД НА RAILWAY
DATABASE_URL = "postgresql://postgres:YHceVkBwWMtDTXqSbqQhsGrnIxeWlcwz@thomas.proxy.rlwy.net:27717/railway"

def run_fix():
    conn = None
    cur = None
    try:
        print("🔌 Подключение к БД Railway...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("=" * 70)
        print("🛠 ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ С БД")
        print("=" * 70)
        
        # ============================================================
        # 1. ПРОВЕРЯЕМ И ДОБАВЛЯЕМ КОЛОНКУ icon
        # ============================================================
        print("\n📋 1. ПРОВЕРКА КОЛОНКИ icon...")
        
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'supplier_products' AND column_name = 'icon'
        """)
        
        if not cur.fetchone():
            print("   ➕ Добавляю колонку icon...")
            cur.execute("ALTER TABLE supplier_products ADD COLUMN icon VARCHAR(50) DEFAULT '🍽️'")
            print("   ✅ Колонка icon добавлена")
        else:
            print("   ✅ Колонка icon уже существует")
        
        # ============================================================
        # 2. ИСПРАВЛЯЕМ КОЛОНКУ description_ru
        # ============================================================
        print("\n📋 2. ИСПРАВЛЕНИЕ КОЛОНКИ description_ru...")
        
        # Проверяем, есть ли колонка description_ru
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'supplier_products' AND column_name = 'description_ru'
        """)
        
        if not cur.fetchone():
            print("   ➕ Добавляю колонку description_ru...")
            cur.execute("ALTER TABLE supplier_products ADD COLUMN description_ru TEXT")
            
            # Копируем данные из description
            cur.execute("""
                UPDATE supplier_products 
                SET description_ru = description 
                WHERE description IS NOT NULL
            """)
            print("   ✅ Колонка description_ru добавлена и заполнена")
        else:
            print("   ✅ Колонка description_ru уже существует")
        
        # ============================================================
        # 3. ОБНОВЛЯЕМ ИКОНКИ ДЛЯ ВСЕХ ТОВАРОВ
        # ============================================================
        print("\n📋 3. ОБНОВЛЕНИЕ ИКОНОК...")
        
        cur.execute("""
            SELECT id, name, icon FROM supplier_products
        """)
        
        products = cur.fetchall()
        print(f"   📦 Найдено товаров: {len(products)}")
        
        # Маппинг иконок
        icon_map = {
            # ЕДА
            'пицц': '🍕', 'pizza': '🍕', 'маргарит': '🍕', 'пепперони': '🍕',
            'бургер': '🍔', 'burger': '🍔', 
            'донер': '🌯', 'шаурм': '🥙', 'кебаб': '🥙',
            'суши': '🍣', 'sushi': '🍣', 'ролл': '🍣', 'roll': '🍣',
            'салат': '🥗', 'salad': '🥗', 'цезарь': '🥗', 'греческ': '🥗',
            'картошк': '🍟', 'fries': '🍟', 'фри': '🍟',
            'куриц': '🍗', 'chicken': '🍗', 'крилс': '🍗', 'wings': '🍗',
            'стейк': '🥩', 'steak': '🥩', 'говядин': '🥩',
            'паста': '🍝', 'pasta': '🍝', 'спагетти': '🍝', 'макарон': '🍝',
            'суп': '🍲', 'soup': '🍲', 'борщ': '🍲',
            'десерт': '🍰', 'dessert': '🍰', 'торт': '🍰', 'cake': '🍰',
            'хот-дог': '🌭', 'hot dog': '🌭',
            'сэндвич': '🥪', 'sandwich': '🥪',
            'буррито': '🌯', 'burrito': '🌯',
            'фалафель': '🧆', 'falafel': '🧆',
            'плов': '🥘', 'plov': '🥘',
            'креветк': '🍤', 'shrimp': '🍤',
            'бенто': '🍱', 'bento': '🍱',
            'карри': '🍛', 'curry': '🍛',
            'лапш': '🍜', 'noodle': '🍜',
            'пельмен': '🥟', 'dumpling': '🥟',
            'фондю': '🫕', 'fondue': '🫕',
            
            # МОЛОЧНЫЕ
            'сыр': '🧀', 'cheese': '🧀',
            'молоко': '🥛', 'milk': '🥛',
            'морожен': '🍦', 'ice cream': '🍦',
            'яйц': '🥚', 'egg': '🥚',
            'масло': '🧈', 'butter': '🧈',
            'блин': '🥞', 'pancake': '🥞',
            'вафл': '🧇', 'waffle': '🧇',
            'сливк': '🍶', 'cream': '🍶',
            
            # ВЫПЕЧКА
            'кекс': '🧁', 'cupcake': '🧁',
            'пирог': '🥧', 'pie': '🥧',
            'печень': '🍪', 'cookie': '🍪',
            'пончик': '🍩', 'donut': '🍩',
            'шоколад': '🍫', 'chocolate': '🍫',
            'конфет': '🍬', 'candy': '🍬',
            'леденец': '🍭', 'lollipop': '🍭',
            'пудинг': '🍮', 'pudding': '🍮',
            'круассан': '🥐', 'croissant': '🥐',
            'багет': '🥖', 'baguette': '🥖',
            'хлеб': '🍞', 'bread': '🍞',
            'бублик': '🥯', 'bagel': '🥯',
            'лепешк': '🫓', 'flatbread': '🫓',
            
            # НАПИТКИ
            'кофе': '☕', 'coffee': '☕', 'капучино': '☕', 'латте': '☕',
            'чай': '🍵', 'tea': '🍵',
            'сок': '🧃', 'juice': '🧃',
            'напит': '🥤', 'drink': '🥤',
            'кола': '🥤', 'coca': '🥤', 'лимонад': '🥤',
            'пиво': '🍺', 'beer': '🍺',
            'вино': '🍷', 'wine': '🍷',
            'виски': '🥃', 'whiskey': '🥃',
            'коктейль': '🍸', 'cocktail': '🍸',
            'шампанск': '🍾', 'champagne': '🍾',
            'вода': '💧', 'water': '💧',
            'лёд': '🧊', 'ice': '🧊',
            
            # ФРУКТЫ И ОВОЩИ
            'яблок': '🍎', 'apple': '🍎',
            'груш': '🍐', 'pear': '🍐',
            'апельсин': '🍊', 'orange': '🍊',
            'лимон': '🍋', 'lemon': '🍋',
            'банан': '🍌', 'banana': '🍌',
            'арбуз': '🍉', 'watermelon': '🍉',
            'виноград': '🍇', 'grape': '🍇',
            'клубник': '🍓', 'strawberry': '🍓',
            'черник': '🫐', 'blueberry': '🫐',
            'персик': '🍑', 'peach': '🍑',
            'вишн': '🍒', 'cherry': '🍒',
            'ананас': '🍍', 'pineapple': '🍍',
            'манго': '🥭', 'mango': '🥭',
            'дын': '🍈', 'melon': '🍈',
            'киви': '🥝', 'kiwi': '🥝',
            'помидор': '🍅', 'tomato': '🍅',
            'огурец': '🥒', 'cucumber': '🥒',
            'перец': '🌶️', 'pepper': '🌶️',
            'морков': '🥕', 'carrot': '🥕',
            'чеснок': '🧄', 'garlic': '🧄',
            'лук': '🧅', 'onion': '🧅',
            'картофель': '🥔', 'potato': '🥔',
            'гриб': '🍄', 'mushroom': '🍄',
            'кукуруз': '🌽', 'corn': '🌽',
            
            # РЫБА
            'рыб': '🐟', 'fish': '🐟',
            'лосос': '🐟', 'salmon': '🐟',
            'семг': '🐟',
            'лобстер': '🦞', 'lobster': '🦞',
            'краб': '🦀', 'crab': '🦀',
            'осьминог': '🐙', 'octopus': '🐙',
            'кальмар': '🦑', 'squid': '🦑',
            'ракушк': '🐚', 'shell': '🐚',
            
            # СОУСЫ
            'соль': '🧂', 'salt': '🧂',
            'трав': '🌿', 'herb': '🌿',
            'мёд': '🍯', 'honey': '🍯',
            'соус': '🥫', 'sauce': '🥫',
            
            # ХОЗТОВАРЫ
            'веник': '🧹', 'broom': '🧹',
            'корзин': '🧺', 'basket': '🧺',
            'губк': '🧽', 'sponge': '🧽',
            'мыть': '🧴', 'clean': '🧴',
            'нитк': '🧵', 'thread': '🧵',
            'ведр': '🪣', 'bucket': '🪣',
            'вантуз': '🪠', 'plunger': '🪠',
            'перчатк': '🧤', 'glove': '🧤',
            'носок': '🧦', 'sock': '🧦',
            'футболк': '👕', 't-shirt': '👕',
            'штаны': '👖', 'pants': '👖',
            'плать': '👗', 'dress': '👗',
            'галстук': '👔', 'tie': '👔',
            'кроссовк': '👟', 'sneaker': '👟',
            'туфл': '👠', 'heel': '👠',
            'чемодан': '🧳', 'suitcase': '🧳',
            'рюкзак': '🎒', 'backpack': '🎒',
            'сумк': '👜', 'bag': '👜',
            'кепк': '🧢', 'cap': '🧢',
            'каск': '⛑️', 'helmet': '⛑️',
            'зубн': '🪥', 'toothbrush': '🪥',
            'шампун': '🧴', 'shampoo': '🧴',
            'туалет': '🧻', 'toilet': '🧻',
            'зеркал': '🪞', 'mirror': '🪞',
            'бритв': '🪒', 'razor': '🪒',
            'булавк': '🧷', 'pin': '🧷',
            'игрушк': '🧸', 'toy': '🧸',
            'игр': '🎮', 'game': '🎮',
            'книг': '📚', 'book': '📚',
            'ручк': '🖊️', 'pen': '🖊️',
            'блокнот': '📝', 'notebook': '📝',
            'скрепк': '📎', 'clip': '📎',
            'линейк': '📏', 'ruler': '📏',
        }
        
        updated_count = 0
        for product_id, name, icon in products:
            # Если иконка уже есть и не дефолтная - пропускаем
            if icon and icon != '🍽️':
                continue
                
            name_lower = name.lower()
            new_icon = None
            
            for keyword, emoji in icon_map.items():
                if keyword in name_lower:
                    new_icon = emoji
                    break
            
            if not new_icon:
                new_icon = '🍽️'
            
            if new_icon != icon:
                cur.execute("""
                    UPDATE supplier_products 
                    SET icon = %s 
                    WHERE id = %s
                """, (new_icon, product_id))
                updated_count += 1
                print(f"   ✅ #{product_id}: '{name}' → {new_icon}")
        
        print(f"   ✅ Обновлено {updated_count} товаров")
        
        # ============================================================
        # 4. ПРОВЕРЯЕМ РЕЗУЛЬТАТ
        # ============================================================
        print("\n📋 4. ИТОГОВЫЙ СПИСОК ТОВАРОВ:")
        print("-" * 70)
        
        cur.execute("""
            SELECT id, name, icon, description_ru 
            FROM supplier_products 
            ORDER BY id
        """)
        
        products = cur.fetchall()
        for product_id, name, icon, desc in products:
            icon_display = icon if icon else '🍽️'
            desc_display = desc if desc else '-'
            print(f"   #{product_id}: {icon_display} {name} | {desc_display[:30]}")
        
        conn.commit()
        
        print("\n" + "=" * 70)
        print("✅ ✅ ✅ ВСЕ ИСПРАВЛЕНИЯ УСПЕШНО ПРИМЕНЕНЫ!")
        print("=" * 70)
        print("\n📋 ЧТО БЫЛО СДЕЛАНО:")
        print("   1. ✅ Добавлена колонка icon")
        print("   2. ✅ Добавлена колонка description_ru")
        print("   3. ✅ Обновлены иконки для всех товаров")
        print("   4. ✅ Все товары проверены")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        if conn:
            conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("\n🔌 Соединение закрыто")

if __name__ == "__main__":
    run_fix()