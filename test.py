# add_foods.py
from backend.database import SessionLocal
from backend.models import Food

db = SessionLocal()

# Удаляем старые продукты (опционально)
# db.query(Food).delete()
# db.commit()

foods = [
    # ========== ПИЦЦЫ ==========
    Food(name_ru="Пицца Маргарита", name_kz="Пицца Маргарита", price=1800, image="https://images.unsplash.com/photo-1604382355076-af4b0eb60143?w=400&h=300&fit=crop", discount=40),
    Food(name_ru="Пицца Пепперони", name_kz="Пицца Пепперони", price=2200, image="https://images.unsplash.com/photo-1628840042765-356cda07504e?w=400&h=300&fit=crop", discount=35),
    Food(name_ru="Пицца Гавайская", name_kz="Пицца Гавайская", price=2100, image="https://images.unsplash.com/photo-1595854341625-f33ee10dbf94?w=400&h=300&fit=crop", discount=38),
    Food(name_ru="Пицца Четыре сыра", name_kz="Пицца Төрт ірімшік", price=2300, image="https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&h=300&fit=crop", discount=30),
    Food(name_ru="Пицца Мясная", name_kz="Пицца Етті", price=2500, image="https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=300&fit=crop", discount=35),
    
    # ========== БУРГЕРЫ ==========
    Food(name_ru="Бургер Классический", name_kz="Бургер Классикалық", price=1500, image="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop", discount=40),
    Food(name_ru="Бургер Чизбургер", name_kz="Бургер Чизбургер", price=1700, image="https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=400&h=300&fit=crop", discount=35),
    Food(name_ru="Бургер Двойной", name_kz="Бургер Қос", price=2200, image="https://images.unsplash.com/photo-1553979459-d2229ba7433a?w=400&h=300&fit=crop", discount=40),
    Food(name_ru="Бургер Острый", name_kz="Бургер Ащы", price=2000, image="https://images.unsplash.com/photo-1551782450-a2132b4ba21d?w=400&h=300&fit=crop", discount=35),
    Food(name_ru="Бургер Вегетарианский", name_kz="Бургер Вегетариандық", price=1800, image="https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=400&h=300&fit=crop", discount=30),
    
    # ========== САЛАТЫ ==========
    Food(name_ru="Цезарь с курицей", name_kz="Цезарь тауық етімен", price=1200, image="https://images.unsplash.com/photo-1550304943-4f24f54dd3b9?w=400&h=300&fit=crop", discount=33),
    Food(name_ru="Греческий салат", name_kz="Грек салаты", price=900, image="https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400&h=300&fit=crop", discount=35),
    Food(name_ru="Салат Оливье", name_kz="Оливье салаты", price=800, image="https://images.unsplash.com/photo-1565552645632-d725f8bfc19a?w=400&h=300&fit=crop", discount=30),
    Food(name_ru="Салат с тунцом", name_kz="Тунец қосылған салат", price=1300, image="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop", discount=30),
    
    # ========== СУШИ И РОЛЛЫ ==========
    Food(name_ru="Суши сет (8 шт)", name_kz="Суши сет (8 дана)", price=2250, image="https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400&h=300&fit=crop", discount=25),
    Food(name_ru="Филадельфия ролл", name_kz="Филадельфия ролл", price=2800, image="https://images.unsplash.com/photo-1617196034183-421c4917c92d?w=400&h=300&fit=crop", discount=30),
    Food(name_ru="Калифорния ролл", name_kz="Калифорния ролл", price=2500, image="https://images.unsplash.com/photo-1617196035154-1e7e6e28a0a4?w=400&h=300&fit=crop", discount=28),
    Food(name_ru="Ролл с лососем", name_kz="Лосось ролл", price=2600, image="https://images.unsplash.com/photo-1617196034791-1dfea5f9f1b2?w=400&h=300&fit=crop", discount=25),
    
    # ========== ДЕСЕРТЫ ==========
    Food(name_ru="Чизкейк Нью-Йорк", name_kz="Чизкейк Нью-Йорк", price=1200, image="https://picsum.photos/id/132/400/300", discount=20),
    Food(name_ru="Тирамису", name_kz="Тирамису", price=1300, image="https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400&h=300&fit=crop", discount=23),
    Food(name_ru="Медовик", name_kz="Балды қамыр", price=1000, image="https://images.unsplash.com/photo-1585817918459-3c645c0e17c5?w=400&h=300&fit=crop", discount=25),
    Food(name_ru="Эклеры", name_kz="Эклерлер", price=800, image="https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=400&h=300&fit=crop", discount=20),
    Food(name_ru="Панна котта", name_kz="Панна котта", price=1100, image="https://images.unsplash.com/photo-1488477181946-6428a0292829?w=400&h=300&fit=crop", discount=25),
    
    # ========== НАПИТКИ ==========
    Food(name_ru="Кока-Кола", name_kz="Кока-Кола", price=400, image="https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400&h=300&fit=crop", discount=33),
    Food(name_ru="Спрайт", name_kz="Спрайт", price=400, image="https://images.unsplash.com/photo-1581636625402-29b2a704ef13?w=400&h=300&fit=crop", discount=30),
    Food(name_ru="Фанта", name_kz="Фанта", price=400, image="https://images.unsplash.com/photo-1581006852262-e4307cf6283a?w=400&h=300&fit=crop", discount=30),
    Food(name_ru="Лимонад", name_kz="Лимонад", price=500, image="https://images.unsplash.com/photo-1527960471264-932f39eb36a6?w=400&h=300&fit=crop", discount=28),
    Food(name_ru="Морс", name_kz="Морс", price=450, image="https://images.unsplash.com/photo-1563252870-6bc76ead1a10?w=400&h=300&fit=crop", discount=25),
    Food(name_ru="Чай зеленый", name_kz="Көк шай", price=300, image="https://images.unsplash.com/photo-1627435601361-ec25f5b1d0e5?w=400&h=300&fit=crop", discount=20),
    Food(name_ru="Чай черный", name_kz="Қара шай", price=300, image="https://images.unsplash.com/photo-1596097635121-14b8a4fe30b0?w=400&h=300&fit=crop", discount=20),
    Food(name_ru="Кофе Капучино", name_kz="Капучино кофесі", price=600, image="https://images.unsplash.com/photo-1569576864763-fbd4626cd694?w=400&h=300&fit=crop", discount=25),
    Food(name_ru="Кофе Латте", name_kz="Латте кофесі", price=650, image="https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=400&h=300&fit=crop", discount=25),
    Food(name_ru="Кофе Американо", name_kz="Американо кофесі", price=550, image="https://images.unsplash.com/photo-1559496419-2f7c6c9c8f1c?w=400&h=300&fit=crop", discount=20),
    
    # ========== ДОПОЛНИТЕЛЬНЫЕ БЛЮДА ==========
    Food(name_ru="Картофель фри", name_kz="Қуырылған картоп", price=500, image="https://images.unsplash.com/photo-1585109649139-366815a0d713?w=400&h=300&fit=crop", discount=25),
    Food(name_ru="Куриные крылышки", name_kz="Тауық қанаттары", price=1200, image="https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=400&h=300&fit=crop", discount=30),
    Food(name_ru="Луковые кольца", name_kz="Пияз сақиналары", price=600, image="https://images.unsplash.com/photo-1639024471283-52c5dd6ed8c7?w=400&h=300&fit=crop", discount=25),
    Food(name_ru="Тосты с сыром", name_kz="Ірімшік қосылған тост", price=450, image="https://images.unsplash.com/photo-1528736235302-52922df5c122?w=400&h=300&fit=crop", discount=20),
    
    # ========== АЗИАТСКАЯ КУХНЯ ==========
    Food(name_ru="Вок с лапшой", name_kz="Лапша вок", price=1400, image="https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=300&fit=crop", discount=30),
    Food(name_ru="Рис с овощами", name_kz="Көкөніс қосылған күріш", price=900, image="https://images.unsplash.com/photo-1512058564366-18510be2db19?w=400&h=300&fit=crop", discount=25),
    Food(name_ru="Удон с курицей", name_kz="Тауық еті қосылған удон", price=1600, image="https://images.unsplash.com/photo-1552611052-33e04de081de?w=400&h=300&fit=crop", discount=30),
    
    # ========== КАЗАХСКАЯ КУХНЯ ==========
    Food(name_ru="Бешбармак", name_kz="Бешбармақ", price=2500, image="https://images.unsplash.com/photo-1598276712752-7e61141e5f0c?w=400&h=300&fit=crop", discount=35),
    Food(name_ru="Куырдак", name_kz="Қуырдақ", price=2000, image="https://images.unsplash.com/photo-1574482626633-6b6ea68cfb5d?w=400&h=300&fit=crop", discount=30),
    Food(name_ru="Манты", name_kz="Мәнті", price=1500, image="https://images.unsplash.com/photo-1611162616305-c5afa2d4e6b4?w=400&h=300&fit=crop", discount=25),
    Food(name_ru="Самса", name_kz="Самса", price=500, image="https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop", discount=20),
    Food(name_ru="Баурсаки", name_kz="Бауырсақ", price=400, image="https://images.unsplash.com/photo-1601050690553-763f77fa26cd?w=400&h=300&fit=crop", discount=25),
]

# Очищаем существующие продукты (раскомментируйте если нужно)
# db.query(Food).delete()
# db.commit()

for food in foods:
    db.add(food)

db.commit()
print(f"✅ Добавлено {len(foods)} продуктов!")
db.close()