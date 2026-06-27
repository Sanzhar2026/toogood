# migrate_add_icons.py

import psycopg2
import re

# ✅ ТВОЯ БД НА RAILWAY
DATABASE_URL = "postgresql://postgres:YHceVkBwWMtDTXqSbqQhsGrnIxeWlcwz@thomas.proxy.rlwy.net:27717/railway"

def run_migration():
    conn = None
    cur = None
    try:
        print("🔌 Подключение к БД Railway...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("=" * 60)
        print("📋 ДОБАВЛЕНИЕ ИКОНОК В ТАБЛИЦУ supplier_products")
        print("=" * 60)
        
        # ============================================================
        # 1. ПРОВЕРИТЬ И ДОБАВИТЬ КОЛОНКУ icon
        # ============================================================
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'supplier_products' AND column_name = 'icon'
        """)
        
        if not cur.fetchone():
            print("➕ ДОБАВЛЯЮ КОЛОНКУ icon...")
            cur.execute("ALTER TABLE supplier_products ADD COLUMN icon VARCHAR(50) DEFAULT '🍽️'")
            print("✅ КОЛОНКА icon ДОБАВЛЕНА")
        else:
            print("✅ КОЛОНКА icon УЖЕ СУЩЕСТВУЕТ")
        
        # ============================================================
        # 2. ОБНОВИТЬ СУЩЕСТВУЮЩИЕ ТОВАРЫ
        # ============================================================
        cur.execute("""
            SELECT id, name FROM supplier_products
        """)
        
        products = cur.fetchall()
        print(f"\n📦 ВСЕГО ТОВАРОВ: {len(products)}")
        
        # ============================================================
        # 3. МАППИНГ ИКОНОК ПО НАЗВАНИЮ
        # ============================================================
        icon_map = {
            # ===== ЕДА =====
            'пицц': '🍕', 'pizza': '🍕', 'маргарит': '🍕', 'пепперони': '🍕',
            'бургер': '🍔', 'burger': '🍔', 
            'донер': '🌯', 'шаурм': '🥙', 'кебаб': '🥙',
            'суши': '🍣', 'sushi': '🍣', 'ролл': '🍣', 'roll': '🍣', 'нигири': '🍣', 'сашими': '🍣',
            'салат': '🥗', 'salad': '🥗', 'цезарь': '🥗', 'греческ': '🥗',
            'картошк': '🍟', 'fries': '🍟', 'фри': '🍟',
            'куриц': '🍗', 'chicken': '🍗', 'крилс': '🍗', 'wings': '🍗', 'наггетс': '🍗',
            'стейк': '🥩', 'steak': '🥩', 'говядин': '🥩', 'баранин': '🥩',
            'паста': '🍝', 'pasta': '🍝', 'спагетти': '🍝', 'макарон': '🍝',
            'суп': '🍲', 'soup': '🍲', 'борщ': '🍲', 'том ям': '🍲',
            'десерт': '🍰', 'dessert': '🍰', 'торт': '🍰', 'cake': '🍰', 'пирожн': '🍰', 
            'тирамису': '🍰', 'чизкейк': '🍰',
            'хот-дог': '🌭', 'hot dog': '🌭',
            'сэндвич': '🥪', 'sandwich': '🥪',
            
            'плов': '🥘', 'plov': '🥘',
            'креветк': '🍤', 'shrimp': '🍤',
            'бенто': '🍱', 'bento': '🍱',
         
            'лапш': '🍜', 'noodle': '🍜',
            'пельмен': '🥟', 'dumpling': '🥟',

            
            # ===== МОЛОЧНЫЕ =====
            'сыр': '🧀', 'cheese': '🧀',
            'молоко': '🥛', 'milk': '🥛',
            'морожен': '🍦', 'ice cream': '🍦',
            'яйц': '🥚', 'egg': '🥚',
            'масло': '🧈', 'butter': '🧈',
            'блин': '🥞', 'pancake': '🥞',
            'вафл': '🧇', 'waffle': '🧇',
            'сливк': '🍶', 'cream': '🍶',
            
            # ===== ВЫПЕЧКА =====
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
            
            # ===== НАПИТКИ =====
            'кофе': '☕', 'coffee': '☕', 'капучино': '☕', 'латте': '☕', 'эспрессо': '☕',
            'чай': '🍵', 'tea': '🍵',
            'сок': '🧃', 'juice': '🧃',
            'напит': '🥤', 'drink': '🥤',
            'кола': '🥤', 'coca': '🥤', 'лимонад': '🥤',
            'bubble tea': '🧋',
            'мате': '🧉', 'mate': '🧉',
            'пиво': '🍺', 'beer': '🍺',
            'вино': '🍷', 'wine': '🍷',
            'виски': '🥃', 'whiskey': '🥃',
            'коктейль': '🍸', 'cocktail': '🍸',
            'шампанск': '🍾', 'champagne': '🍾',
            'вода': '💧', 'water': '💧',
            'лёд': '🧊', 'ice': '🧊',
            
            # ===== ФРУКТЫ И ОВОЩИ =====
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
            'лист': '🥬', 'lettuce': '🥬',
            'огурец': '🥒', 'cucumber': '🥒',
            'перец': '🌶️', 'pepper': '🌶️',
            'морков': '🥕', 'carrot': '🥕',
            'чеснок': '🧄', 'garlic': '🧄',
            'лук': '🧅', 'onion': '🧅',
            'картофель': '🥔', 'potato': '🥔',
            'гриб': '🍄', 'mushroom': '🍄',
            'кукуруз': '🌽', 'corn': '🌽',
            
            # ===== РЫБА =====
            'рыб': '🐟', 'fish': '🐟',
            'лосос': '🐟', 'salmon': '🐟',
            'семг': '🐟', 
            'креветк': '🦐', 'shrimp': '🦐',
            'лобстер': '🦞', 'lobster': '🦞',
            'краб': '🦀', 'crab': '🦀',
            'осьминог': '🐙', 'octopus': '🐙',
            'кальмар': '🦑', 'squid': '🦑',
            'ракушк': '🐚', 'shell': '🐚',
            
            # ===== СОУСЫ =====
            'соль': '🧂', 'salt': '🧂',
            'трав': '🌿', 'herb': '🌿',
            'мёд': '🍯', 'honey': '🍯',
            'соус': '🥫', 'sauce': '🥫',
            
            # ===== ХОЗТОВАРЫ =====
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
        print("\n🔄 ОБНОВЛЕНИЕ ИКОНОК:")
        
        for product_id, name in products:
            name_lower = name.lower()
            icon = None
            
            # Ищем совпадение в маппинге
            for keyword, emoji in icon_map.items():
                if keyword in name_lower:
                    icon = emoji
                    break
            
            # Если не найдено - ставим по умолчанию
            if not icon:
                icon = '🍽️'
            
            cur.execute("""
                UPDATE supplier_products 
                SET icon = %s 
                WHERE id = %s
            """, (icon, product_id))
            
            updated_count += 1
            print(f"  ✅ #{product_id}: '{name}' → {icon}")
        
        conn.commit()
        print(f"\n✅ ОБНОВЛЕНО {updated_count} ТОВАРОВ")
        
        # ============================================================
        # 4. ПРОВЕРИТЬ РЕЗУЛЬТАТ
        # ============================================================
        cur.execute("""
            SELECT id, name, icon FROM supplier_products ORDER BY id
        """)
        
        products = cur.fetchall()
        print("\n" + "=" * 60)
        print("📋 ИТОГОВЫЙ СПИСОК ТОВАРОВ С ИКОНКАМИ:")
        print("=" * 60)
        
        for product_id, name, icon in products:
            print(f"  #{product_id}: {icon} {name}")
        
        print("\n" + "=" * 60)
        print("✅ ✅ ✅ МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
        print("=" * 60)
        
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
    run_migration()