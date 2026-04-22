from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, get_db
from backend import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Categories
categories = [
    {"id": "all", "name_kz": "Барлығы", "name_ru": "Все", "emoji": "🍽️"},
    {"id": "main", "name_kz": "Негізгі тағам", "name_ru": "Основные блюда", "emoji": "🍕"},
    {"id": "salads", "name_kz": "Салаттар", "name_ru": "Салаты", "emoji": "🥗"},
    {"id": "drinks", "name_kz": "Сусындар", "name_ru": "Напитки", "emoji": "🥤"},
    {"id": "desserts", "name_kz": "Десерттер", "name_ru": "Десерты", "emoji": "🍰"},
]

# Helper to add mock data if database is empty
def add_mock_data(db: Session):
    if db.query(models.Food).count() == 0:
        mock_foods = [
            models.Food(name_ru="Пицца Маргарита", name_kz="Пицца Маргарита", price=1800, image="https://images.unsplash.com/photo-1604382355076-af4b0eb60143?w=400&h=300&fit=crop", discount=40),
            models.Food(name_ru="Бургер", name_kz="Бургер", price=1500, image="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop", discount=40),
            models.Food(name_ru="Суши сет", name_kz="Суши сет", price=2250, image="https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400&h=300&fit=crop", discount=25),
            models.Food(name_ru="Грек салаты", name_kz="Грек салаты", price=975, image="https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400&h=300&fit=crop", discount=35),
            models.Food(name_ru="Цезарь", name_kz="Цезарь", price=1200, image="https://images.unsplash.com/photo-1550304943-4f24f54dd3b9?w=400&h=300&fit=crop", discount=33),
            models.Food(name_ru="Чизкейк", name_kz="Чизкейк", price=1200, image="https://picsum.photos/id/132/400/300", discount=20),
            models.Food(name_ru="Тирамису", name_kz="Тирамису", price=1300, image="https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400&h=300&fit=crop", discount=23),
            models.Food(name_ru="Кола", name_kz="Кола", price=400, image="https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400&h=300&fit=crop", discount=33),
            models.Food(name_ru="Лимонад", name_kz="Лимонад", price=500, image="https://images.unsplash.com/photo-1527960471264-932f39eb36a6?w=400&h=300&fit=crop", discount=28),
        ]
        for food in mock_foods:
            db.add(food)
        db.commit()

# Home page
@app.get("/")
async def home(request: Request, lang: str = "kz", category: str = "all", db: Session = Depends(get_db)):
    add_mock_data(db)
    
    foods = db.query(models.Food).all()
    
    foods_list = []
    for food in foods:
        foods_list.append({
            "id": food.id,
            "name_kz": food.name_kz,
            "name_ru": food.name_ru,
            "price": food.price,
            "old_price": round(food.price / (1 - food.discount/100)) if food.discount > 0 else None,
            "discount": food.discount,
            "image_url": food.image,
            "restaurant": "Sarqyn Food",
            "rating": 4.5,
            "distance": 1.0,
            "time": 20,
        })
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "foods": foods_list,
        "categories": categories,
        "active_category": category,
        "lang": lang
    })

# Create order
@app.post("/order/{food_id}")
async def create_order(
    food_id: int, 
    lat: float = 0, 
    lon: float = 0, 
    db: Session = Depends(get_db)
):
    food = db.query(models.Food).filter(models.Food.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    
    order = models.Order(
        user_id=1,
        food_id=food_id,
        lat=lat if lat != 0 else None,
        lon=lon if lon != 0 else None
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return {"message": "Order created", "order_id": order.id}


# API endpoint for orders (JSON)
@app.post("/api/orders")
async def create_order_api(order_data: dict, db: Session = Depends(get_db)):
    try:
        order = models.Order(
            user_id=order_data.get("user_id", 1),
            food_id=order_data["food_id"],
            lat=order_data.get("lat"),
            lon=order_data.get("lon"),
            address=order_data.get("address")  # ADD THIS LINE
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return {"success": True, "order_id": order.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API endpoint to get foods
@app.get("/api/foods")
async def get_foods_api(db: Session = Depends(get_db)):
    foods = db.query(models.Food).all()
    return foods

# Admin panel
@app.get("/admin")
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    foods = db.query(models.Food).all()
    orders = db.query(models.Order).all()
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "foods": foods,
        "orders": orders
    })

# Add food from admin
@app.post("/admin/add-food")
async def add_food(
    name_ru: str = Form(...),
    name_kz: str = Form(...),
    price: float = Form(...),
    image: str = Form(...),
    discount: int = Form(0),
    db: Session = Depends(get_db)
):
    new_food = models.Food(
        name_ru=name_ru,
        name_kz=name_kz,
        price=price,
        image=image,
        discount=discount
    )
    db.add(new_food)
    db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)

# Delete food
@app.get("/admin/delete-food/{food_id}")
async def delete_food(food_id: int, db: Session = Depends(get_db)):
    food = db.query(models.Food).filter(models.Food.id == food_id).first()
    if food:
        db.delete(food)
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)
import os
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)