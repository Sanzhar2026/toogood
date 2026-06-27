from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from backend.database import SessionLocal, engine, get_db
from backend import models
from backend.models import Food, User, Supplier, SurpriseBag, Order, OrderTracking
from datetime import datetime, timedelta
import secrets
import os
import math
import hashlib
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from backend.schemas import (
    OrderCreate, PhoneVerificationRequest, PhoneRegisterRequest
)
from datetime import datetime, timedelta
from backend.models import (
    CartItem,Food, User, Supplier, SurpriseBag, SurpriseBagItem,SupplierReview,
    Order, OrderTracking, CourierProfile, AssignedOrder ,TemporaryReservation,SurpriseBagReview, Admin
)
from backend.websocket_manager import ConnectionManager
from backend.routes.users import router as users_router

from typing import Dict

# ============ TWILIO IMPORTS ============
try:
    from backend.twilio_service import send_verification_code, verify_code
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("⚠️ Twilio service not available. SMS verification will use demo mode.")





models.Base.metadata.create_all(bind=engine)

# ============ FASTAPI APP ============
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="backend/static"), name="static")
# ============ CACHE FOR DELIVERIES ============
delivery_cache = {}
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://toogood-production.up.railway.app","https://sarqyt-go-production.up.railway.app","https://*-production.up.railway.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ CATEGORIES ============
categories = [
    {"id": "all", "name_kz": "Барлығы", "name_ru": "Все", "emoji": "🍽️"},
    {"id": "main", "name_kz": "Негізгі тағам", "name_ru": "Основные блюда", "emoji": "🍕"},
    {"id": "salads", "name_kz": "Салаттар", "name_ru": "Салаты", "emoji": "🥗"},
    {"id": "drinks", "name_kz": "Сусындар", "name_ru": "Напитки", "emoji": "🥤"},
    {"id": "desserts", "name_kz": "Десерттер", "name_ru": "Десерты", "emoji": "🍰"},
]

import httpx
import json
import math
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjYyMDU3ZGE4OTkxODQ2M2JhNmVlZDgzM2QzMDE2OTYwIiwiaCI6Im11cm11cjY0In0="
# backend/main.py - добавьте эндпоинт для маршрута

# backend/main.py - обновите эндпоинт
from jose import jwt
import os
# backend/main.py - добавьте в начало файла (после импортов)

from jose import jwt
from datetime import datetime, timedelta
import os

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "sarqyn-super-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 дней

password_reset_requests = {}
# backend/main.py - в самое начало файла
# backend/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid
from typing import Optional
from jose import jwt

from backend.database import get_db
from backend.models import User

# 👇 ВАЖНО: импортируй SECRET_KEY и ALGORITHM из config или main
# Вариант 1: если есть config.py
try:
    from backend.config import SECRET_KEY, ALGORITHM
except ImportError:
    # Вариант 2: если SECRET_KEY в main.py
    from backend.main import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/users", tags=["users"])
app.include_router(users_router)
# Директория для хранения аватаров
BASE_DIR = Path(__file__).resolve().parent.parent
AVATAR_DIR = BASE_DIR / "uploads" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

print(f"📁 AVATAR_DIR: {AVATAR_DIR.absolute()}")
print(f"🔑 SECRET_KEY loaded: {SECRET_KEY[:10]}...")  # Проверка что ключ загружен

# backend/routers/users.py - добавь этот эндпоинт в конец файла


def get_city_from_coords(lat: float, lon: float) -> str:
    """Определяет город по координатам"""
    # Основные города Казахстана
    CITIES = {
        'Алматы': {'lat': 43.238, 'lon': 76.945, 'radius': 30},
        'Астана': {'lat': 51.169, 'lon': 71.449, 'radius': 30},
        'Шымкент': {'lat': 42.341, 'lon': 69.590, 'radius': 30},
        'Ақтөбе': {'lat': 50.283, 'lon': 57.167, 'radius': 30},
        'Қарағанды': {'lat': 49.801, 'lon': 73.102, 'radius': 30},
        'Атырау': {'lat': 47.115, 'lon': 51.917, 'radius': 30},
        'Өскемен': {'lat': 49.950, 'lon': 82.618, 'radius': 30},
        'Павлодар': {'lat': 52.287, 'lon': 76.973, 'radius': 30},
        'Тараз': {'lat': 42.899, 'lon': 71.365, 'radius': 30},
        'Қызылорда': {'lat': 44.848, 'lon': 65.482, 'radius': 30},
    }
    
    closest_city = None
    min_distance = float('inf')
    
    for city, coords in CITIES.items():
        distance = haversine_distance(lat, lon, coords['lat'], coords['lon'])
        if distance < coords['radius'] and distance < min_distance:
            min_distance = distance
            closest_city = city
    
    return closest_city






# backend/main.py - ДОБАВЬ В НАЧАЛО ФАЙЛА

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

async def get_current_supplier(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Получить текущего поставщика из токена"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        if role != "supplier":
            raise HTTPException(status_code=403, detail="Not a supplier")
        
        supplier_id = payload.get("supplier_id")
        if not supplier_id:
            user_id = int(payload.get("sub"))
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id FROM suppliers WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            if not result:
                raise HTTPException(status_code=404, detail="Supplier not found")
            supplier_id = result[0]
        
        # Проверяем что поставщик существует
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return supplier
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/avatar-file/{user_id}")
async def get_avatar_file(
    user_id: int,
):
    """Получить файл аватара напрямую (минуя статику)"""
    
    from pathlib import Path
    
    # Директория с аватарами
    AVATAR_DIR = Path("uploads/avatars")
    
    print(f"🔍 Looking for avatar of user {user_id}")
    print(f"📁 Path: {AVATAR_DIR.absolute()}")
    
    # Ищем файл аватара
    avatar_files = list(AVATAR_DIR.glob(f"avatar_{user_id}_*.webp"))
    
    print(f"📄 Found files: {[f.name for f in avatar_files]}")
    
    if avatar_files:
        file_path = avatar_files[0]
        print(f"✅ Serving: {file_path.name} ({file_path.stat().st_size} bytes)")
        return FileResponse(
            file_path, 
            media_type="image/webp",
            headers={
                "Cache-Control": "public, max-age=86400",
                "Content-Type": "image/webp"
            }
        )
    
    print(f"❌ No avatar for user {user_id}")
    
    # Если нет аватара, возвращаем 204 No Content
    raise HTTPException(status_code=204, detail="No avatar")

# backend/main.py - ДОБАВИТЬ В НАЧАЛО ФАЙЛА

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

async def get_supplier_id_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """
    Получить supplier_id из JWT токена.
    Используется во всех эндпоинтах для проверки авторизации.
    
    Returns:
        int: supplier_id
    
    Raises:
        HTTPException: 401 если токен невалидный
        HTTPException: 403 если роль не supplier
        HTTPException: 404 если поставщик не найден
    """
    token = credentials.credentials
    
    try:
        # Декодируем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Проверяем роль
        role = payload.get("role")
        if role != "supplier":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a supplier"
            )
        
        # Получаем supplier_id из токена
        supplier_id = payload.get("supplier_id")
        
        # Если supplier_id нет в токене - ищем по user_id
        if not supplier_id:
            user_id = int(payload.get("sub"))
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id FROM suppliers WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Supplier not found"
                )
            supplier_id = result[0]
        
        # Проверяем что поставщик существует и активен
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, is_active FROM suppliers 
            WHERE id = %s
        """, (supplier_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found"
            )
        
        if not result[1]:  # is_active = False
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supplier account is not active"
            )
        
        return supplier_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_supplier_id_from_token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    




def get_current_user_from_token(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Получить текущего пользователя из JWT токена"""
    
    auth_header = request.headers.get("Authorization")
    print(f"🔑 Auth header: {auth_header[:50] if auth_header else 'None'}...")  # Отладка
    
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = auth_header.split(" ")[1]
    print(f"🔑 Token: {token[:50]}...")  # Отладка
    
    try:
        # 👇 Используем импортированные SECRET_KEY и ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        print(f"✅ User ID from token: {user_id}")  # Отладка
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        print(f"✅ User found: {user.id} - {user.phone}")  # Отладка
        return user
        
    except jwt.ExpiredSignatureError:
        print(f"❌ Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        print(f"❌ Token error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

 # 👈 ВАЖНО!

# Монтируем статику для аватаров
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


import psycopg2
from psycopg2.extras import RealDictCursor
def get_db_connection():
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://toogood_db_a3k0_user:2tWztMrzy1VCriWHefthkLBK1EOeeYnG@dpg-d8eo51rbc2fs73coebs0-a.frankfurt-postgres.render.com/toogood_db_a3k0?sslmode=require"
    )
    return psycopg2.connect(DATABASE_URL)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
@app.post("/api/delivery/route/{order_id}")
async def get_delivery_route(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Получить маршрут доставки от текущего положения курьера до ресторана и клиента"""
    
    data = await request.json()
    start_lat = data.get("start_lat")
    start_lon = data.get("start_lon")
    end_lat = data.get("end_lat")
    end_lon = data.get("end_lon")
    
    # ✅ НЕТ АЛМАТЫ! Используем ТОЛЬКО переданные координаты
    if not start_lat or not start_lon:
        raise HTTPException(status_code=400, detail="Start location required")
    
    if not end_lat or not end_lon:
        raise HTTPException(status_code=400, detail="End location required")
    
    ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjYyMDU3ZGE4OTkxODQ2M2JhNmVlZDgzM2QzMDE2OTYwIiwiaCI6Im11cm11cjY0In0="
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openrouteservice.org/v2/directions/driving-car",
                headers={
                    "Authorization": ORS_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "coordinates": [[start_lon, start_lat], [end_lon, end_lat]]
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                route = data['routes'][0]
                
                import polyline
                decoded_points = polyline.decode(route['geometry'])
                
                waypoints = []
                for point in decoded_points:
                    waypoints.append({"lat": point[0], "lon": point[1]})
                
                distance_km = route['summary']['distance'] / 1000
                duration_min = route['summary']['duration'] / 60
                
                return {
                    "success": True,
                    "waypoints": waypoints,
                    "distance_km": round(distance_km, 2),
                    "duration_min": round(duration_min, 2),
                    "start_lat": start_lat,
                    "start_lon": start_lon,
                    "end_lat": end_lat,
                    "end_lon": end_lon
                }
            else:
                return get_straight_line_route(start_lat, start_lon, end_lat, end_lon)
                
        except Exception as e:
            print(f"ORS error: {e}")
            return get_straight_line_route(start_lat, start_lon, end_lat, end_lon)
def get_user_id_from_request(request: Request) -> int | None:
    """Универсальное получение user_id из запроса (Bearer token или cookie)"""
    
    # 1. Bearer token (для мобильного приложения)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from jose import jwt
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                print(f"🔑 user_id из Bearer токена: {user_id}")
                return int(user_id)
        except Exception as e:
            print(f"❌ Ошибка Bearer токена: {e}")
    
    # 2. Cookie (для веб-версии)
    user_id = request.cookies.get("user_id")
    if user_id:
        print(f"🍪 user_id из cookie: {user_id}")
        return int(user_id)
    
    return None




def create_admin_if_not_exists(db: Session):
    """Создает админа при первом запуске"""
    admin = db.query(Admin).first()
    if not admin:
        MY_LOGIN = "ACCOUNTA@#$26"
        MY_PASSWORD = "CEVONICQW%&%y*"
        
        new_admin = Admin(
            username=MY_LOGIN,
            password_hash=hash_password(MY_PASSWORD)
        )
        db.add(new_admin)
        db.commit()
        print(f"✅ Админ создан: {MY_LOGIN}")
        return True
    return False






# backend/main.py
@app.post("/api/courier/pickup-order/{order_id}")
async def courier_pickup_order(order_id: int, request: Request):
    """Курьер забрал заказ из ресторана - БЕЗ delivery_status"""
    
    # Проверка токена
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Получаем курьера
        cur.execute("""
            SELECT first_name, last_name
            FROM courier_profiles 
            WHERE user_id = %s
        """, (int(user_id),))
        
        courier = cur.fetchone()
        if not courier:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Courier not found")
        
        courier_name = f"{courier[0]} {courier[1]}"
        
        # 2. Проверяем заказ
        cur.execute("""
            SELECT id, status, assigned_courier_id, user_id, order_number
            FROM orders 
            WHERE id = %s
        """, (order_id,))
        
        order = cur.fetchone()
        if not order:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Order not found")
        
        order_status = order[1]
        assigned_courier = order[2]
        customer_user_id = order[3]
        order_number = order[4]
        
        # 3. Проверки
        if assigned_courier != int(user_id):
            cur.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Order not assigned to you")
        
        if order_status != 'ready_for_pickup':
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"Заказ не готов к выдаче. Статус: {order_status}"}
            )
        
        # 4. Обновляем заказ - БЕЗ delivery_status!
        cur.execute("""
            UPDATE orders 
            SET status = 'picked_up',
                delivery_started_at = NOW(),
                delivery_deadline = NOW() + INTERVAL '30 minutes'
            WHERE id = %s
        """, (order_id,))
        
        # 5. Обновляем курьера
        cur.execute("""
            UPDATE courier_profiles 
            SET current_order_status = 'picked_up'
            WHERE user_id = %s
        """, (int(user_id),))
        
        # 6. Добавляем в трекинг - БЕЗ delivery_status!
        cur.execute("""
            INSERT INTO order_tracking 
            (order_id, status, message, created_at)
            VALUES (%s, 'picked_up', 'Курьер забрал заказ из ресторана', NOW())
        """, (order_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Курьер {courier_name} забрал заказ #{order_id}")
        
        # 7. Отправляем уведомление клиенту
        try:
            if customer_user_id:
                await manager.broadcast({
                    "type": "order_picked_up",
                    "data": {
                        "order_id": order_id,
                        "order_number": order_number,
                        "courier_name": courier_name,
                        "status": "picked_up",
                        "message": f"📦 Курьер {courier_name} забрал ваш заказ и едет к вам!",
                        "delivery_deadline": (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }, channel=f"user_{customer_user_id}")
                print(f"📢 Уведомление отправлено клиенту {customer_user_id}")
        except Exception as e:
            print(f"⚠️ Не удалось отправить уведомление: {e}")
        
        return {
            "success": True,
            "message": "Заказ забран из ресторана! Едем к клиенту.",
            "order_id": order_id,
            "delivery_deadline": (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        }
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(f"❌ Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))

import traceback
# backend/main.py



@app.get("/avatar/{user_id}")
async def get_avatar(user_id: int):
    """Получить аватар пользователя напрямую"""
    from pathlib import Path
    
    avatar_dir = Path("uploads/avatars")
    avatar_files = list(avatar_dir.glob(f"avatar_{user_id}_*.webp"))
    
    if avatar_files:
        return FileResponse(avatar_files[0], media_type="image/webp")
    
    raise HTTPException(status_code=404, detail="Avatar not found")

# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/courier/pickup-order/{order_id}")
async def courier_pickup_order(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Курьер забрал заказ из ресторана (едет к клиенту)"""
    
    # Проверка токена
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if payload.get("role") != "courier":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Not a courier"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    
    # Находим курьера
    courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
    if not courier:
        return JSONResponse(
            status_code=404,
            content={"success": False, "detail": "Courier not found"}
        )
    
    # Находим заказ
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return JSONResponse(
            status_code=404,
            content={"success": False, "detail": "Order not found"}
        )
    
    # Проверяем что заказ назначен этому курьеру
    if order.assigned_courier_id != courier.user_id:
        return JSONResponse(
            status_code=403,
            content={"success": False, "detail": "Order not assigned to you"}
        )
    
    # ✅ ИСПРАВЛЕНО: status = 'ready_for_pickup' (строка, БЕЗ ENUM)
    if order.status != "ready_for_pickup":
        return JSONResponse(
            status_code=400,
            content={"success": False, "detail": f"Order not ready for pickup. Current status: {order.status}"}
        )
    
    # ✅ ИСПРАВЛЕНО: status = 'picked_up' (строка, БЕЗ ENUM)
    order.status = "picked_up"
    
    # Устанавливаем дедлайн с момента забора
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    order.delivery_started_at = now
    order.delivery_deadline = now + timedelta(minutes=30)
    
    db.commit()
    
    print(f"✅ Курьер {courier.first_name} забрал заказ #{order_id} из ресторана")
    print(f"⏰ Дедлайн доставки клиенту: {order.delivery_deadline}")
    
    return {
        "success": True,
        "message": "Заказ забран из ресторана! Едем к клиенту.",
        "delivery_deadline": order.delivery_deadline.isoformat()
    }

def get_straight_line_route(start_lat, start_lon, end_lat, end_lon):
    """Прямая линия если ORS не работает"""
    waypoints = []
    for i in range(101):
        t = i / 100
        waypoints.append({
            "lat": start_lat + (end_lat - start_lat) * t,
            "lon": start_lon + (end_lon - start_lon) * t
        })
    
    from math import radians, sin, cos, sqrt, atan2
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    
    distance_km = haversine(start_lat, start_lon, end_lat, end_lon)
    duration_min = (distance_km / 40) * 60
    
    return {
        "success": True,
        "waypoints": waypoints,
        "distance_km": round(distance_km, 2),
        "duration_min": round(duration_min, 2),
        "start_lat": start_lat,
        "start_lon": start_lon,
        "end_lat": end_lat,
        "end_lon": end_lon
    }




# WEBSOCKET

# Добавь это в начало файла (рядом с другими импортами)
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import json








courier_sessions = {}















# backend/main.py - добавьте эти эндпоинты

# ============ АДМИН ЭНДПОИНТЫ ============
async def get_current_admin_from_token(request: Request, db: Session = Depends(get_db)):
    """Получить текущего админа из Bearer токена"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        
        # Проверяем что это админ
        if role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        # В токене хранится admin.id, а не user_id
        admin_id = payload.get("sub")
        
        # Ищем админа по id (не по user_id!)
        admin = db.query(Admin).filter(Admin.id == int(admin_id)).first()
        
        if not admin:
            raise HTTPException(status_code=401, detail="Admin not found")
        
        return admin
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
# backend/main.py - ДОБАВЬТЕ ЭТОТ ЭНДПОИНТ



    # backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/admin/cancel-order/{order_id}")
async def admin_cancel_order(
    order_id: int, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """Админ отменяет заказ и возвращает деньги"""
    
    # ✅ ТОЛЬКО Bearer токен, НИКАКИХ КУК!
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        
        # Проверяем что это админ
        if role != "admin":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Admin only"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        data = await request.json()
        reason = data.get("reason", "Отменено администратором")
    except:
        reason = "Отменено администратором"
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return JSONResponse(
            status_code=404,
            content={"success": False, "detail": "Order not found"}
        )
    
    print(f"🔍 Отмена заказа #{order_id}, назначенный курьер: {order.assigned_courier_id}")
    
    # ✅ ГАРАНТИРОВАННАЯ ОЧИСТКА КУРЬЕРА
    if order.assigned_courier_id:
        courier = db.query(CourierProfile).filter(CourierProfile.user_id == order.assigned_courier_id).first()
        
        if courier:
            old_order_id = courier.current_order_id
            courier.current_order_id = None
            courier.current_order_status = None
            courier.is_available = True
            courier.is_online = True
            print(f"✅ Курьер {courier.first_name} освобожден (был заказ #{old_order_id})")
        else:
            print(f"⚠️ Курьер с user_id={order.assigned_courier_id} не найден в профилях")
        
        # Принудительная очистка
        db.query(CourierProfile).filter(
            CourierProfile.user_id == order.assigned_courier_id
        ).update({
            "current_order_id": None,
            "current_order_status": None,
            "is_available": True,
            "is_online": True
        })
    
    from datetime import datetime
    
    # ✅ ИСПРАВЛЕНО: status = 'cancelled' (строка, БЕЗ ENUM)
    order.status = "cancelled"
    order.payment_status = "refunded"
    order.refund_status = "completed"
    order.refund_processed_at = datetime.utcnow()
    order.refund_amount = order.amount_paid
    order.refund_reason = reason
    order.cancelled_at = datetime.utcnow()
    
    # Возвращаем количество сюрприза
    bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
    if bag:
        bag.available_quantity += 1
        if bag.available_quantity > 0:
            bag.is_active = True
        print(f"📦 Восстановлен товар '{bag.name}', теперь {bag.available_quantity} шт.")
    
    db.commit()
    
    # Отправляем уведомления
    if order.assigned_courier_id:
        try:
            await manager.broadcast({
                "type": "order_cancelled",
                "data": {
                    "order_id": order_id,
                    "order_number": order.order_number,
                    "reason": reason,
                    "cancelled_by": "admin",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }, channel=f"courier_{order.assigned_courier_id}")
        except Exception as e:
            print(f"❌ Ошибка отправки уведомления курьеру: {e}")
    
    try:
        await manager.broadcast({
            "type": "order_cancelled",
            "data": {
                "order_id": order_id,
                "order_number": order.order_number,
                "reason": reason,
                "refund_amount": order.amount_paid,
                "timestamp": datetime.utcnow().isoformat()
            }
        }, channel=f"order_{order_id}")
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления клиенту: {e}")
    
    return {
        "success": True,
        "message": f"Заказ #{order.order_number} отменен, деньги возвращены",
        "order_id": order_id,
        "order_number": order.order_number,
        "cancelled_at": order.cancelled_at.isoformat()
    }
@app.get("/api/admin/orders")
async def get_admin_orders(
    request: Request
):
    """Получить все заказы - ЧИСТЫЙ SQL (без SQLAlchemy)"""
    
    try:
        # Подключаемся к БД через psycopg2
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # ✅ ЧИСТЫЙ SQL - никакого SQLAlchemy!
        cur.execute("""
            SELECT 
                o.id,
                o.order_number,
                o.status::text as status,
                o.amount_paid,
                o.payment_status,
                o.created_at,
                u.full_name as customer_name,
                u.phone as customer_phone,
                sb.name as bag_name
            FROM orders o
            LEFT JOIN users u ON u.id = o.user_id
            LEFT JOIN surprise_bags sb ON sb.id = o.surprise_bag_id
            ORDER BY o.created_at DESC
        """)
        
        orders = cur.fetchall()
        cur.close()
        conn.close()
        
        # Форматируем результат
        result = []
        for order in orders:
            result.append({
                "id": order['id'],
                "order_number": order['order_number'],
                "customer_name": order['customer_name'] or order['customer_phone'] or "Неизвестно",
                "customer_phone": order['customer_phone'] or "Неизвестно",
                "bag_name": order['bag_name'] or "Сюрприз",
                "amount": float(order['amount_paid']) if order['amount_paid'] else 0,
                "payment_status": order['payment_status'] or "pending",
                "status": order['status'] or "pending",  # ✅ УЖЕ СТРОКА!
                "created_at": order['created_at'].isoformat() if order['created_at'] else None
            })
        
        return {"orders": result}
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "orders": []}
        )

        
@app.get("/api/admin/couriers")
async def get_admin_couriers(request: Request):
    """Получить подтвержденных курьеров - чистый SQL"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                cp.id,
                cp.first_name,
                cp.last_name,
                cp.phone,
                cp.courier_type,
                cp.car_model,
                cp.car_number,
                cp.is_online,
                cp.total_deliveries,
                cp.rating
            FROM courier_profiles cp
            WHERE cp.is_verified = true
            ORDER BY cp.created_at DESC
        """)
        
        couriers = cur.fetchall()
        cur.close()
        conn.close()
        
        return {"couriers": couriers}
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})




        
@app.get("/api/admin/pending-couriers")
async def get_admin_pending_couriers(request: Request):
    """Получить неподтвержденных курьеров - чистый SQL"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                cp.id,
                cp.user_id,
                cp.first_name,
                cp.last_name,
                cp.phone,
                cp.courier_type,
                cp.car_model,
                cp.car_number,
                cp.created_at
            FROM courier_profiles cp
            WHERE cp.is_verified = false
            ORDER BY cp.created_at DESC
        """)
        
        couriers = cur.fetchall()
        cur.close()
        conn.close()
        
        return {"couriers": couriers}
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# backend/main.py - ИСПРАВЛЕННЫЙ эндпоинт

@app.post("/api/admin/verify-courier/{courier_id}")
async def admin_verify_courier(
    courier_id: int, 
    request: Request,

    db: Session = Depends(get_db)
):
    """Админ подтверждает курьера"""
    
    # ✅ ТОЛЬКО Bearer токен (НЕ cookies!)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        
        if role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    # Находим курьера
    courier = db.query(CourierProfile).filter(CourierProfile.id == courier_id).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    # Подтверждаем
    courier.is_verified = True
    courier.verified_at = datetime.utcnow()
    
    # Активируем пользователя
    user = db.query(User).filter(User.id == courier.user_id).first()
    if user:
        user.is_active = True
    
    db.commit()
    
    print(f"✅ Курьер {courier.first_name} {courier.last_name} подтвержден")
    
    return {"success": True, "message": "Курьер подтвержден"}

@app.post("/api/admin/reject-courier/{courier_id}")
async def admin_reject_courier(
    courier_id: int, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """Админ отклоняет заявку курьера"""
    
    # ✅ ТОЛЬКО Bearer токен
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        
        if role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    # Находим курьера
    courier = db.query(CourierProfile).filter(CourierProfile.id == courier_id).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    # Удаляем профиль курьера и пользователя
    user = db.query(User).filter(User.id == courier.user_id).first()
    if user:
        db.delete(user)
    db.delete(courier)
    db.commit()
    
    print(f"❌ Заявка курьера #{courier_id} отклонена")
    
    return {"success": True, "message": "Заявка отклонена"}


@app.get("/api/admin/reservations")
async def get_admin_reservations(request: Request):
    """Получить активные резервации - чистый SQL"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                tr.id,
                tr.user_id,
                tr.bag_id,
                tr.quantity,
                tr.reserved_at,
                tr.expires_at,
                u.full_name as user_name,
                u.phone as user_phone,
                sb.name as bag_name,
                s.business_name as supplier_name,
                sb.discounted_price
            FROM temporary_reservations tr
            LEFT JOIN users u ON u.id = tr.user_id
            LEFT JOIN surprise_bags sb ON sb.id = tr.bag_id
            LEFT JOIN suppliers s ON s.id = sb.supplier_id
            WHERE tr.is_paid = false 
              AND tr.expires_at > NOW()
            ORDER BY tr.expires_at ASC
        """)
        
        reservations = cur.fetchall()
        cur.close()
        conn.close()
        
        # Форматируем с расчетом оставшегося времени
        result = []
        for res in reservations:
            time_left = int((res['expires_at'] - datetime.utcnow()).total_seconds() / 60)
            result.append({
                "id": res['id'],
                "user_name": res['user_name'] or res['user_phone'] or f"User {res['user_id']}",
                "user_phone": res['user_phone'] or "Не указан",
                "bag_name": res['bag_name'] or "Товар",
                "supplier_name": res['supplier_name'] or "Ресторан",
                "quantity": res['quantity'],
                "total_amount": float(res['discounted_price'] or 0) * res['quantity'],
                "reserved_at": res['reserved_at'].isoformat() if res['reserved_at'] else None,
                "expires_at": res['expires_at'].isoformat() if res['expires_at'] else None,
                "time_left_minutes": time_left
            })
        
        return {"reservations": result}
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# backend/main.py - добавьте WebSocket для курьеров

# ============ АДМИН ЭНДПОИНТЫ ДЛЯ УПРАВЛЕНИЯ ЗАКАЗАМИ ============
# backend/main.py - ИСПРАВЛЕННЫЙ эндпоинт
@app.put("/api/admin/update-order-status/{order_id}")
async def admin_update_order_status(
    order_id: int,
    request: Request
):
    """Админ обновляет статус заказа - БЕЗ delivery_status"""
    
    # Проверка токена
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    data = await request.json()
    field = data.get("field")
    value = data.get("value")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем заказ
        cur.execute("SELECT id, status FROM orders WHERE id = %s", (order_id,))
        order = cur.fetchone()
        if not order:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Order not found")
        
        old_status = order[1] if len(order) > 1 else "unknown"
        
        if field == "payment_status":
            cur.execute("""
                UPDATE orders 
                SET payment_status = %s
                WHERE id = %s
            """, (value, order_id))
            
            if value == "paid":
                cur.execute("""
                    UPDATE orders 
                    SET status = 'confirmed', 
                        paid_at = NOW(),
                        confirmed_at = NOW()
                    WHERE id = %s
                """, (order_id,))
                
                # Добавляем в трекинг - БЕЗ delivery_status!
                cur.execute("""
                    INSERT INTO order_tracking 
                    (order_id, status, message, created_at)
                    VALUES (%s, 'confirmed', 'Заказ подтвержден администратором после оплаты', NOW())
                """, (order_id,))
                
                # Отправляем уведомление курьерам
                try:
                    await manager.broadcast({
                        "type": "new_order",
                        "data": {
                            "order_id": order_id,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }, channel="couriers")
                except Exception as e:
                    print(f"⚠️ Не удалось отправить уведомление: {e}")
                
        elif field == "order_status":
            new_status = value.lower()
            cur.execute("""
                UPDATE orders 
                SET status = %s
                WHERE id = %s
            """, (new_status, order_id))
            
            # Добавляем в трекинг - БЕЗ delivery_status!
            cur.execute("""
                INSERT INTO order_tracking 
                (order_id, status, message, created_at)
                VALUES (%s, %s, 'Статус изменен администратором', NOW())
            """, (order_id, new_status))
            
            # Уведомление клиенту
            try:
                cur.execute("SELECT user_id FROM orders WHERE id = %s", (order_id,))
                user = cur.fetchone()
                if user:
                    await manager.broadcast({
                        "type": "order_status_updated",
                        "data": {
                            "order_id": order_id,
                            "old_status": old_status,
                            "new_status": new_status,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }, channel=f"user_{user[0]}")
            except Exception as e:
                print(f"⚠️ Не удалось отправить уведомление: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Статус заказа #{order_id} изменен",
            "old_status": old_status,
            "new_status": value
        }
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(f"❌ Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# Вспомогательная функция для отправки уведомлений пользователю
async def notify_user(user_id: int, message: dict):
    """Отправить уведомление конкретному пользователю"""
    if user_id in manager.user_connections:
        try:
            await manager.user_connections[user_id].send_json(message)
            print(f"📨 Уведомление отправлено пользователю {user_id}")
        except Exception as e:
            print(f"❌ Ошибка отправки пользователю {user_id}: {e}")

app.post("/api/admin/bulk-update-status")
async def admin_bulk_update_status(
    request: Request,
    db: Session = Depends(get_db)
):
    """Массовое обновление статусов заказов"""
    
    # Проверка админа
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Admin only"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    
    try:
        data = await request.json()
        order_ids = data.get("order_ids", [])
        new_status = data.get("status")
        
        if not order_ids:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "No order IDs provided"}
            )
        
        if not new_status:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "No status provided"}
            )
        
        # ✅ ИСПРАВЛЕНО: проверяем что статус валидный (строка)
        valid_statuses = [
            "pending", "confirmed", "preparing", "ready_for_pickup",
            "picked_up", "out_for_delivery", "nearby", "delivered", "cancelled"
        ]
        
        if new_status not in valid_statuses:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Invalid status: {new_status}"}
            )
        
        updated_count = 0
        for order_id in order_ids:
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                order.status = new_status  # ✅ СТРОКА, БЕЗ ENUM
                updated_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Обновлено {updated_count} заказов",
            "updated_count": updated_count
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

@app.post("/api/orders")
async def create_order_duplicate(request: Request):
    """Создание заказа - ДУБЛИКАТ"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    data = await request.json()
    bag_id = data.get("bag_id")
    delivery_type = data.get("delivery_type", "pickup")
    customer_address = data.get("address", "Самовывоз")
    customer_lat = data.get("lat")
    customer_lon = data.get("lon")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT id, bag_id, user_id, quantity, is_paid
            FROM temporary_reservations 
            WHERE user_id = %s 
              AND bag_id = %s 
              AND is_paid = false 
              AND expires_at > NOW()
            ORDER BY reserved_at DESC
            LIMIT 1
        """, (int(user_id), bag_id))
        
        reservation = cur.fetchone()
        
        cur.execute("""
            SELECT id, supplier_id, discounted_price, name
            FROM surprise_bags 
            WHERE id = %s
        """, (bag_id,))
        
        bag = cur.fetchone()
        if not bag:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Bag not found")
        
        bag_supplier_id = bag[1]
        bag_price = bag[2]
        bag_name = bag[3]
        
        import secrets
        order_number = f"ORD-{secrets.token_hex(4).upper()}"
        now = datetime.utcnow()
        
        if reservation:
            cur.execute("""
                INSERT INTO orders (
                    user_id, supplier_id, surprise_bag_id, 
                    order_number, status,
                    payment_status, customer_address, 
                    customer_lat, customer_lon,
                    amount_paid, delivery_type, created_at
                ) VALUES (
                    %s, %s, %s,
                    %s, 'pending',
                    'pending', %s,
                    %s, %s,
                    %s, %s, %s
                ) RETURNING id
            """, (
                int(user_id),
                bag_supplier_id,
                bag_id,
                order_number,
                customer_address if customer_address else "Самовывоз",
                customer_lat if delivery_type == "delivery" else None,
                customer_lon if delivery_type == "delivery" else None,
                bag_price,
                delivery_type,
                now
            ))
            
            order_id = cur.fetchone()[0]
            
            cur.execute("""
                UPDATE temporary_reservations 
                SET is_paid = true 
                WHERE id = %s
            """, (reservation[0],))
            
        else:
            cur.execute("""
                SELECT available_quantity, is_active 
                FROM surprise_bags 
                WHERE id = %s
            """, (bag_id,))
            
            bag_status = cur.fetchone()
            if not bag_status:
                cur.close()
                conn.close()
                raise HTTPException(status_code=404, detail="Bag not found")
            
            available = bag_status[0]
            is_active = bag_status[1]
            
            if available < 1 or not is_active:
                cur.close()
                conn.close()
                raise HTTPException(status_code=400, detail="Товар недоступен")
            
            cur.execute("""
                UPDATE surprise_bags 
                SET available_quantity = available_quantity - 1,
                    is_active = CASE WHEN available_quantity - 1 <= 0 THEN false ELSE true END
                WHERE id = %s
            """, (bag_id,))
            
            cur.execute("""
                INSERT INTO temporary_reservations (
                    bag_id, user_id, quantity, 
                    reserved_at, expires_at, is_paid
                ) VALUES (
                    %s, %s, 1,
                    %s, %s, false
                )
            """, (
                bag_id,
                int(user_id),
                now,
                now + timedelta(minutes=15)
            ))
            
            cur.execute("""
                INSERT INTO orders (
                    user_id, supplier_id, surprise_bag_id, 
                    order_number, status,
                    payment_status, customer_address, 
                    customer_lat, customer_lon,
                    amount_paid, delivery_type, created_at
                ) VALUES (
                    %s, %s, %s,
                    %s, 'pending',
                    'pending', %s,
                    %s, %s,
                    %s, %s, %s
                ) RETURNING id
            """, (
                int(user_id),
                bag_supplier_id,
                bag_id,
                order_number,
                customer_address if customer_address else "Самовывоз",
                customer_lat if delivery_type == "delivery" else None,
                customer_lon if delivery_type == "delivery" else None,
                bag_price,
                delivery_type,
                now
            ))
            
            order_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "order_id": order_id,
            "order_number": order_number,
            "status": "pending",
            "message": "Order created successfully"
        }
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(f"❌ Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))
                
@app.get("/api/surprise-bags/{bag_id}/rating")
async def get_surprise_bag_rating(
    bag_id: int,
    request: Request
):
    """Получить рейтинг сюрприза - ЧИСТЫЙ SQL"""
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Проверяем существование сюрприза
        cur.execute("""
            SELECT id, rating, total_reviews 
            FROM surprise_bags 
            WHERE id = %s
        """, (bag_id,))
        
        bag = cur.fetchone()
        if not bag:
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Surprise bag not found"}
            )
        
        # 2. Получаем оценку текущего пользователя (если есть)
        user_rating = None
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                from jose import jwt
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
                
                if user_id:
                    cur.execute("""
                        SELECT rating 
                        FROM surprise_bag_reviews 
                        WHERE surprise_bag_id = %s AND user_id = %s
                    """, (bag_id, int(user_id)))
                    
                    review = cur.fetchone()
                    if review:
                        user_rating = review['rating']
            except:
                pass
        
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "rating": bag['rating'] or 0,
            "total_reviews": bag['total_reviews'] or 0,
            "user_rating": user_rating
        }
        
    except Exception as e:
        cur.close()
        conn.close()
        print(f"❌ Ошибка получения рейтинга: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )
# backend/main.py - эндпоинт для отметки оплаты
# backend/main.py - ПОЛНОСТЬЮ ЗАМЕНИТЕ существующий эндпоинт
@app.post("/api/admin/mark-reservation-paid/{reservation_id}")
async def admin_mark_reservation_paid(
    reservation_id: int,
    request: Request
):
    """Админ отмечает бронирование как оплаченное - БЕЗ delivery_status"""
    
    # Проверка токена
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Admin only"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": f"Invalid token: {str(e)}"}
        )
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем резервацию
        cur.execute("""
            SELECT id, bag_id, user_id, quantity, is_paid
            FROM temporary_reservations 
            WHERE id = %s AND is_paid = false
        """, (reservation_id,))
        
        reservation = cur.fetchone()
        if not reservation:
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Reservation not found or already paid"}
            )
        
        reservation_bag_id = reservation[1]
        reservation_user_id = reservation[2]
        reservation_quantity = reservation[3]
        
        # Получаем сюрприз
        cur.execute("""
            SELECT id, supplier_id, discounted_price, name
            FROM surprise_bags 
            WHERE id = %s
        """, (reservation_bag_id,))
        
        bag = cur.fetchone()
        if not bag:
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Bag not found"}
            )
        
        bag_supplier_id = bag[1]
        bag_price = bag[2]
        bag_name = bag[3]
        
        # Помечаем резервацию как оплаченную
        cur.execute("""
            UPDATE temporary_reservations 
            SET is_paid = true 
            WHERE id = %s
        """, (reservation_id,))
        
        import secrets
        order_number = f"ORD-{secrets.token_hex(4).upper()}"
        now = datetime.utcnow()
        
        # Создаем заказ - БЕЗ delivery_status!
        cur.execute("""
            INSERT INTO orders (
                user_id, supplier_id, surprise_bag_id, 
                order_number, status,
                payment_status, paid_at, amount_paid,
                customer_address, delivery_type, created_at,
                confirmed_at
            ) VALUES (
                %s, %s, %s,
                %s, 'confirmed',
                'paid', %s, %s,
                'Самовывоз', 'pickup', %s,
                %s
            ) RETURNING id
        """, (
            reservation_user_id,
            bag_supplier_id,
            reservation_bag_id,
            order_number,
            now,
            bag_price * reservation_quantity,
            now,
            now
        ))
        
        order_id = cur.fetchone()[0]
        
        # Удаляем из корзины
        cur.execute("""
            DELETE FROM cart_items 
            WHERE user_id = %s AND surprise_bag_id = %s
        """, (reservation_user_id, reservation_bag_id))
        
        # Добавляем в трекинг - БЕЗ delivery_status!
        cur.execute("""
            INSERT INTO order_tracking (
                order_id, status, message, created_at
            ) VALUES (
                %s, 'confirmed', 'Заказ создан из резервации и подтвержден админом', %s
            )
        """, (order_id, now))
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Отправляем уведомление курьерам
        try:
            await manager.broadcast({
                "type": "new_order",
                "data": {
                    "order_id": order_id,
                    "order_number": order_number,
                    "supplier_id": bag_supplier_id,
                    "amount": bag_price * reservation_quantity,
                    "bag_name": bag_name,
                    "timestamp": now.isoformat()
                }
            }, channel="couriers")
            print(f"📢 Уведомление о заказе #{order_id} отправлено курьерам")
        except Exception as e:
            print(f"⚠️ Не удалось отправить уведомление: {e}")
        
        return {
            "success": True,
            "message": "Оплата подтверждена, заказ создан",
            "order_id": order_id,
            "order_number": order_number
        }
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(f"❌ Ошибка: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Ошибка: {str(e)}"}
        )

manager = ConnectionManager()



# backend/main.py - добавь этот эндпоинт

# backend/main.py - ОСТАВЬ ТОЛЬКО ЭТОТ

@app.post("/api/courier/register")
async def courier_api_register(request: Request, db: Session = Depends(get_db)):
    """API регистрация курьера"""
    
    try:
        data = await request.json()
        
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        phone = data.get("phone", "").strip()
        password = data.get("password", "")
        courier_type = data.get("courier_type", "pedestrian")
        car_model = data.get("car_model", "").strip()
        car_number = data.get("car_number", "").strip()
        
        print(f"📥 Регистрация курьера: {first_name} {last_name}, {phone}")
        
        # ======== ВАЛИДАЦИЯ ========
        if not first_name or not last_name:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Введите имя и фамилию"}
            )
        
        if not phone:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Введите номер телефона"}
            )
        
        if not password or len(password) < 6:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Пароль должен быть минимум 6 символов"}
            )
        
        if courier_type == "driver" and not car_model:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Укажите модель автомобиля"}
            )
        
        # ======== ПРОВЕРКА СУЩЕСТВОВАНИЯ ========
        existing = db.query(User).filter(User.phone == phone).first()
        if existing:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Пользователь с таким номером уже существует"}
            )
        
        # ======== СОЗДАЕМ ПОЛЬЗОВАТЕЛЯ ========
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        full_name = f"{first_name} {last_name}"
        
        new_user = User(
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            password=password_hash,
            role="courier",
            is_active=False,
            created_at=datetime.utcnow()
        )
        db.add(new_user)
        db.flush()
        
        # ======== СОЗДАЕМ ПРОФИЛЬ КУРЬЕРА ========
        speed = 5.0 if courier_type == "pedestrian" else 40.0
        radius = 3.0 if courier_type == "pedestrian" else 15.0
        
        courier_profile = CourierProfile(
            user_id=new_user.id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            courier_type=courier_type,
            car_model=car_model if courier_type == "driver" else None,
            car_number=car_number if courier_type == "driver" else None,
            speed_kmh=speed,
            delivery_radius_km=radius,
            is_verified=False,
            is_active=True,
            is_available=True,
            rating=5.0,
            total_deliveries=0,
            created_at=datetime.utcnow()
        )
        db.add(courier_profile)
        db.commit()
        
        print(f"✅ Курьер зарегистрирован: {full_name}")
        
        return JSONResponse(content={
            "success": True,
            "message": "Заявка отправлена на рассмотрение администратору",
            "courier_id": new_user.id
        })
        
    except Exception as e:
        print(f"❌ Ошибка регистрации курьера: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": f"Ошибка: {str(e)}"}
        )



from datetime import datetime, timezone  # ← ДОБАВЬ В НАЧАЛО
@app.post("/api/courier/arrived/{order_id}")
async def courier_arrived(order_id: int, request: Request):
    """Курьер прибыл к клиенту - МЕНЯЕМ СТАТУС ЗАКАЗА НА 'nearby'"""
    
    print("=" * 50)
    print(f"📍 КУРЬЕР ПРИБЫЛ К КЛИЕНТУ - ЗАКАЗ #{order_id}")
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        print(f"🔑 Курьер: {user_id}")
    except Exception as e:
        print(f"❌ Ошибка токена: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем заказ
        cur.execute("""
            SELECT id, assigned_courier_id, user_id, order_number, status
            FROM orders 
            WHERE id = %s
        """, (order_id,))
        
        order = cur.fetchone()
        if not order:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Order not found")
        
        assigned_courier = order[1]
        customer_user_id = order[2]
        order_number = order[3]
        current_status = order[4]
        
        print(f"📋 Текущий статус заказа: {current_status}")
        
        if assigned_courier != int(user_id):
            cur.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Order not assigned to you")
        
        # ✅ Если уже nearby — пропускаем
        if current_status == 'nearby':
            cur.close()
            conn.close()
            return {
                "success": True,
                "message": "Заказ уже в статусе 'nearby'",
                "status": "nearby"
            }
        
        # ✅ Если уже waiting_confirmation — пропускаем
        if current_status == 'waiting_confirmation':
            cur.close()
            conn.close()
            return {
                "success": True,
                "message": "Заказ уже в статусе 'waiting_confirmation'",
                "status": "waiting_confirmation"
            }
        
        # ✅ МЕНЯЕМ СТАТУС НА 'nearby' (ПРОСТАЯ СТРОКА!)
        cur.execute("""
            UPDATE orders 
            SET status = 'nearby'
            WHERE id = %s
        """, (order_id,))
        
        print(f"✅ Статус заказа изменен с '{current_status}' на 'nearby'")
        
        # Обновляем курьера
        cur.execute("""
            UPDATE courier_profiles 
            SET current_order_status = 'nearby'
            WHERE user_id = %s
        """, (int(user_id),))
        
        # Добавляем в трекинг
        cur.execute("""
            INSERT INTO order_tracking 
            (order_id, status, message, created_at)
            VALUES (%s, 'nearby', 'Курьер прибыл к клиенту', NOW())
        """, (order_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Заказ #{order_id} помечен как 'nearby'")
        
        # Отправляем уведомление клиенту
        try:
            if customer_user_id:
                await manager.send_to_user(customer_user_id, {
                    "type": "courier_arrived",
                    "data": {
                        "order_id": order_id,
                        "order_number": order_number,
                        "status": "nearby",
                        "message": f"Курьер прибыл к вам! Выходите за заказом.",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                })
                print(f"📢 Уведомление отправлено клиенту {customer_user_id}")
        except Exception as e:
            print(f"⚠️ Не удалось отправить уведомление: {e}")
        
        return {
            "success": True,
            "message": "Уведомление о прибытии отправлено клиенту",
            "order_id": order_id,
            "order_number": order_number,
            "status": "nearby"
        }
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/api/customer/confirm-delivery/{order_id}")
async def customer_confirm_delivery(
    order_id: int,
    request: Request
):
    """Клиент подтверждает получение заказа"""
    
    print("=" * 50)
    print(f"✅ КЛИЕНТ ПОДТВЕРЖДАЕТ ПОЛУЧЕНИЕ - ЗАКАЗ #{order_id}")
    
    # Получаем user_id
    user_id = None
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from jose import jwt
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            print(f"🔑 user_id из токена: {user_id}")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    if not user_id:
        user_id = request.cookies.get("user_id")
        print(f"🍪 user_id из cookie: {user_id}")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Проверяем заказ
        cur.execute("""
            SELECT id, user_id, status, assigned_courier_id, order_number, amount_paid
            FROM orders 
            WHERE id = %s
        """, (order_id,))
        
        order = cur.fetchone()
        if not order:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Order not found")
        
        order_user_id = order[1]
        order_status = order[2]
        assigned_courier = order[3]
        order_number = order[4]
        amount_paid = order[5]
        
        print(f"📋 Заказ #{order_id}: статус={order_status}, клиент={order_user_id}, курьер={assigned_courier}")
        
        # 2. Проверяем, что заказ принадлежит клиенту
        if int(order_user_id) != int(user_id):
            cur.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Not your order")
        
        # 3. ✅ Проверяем статус
        if order_status == 'delivered':
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={
                    "success": False, 
                    "message": "Заказ уже был доставлен ранее",
                    "status": "delivered"
                }
            )
        
        if order_status == 'cancelled':
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={
                    "success": False, 
                    "message": "Заказ был отменен",
                    "status": "cancelled"
                }
            )
        
        # 4. ✅ Проверяем, что заказ в статусе 'waiting_confirmation' или 'nearby'
        if order_status not in ['waiting_confirmation', 'nearby']:
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={
                    "success": False, 
                    "message": f"Заказ не готов к получению. Статус: {order_status}",
                    "status": order_status
                }
            )
        
        # 5. ✅ Меняем статус на 'delivered'
        cur.execute("""
            UPDATE orders 
            SET status = 'delivered',
                delivered_at = NOW()
            WHERE id = %s
        """, (order_id,))
        
        # 6. Освобождаем курьера
        if assigned_courier:
            cur.execute("""
                UPDATE courier_profiles 
                SET current_order_id = NULL,
                    current_order_status = NULL,
                    is_available = true,
                    total_deliveries = COALESCE(total_deliveries, 0) + 1,
                    completed_orders_today = COALESCE(completed_orders_today, 0) + 1
                WHERE user_id = %s
            """, (assigned_courier,))
            print(f"✅ Курьер {assigned_courier} освобожден")
        
        # 7. Добавляем в трекинг
        cur.execute("""
            INSERT INTO order_tracking 
            (order_id, status, message, created_at)
            VALUES (%s, 'delivered', 'Клиент подтвердил получение заказа', NOW())
        """, (order_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Заказ #{order_id} доставлен!")
        
        # 8. ✅ ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ КУРЬЕРУ (ВАЖНО!)
        try:
            if assigned_courier:
                # Получаем имя курьера для уведомления
                conn2 = get_db_connection()
                cur2 = conn2.cursor()
                cur2.execute("""
                    SELECT first_name, last_name 
                    FROM courier_profiles 
                    WHERE user_id = %s
                """, (assigned_courier,))
                courier = cur2.fetchone()
                cur2.close()
                conn2.close()
                
                courier_name = f"{courier[0]} {courier[1]}" if courier else "Курьер"
                
                # ✅ ОТПРАВЛЯЕМ ЧЕРЕЗ send_to_courier
                await manager.send_to_courier(assigned_courier, {
                    "type": "delivery_confirmed_by_customer",
                    "data": {
                        "order_id": order_id,
                        "order_number": order_number,
                        "status": "delivered",
                        "message": f"✅ Клиент подтвердил получение заказа #{order_number}!",
                        "courier_name": courier_name,
                        "amount": float(amount_paid) if amount_paid else 0,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                print(f"📢 Уведомление отправлено курьеру {assigned_courier}")
                
                # ✅ ТАКЖЕ ОТПРАВЛЯЕМ ЧЕРЕЗ BROADCAST (на всякий случай)
                await manager.broadcast({
                    "type": "delivery_confirmed_by_customer",
                    "data": {
                        "order_id": order_id,
                        "order_number": order_number,
                        "status": "delivered",
                        "message": f"✅ Клиент подтвердил получение заказа #{order_number}!",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }, channel=f"courier_{assigned_courier}")
                print(f"📢 Broadcast отправлен курьеру {assigned_courier}")
                
        except Exception as e:
            print(f"⚠️ Не удалось отправить уведомление курьеру: {e}")
            import traceback
            traceback.print_exc()
        
        return {
            "success": True,
            "message": "Спасибо! Заказ получен.",
            "order_id": order_id,
            "order_number": order_number,
            "status": "delivered",
            "courier_notified": True
        }
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    
@app.post("/api/courier/take-order/{order_id}")
async def courier_take_order(order_id: int, request: Request):
    """Курьер берет заказ в работу - БЕЗ delivery_status"""
    
    print("=" * 50)
    print(f"📦 ПОПЫТКА ВЗЯТЬ ЗАКАЗ #{order_id}")
    
    # ✅ ТОЛЬКО Bearer токен
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        print(f"🔑 Пользователь из Bearer токена: {user_id}")
    except Exception as e:
        print(f"❌ Ошибка декодирования токена: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Получаем курьера
        cur.execute("""
            SELECT id, is_online, is_available, current_order_id, is_verified,
                   first_name, last_name, phone
            FROM courier_profiles 
            WHERE user_id = %s
        """, (int(user_id),))
        
        courier = cur.fetchone()
        if not courier:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Courier not found")
        
        courier_id = courier[0]
        is_online = courier[1]
        is_available = courier[2]
        current_order_id = courier[3]
        is_verified = courier[4]
        courier_first_name = courier[5]
        courier_last_name = courier[6]
        courier_phone = courier[7]
        
        print(f"👤 Курьер: id={courier_id}, онлайн={is_online}, верифицирован={is_verified}")
        
        # Проверки
        if not is_verified:
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Курьер не верифицирован"}
            )
        
        if not is_online:
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Вы не на линии. Включите режим 'На линии'"}
            )
        
        if current_order_id:
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"У вас уже есть активный заказ #{current_order_id}"}
            )
        
        # 2. Проверяем заказ
        cur.execute("""
            SELECT id, status, assigned_courier_id, delivery_type, order_number,
                   user_id, amount_paid
            FROM orders 
            WHERE id = %s 
            FOR UPDATE
        """, (order_id,))
        
        order = cur.fetchone()
        if not order:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Order not found")
        
        order_status = order[1]
        assigned_courier = order[2]
        delivery_type = order[3]
        order_number = order[4]
        customer_user_id = order[5]
        amount_paid = order[6]
        
        print(f"📋 Заказ #{order_id}: статус={order_status}, назначен курьеру={assigned_courier}, тип={delivery_type}")
        
        # Проверяем, что заказ доступен
        if order_status != 'confirmed':
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"Заказ не доступен. Текущий статус: {order_status}"}
            )
        
        if assigned_courier is not None:
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Заказ уже назначен другому курьеру"}
            )
        
        if delivery_type != 'delivery':
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Это заказ на самовывоз! Курьер не требуется."}
            )
        
        # 3. Назначаем заказ курьеру
        cur.execute("""
            UPDATE orders 
            SET assigned_courier_id = %s,
                status = 'ready_for_pickup'
            WHERE id = %s
        """, (int(user_id), order_id))
        
        # 4. Обновляем профиль курьера
        cur.execute("""
            UPDATE courier_profiles 
            SET current_order_id = %s,
                current_order_status = 'assigned',
                is_available = false
            WHERE user_id = %s
        """, (order_id, int(user_id)))
        
        # 5. Добавляем запись в трекинг - БЕЗ delivery_status!
        cur.execute("""
            INSERT INTO order_tracking 
            (order_id, status, message, created_at)
            VALUES (%s, 'ready_for_pickup', 'Курьер назначен на заказ', NOW())
        """, (order_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Заказ #{order_id} назначен курьеру {user_id}")
        
        # 6. Отправляем уведомления
        try:
            if customer_user_id:
                await manager.broadcast({
                    "type": "order_assigned",
                    "data": {
                        "order_id": order_id,
                        "order_number": order_number,
                        "courier_id": user_id,
                        "courier_name": f"{courier_first_name} {courier_last_name}",
                        "courier_phone": courier_phone,
                        "status": "assigned",
                        "message": f"🚚 Курьер {courier_first_name} назначен на ваш заказ #{order_number}!",
                        "amount": float(amount_paid) if amount_paid else 0,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }, channel=f"user_{customer_user_id}")
                print(f"📢 Уведомление отправлено КЛИЕНТУ {customer_user_id}")
            
            await manager.broadcast({
                "type": "order_taken",
                "data": {
                    "order_id": order_id,
                    "order_number": order_number,
                    "status": "assigned",
                    "message": f"✅ Вы взяли заказ #{order_number}! Едьте в ресторан.",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }, channel=f"courier_{user_id}")
            
        except Exception as e:
            print(f"⚠️ Не удалось отправить уведомление: {e}")
        
        return {
            "success": True,
            "message": "Заказ взят в работу! Едьте в ресторан.",
            "order_id": order_id,
            "order_number": order_number,
            "status": "ready_for_pickup"
        }
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(f"❌ Ошибка при взятии заказа: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))




# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/admin/process-refund/{order_id}")
async def admin_process_refund(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Админ обрабатывает возврат денег клиенту"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Admin only"}
            )
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        data = await request.json()
        reason = data.get("reason", "Возврат по запросу администратора")
        
        from datetime import datetime
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        # Обновляем статусы
        order.payment_status = "refunded"
        order.refund_status = "completed"
        order.refund_processed_at = datetime.utcnow()
        order.refund_reason = reason
        order.refund_amount = order.amount_paid
        
        # ✅ ИСПРАВЛЕНО: status = 'cancelled' (строка, БЕЗ ENUM)
        order.status = "cancelled"
        order.cancelled_at = datetime.utcnow()
        
        # Возвращаем количество сюрприза
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
        if bag:
            bag.available_quantity += 1
            if bag.available_quantity > 0:
                bag.is_active = True
            print(f"📦 Восстановлен товар '{bag.name}', теперь {bag.available_quantity} шт.")
        
        # ✅ ОСВОБОЖДАЕМ КУРЬЕРА (если был назначен)
        if order.assigned_courier_id:
            db.query(CourierProfile).filter(
                CourierProfile.user_id == order.assigned_courier_id
            ).update({
                "current_order_id": None,
                "current_order_status": None,
                "is_available": True,
                "is_online": True
            })
            print(f"✅ Курьер освобожден от заказа #{order_id}")
        
        db.commit()
        
        print(f"✅ Админ обработал возврат для заказа #{order.order_number}")
        
        return {
            "success": True,
            "message": "Возврат обработан, деньги возвращены клиенту",
            "order_id": order.id,
            "order_number": order.order_number,
            "amount_refunded": order.amount_paid,
            "refund_processed_at": order.refund_processed_at.isoformat()
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )
# backend/main.py - исправленный WebSocket без Depends
courier_connections = {}
supplier_connections = {}
active_connections = set()
ws_connection_count = 0
MAX_WS_CONNECTIONS = 50
ws_lock = asyncio.Lock()

# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============
def get_current_user_from_token(request: Request) -> int:
    """Получить user_id из Bearer токена"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(user_id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# ============ WEBSOCKET ДЛЯ КУРЬЕРОВ (ОПТИМИЗИРОВАННЫЙ) ============
# @app.websocket("/ws/courier-tracking")
# async def courier_tracking_websocket(websocket: WebSocket):
#     """WebSocket для отслеживания курьеров в реальном времени"""
#     global ws_connection_count
    
#     # Проверка лимита
#     async with ws_lock:
#         if ws_connection_count >= MAX_WS_CONNECTIONS:
#             await websocket.close(code=1008, reason="Too many connections")
#             return
#         ws_connection_count += 1
    
#     await websocket.accept()
    
#     token = websocket.query_params.get("token")
#     user_id = None
#     courier_id = None
    
#     if token:
#         try:
#             from jose import jwt
#             payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#             user_id = payload.get("sub")
#         except:
#             pass
    
#     if not user_id:
#         user_id = websocket.cookies.get("user_id")
    
#     if not user_id:
#         await websocket.close(code=1008, reason="Not authenticated")
#         async with ws_lock:
#             ws_connection_count -= 1
#         return
    
#     db = SessionLocal()
    
#     try:
#         courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
#         if not courier:
#             await websocket.close(code=1008, reason="Courier not found")
#             return
        
#         courier_id = courier.id
#         print(f"✅ Курьер {courier_id} подключен. Всего: {ws_connection_count}")
        
#         if courier_id not in courier_connections:
#             courier_connections[courier_id] = []
#         courier_connections[courier_id].append(websocket)
#         active_connections.add(websocket)
        
#         await websocket.send_json({
#             "type": "connected",
#             "courier_id": courier_id,
#             "timestamp": datetime.utcnow().isoformat()
#         })
        
#         # Устанавливаем таймаут
#         while True:
#             try:
#                 data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
#                 message = json.loads(data)
                
#                 if message.get("type") == "ping":
#                     await websocket.send_json({"type": "pong"})
#                 elif message.get("type") == "update_location":
#                     lat = message.get("lat")
#                     lon = message.get("lon")
#                     if lat and lon:
#                         courier.current_lat = lat
#                         courier.current_lon = lon
#                         courier.last_location_update = datetime.utcnow()
#                         db.commit()
                        
#                         # Трансляция всем
#                         await manager.broadcast({
#                             "type": "courier_location",
#                             "courier_id": courier_id,
#                             "first_name": courier.first_name,
#                             "last_name": courier.last_name,
#                             "lat": lat,
#                             "lon": lon,
#                             "timestamp": datetime.utcnow().isoformat()
#                         }, channel="surprise_bags")
                        
#             except asyncio.TimeoutError:
#                 await websocket.send_json({"type": "ping"})
#             except WebSocketDisconnect:
#                 break
#             except Exception as e:
#                 print(f"Ошибка: {e}")
#                 break
                
#     except Exception as e:
#         print(f"WebSocket ошибка: {e}")
#     finally:
#         if courier_id and courier_id in courier_connections:
#             if websocket in courier_connections[courier_id]:
#                 courier_connections[courier_id].remove(websocket)
#         active_connections.discard(websocket)
#         db.close()
#         async with ws_lock:
#             ws_connection_count -= 1
#         print(f"🔌 Курьер {courier_id} отключен. Осталось: {ws_connection_count}")

# backend/main.py - Improved WebSocket endpoint
@app.websocket("/ws/courier-tracking")
async def courier_tracking_websocket(websocket: WebSocket):
    """WebSocket для отслеживания курьеров с улучшенной стабильностью"""
    
    # ✅ CRITICAL FIX: Accept connection FIRST
    try:
        await websocket.accept()
        print("✅ WebSocket connection accepted")
    except Exception as e:
        print(f"❌ Failed to accept connection: {e}")
        return
    
    # Now get token from query parameter
    token = websocket.query_params.get("token")
    
    print(f"🔍 WebSocket connection attempt with token: {token[:50] if token else 'None'}...")
    
    if not token:
        print("❌ No token provided")
        await websocket.send_json({"type": "error", "message": "Token required"})
        await websocket.close(code=1008, reason="Token required")
        return
    
    user_id = None
    
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        print(f"✅ Token decoded, user_id: {user_id}")
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        await websocket.send_json({"type": "error", "message": "Token expired"})
        await websocket.close(code=1008, reason="Token expired")
        return
    except jwt.JWTError as e:
        print(f"❌ Invalid token: {e}")
        await websocket.send_json({"type": "error", "message": f"Invalid token: {str(e)}"})
        await websocket.close(code=1008, reason=f"Invalid token: {str(e)}")
        return
    except Exception as e:
        print(f"❌ Token decode error: {e}")
        await websocket.send_json({"type": "error", "message": f"Token decode error: {str(e)}"})
        await websocket.close(code=1008, reason=f"Token decode error: {str(e)}")
        return
    
    if not user_id:
        print("❌ No user_id in token")
        await websocket.send_json({"type": "error", "message": "No user_id in token"})
        await websocket.close(code=1008, reason="No user_id in token")
        return
    
    db = SessionLocal()
    
    try:
        courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
        if not courier:
            print(f"❌ Courier not found for user_id={user_id}")
            await websocket.send_json({"type": "error", "message": "Courier not found"})
            await websocket.close(code=1008, reason="Courier not found")
            return
        
        courier_id = courier.id
        print(f"✅ Courier found: id={courier_id}, name={courier.first_name}")
        
        # Отправляем подтверждение
        await websocket.send_json({
            "type": "connected",
            "courier_id": courier_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Подписываем курьера
        if courier_id not in manager.courier_connections:
            manager.courier_connections[courier_id] = set()
        manager.courier_connections[courier_id].add(websocket)
        print(f"📡 Courier {courier_id} subscribed")
        
        await websocket.send_json({
            "type": "subscribed",
            "channel": "couriers",
            "message": "Вы будете получать уведомления о новых заказах"
        })
        
        # ✅ Улучшенный heartbeat с таймаутом
        last_pong = datetime.utcnow()
        heartbeat_interval = 25  # секунд
        heartbeat_timeout = 60   # секунд без ответа
        
        while True:
            try:
                # Ждем сообщение с таймаутом
                data = await asyncio.wait_for(websocket.receive_text(), timeout=heartbeat_interval)
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    print(f"💓 Heartbeat from courier {courier_id}")
                    last_pong = datetime.utcnow()
                    
                elif message.get("type") == "update_location":
                    lat = message.get("lat")
                    lon = message.get("lon")
                    if lat and lon:
                        courier.current_lat = lat
                        courier.current_lon = lon
                        courier.last_location_update = datetime.utcnow()
                        db.commit()
                        print(f"📍 Courier {courier_id} location updated: {lat}, {lon}")
                        
                        # Транслируем всем клиентам
                        await manager.broadcast_to_all({
                            "type": "courier_location",
                            "courier_id": courier_id,
                            "first_name": courier.first_name,
                            "last_name": courier.last_name,
                            "lat": lat,
                            "lon": lon,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                
                elif message.get("type") == "pong":
                    print(f"💓 Pong received from courier {courier_id}")
                    last_pong = datetime.utcnow()
                
            except asyncio.TimeoutError:
                # Проверяем, не истекло ли время ожидания pong
                time_since_last_pong = (datetime.utcnow() - last_pong).total_seconds()
                if time_since_last_pong > heartbeat_timeout:
                    print(f"⚠️ Heartbeat timeout for courier {courier_id}, closing connection")
                    break
                else:
                    # Отправляем ping для проверки
                    try:
                        await websocket.send_json({"type": "ping"})
                        print(f"💓 Sending ping to courier {courier_id}")
                    except:
                        print(f"❌ Failed to send ping to courier {courier_id}")
                        break
                        
            except WebSocketDisconnect:
                print(f"🔌 Courier {courier_id} disconnected normally")
                break
                
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON from courier {courier_id}: {e}")
                continue
                
            except Exception as e:
                print(f"❌ Error in WebSocket loop for courier {courier_id}: {e}")
                break
                
    except Exception as e:
        print(f"❌ WebSocket error for courier: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
    finally:
        # Очищаем соединение
        if 'courier_id' in locals() and courier_id in manager.courier_connections:
            manager.courier_connections[courier_id].discard(websocket)
            if not manager.courier_connections[courier_id]:
                del manager.courier_connections[courier_id]
                print(f"🗑️ Removed courier {courier_id} from connections")
        db.close()

@app.get("/api/debug/suppliers")
async def debug_suppliers(db: Session = Depends(get_db)):
    """Временный эндпоинт для отладки - показать всех поставщиков с email"""
    suppliers = db.query(Supplier).all()
    result = []
    for s in suppliers:
        # Получаем email из связанного пользователя
        user = db.query(User).filter(User.id == s.user_id).first()
        result.append({
            "id": s.id,
            "business_name": s.business_name,
            "email": user.email if user else "No email",
            "user_id": s.user_id,
            "phone": s.phone
        })
    return {
        "count": len(result),
        "suppliers": result
    }
# Добавьте в main.py бекенда
import psutil
import os

@app.get("/api/debug/memory")
async def check_memory():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    return {
        "current_memory_mb": memory_mb,
        "limit_mb": 512,
        "free_mb": 512 - memory_mb,
        "percent_used": (memory_mb / 512) * 100
    }
        
@app.get("/api/courier/available-orders")
async def get_available_orders_for_courier(request: Request):
    """Доступные заказы для курьера - ЧИСТЫЙ SQL БЕЗ delivery_status"""
    
    # Проверка токена
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Получаем курьера
        cur.execute("""
            SELECT id, is_online, is_available, current_order_id, 
                   current_lat, current_lon, courier_type, is_verified
            FROM courier_profiles 
            WHERE user_id = %s
        """, (int(user_id),))
        
        courier = cur.fetchone()
        if not courier:
            cur.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Not a courier")
        
        if not courier['is_online']:
            cur.close()
            conn.close()
            return {"success": True, "orders": [], "message": "Вы не на линии"}
        
        if not courier['is_verified']:
            cur.close()
            conn.close()
            return {"success": True, "orders": [], "message": "Курьер не верифицирован"}
        
        courier_lat = courier['current_lat']
        courier_lon = courier['current_lon']
        
        if not courier_lat or not courier_lon:
            cur.close()
            conn.close()
            return {"success": True, "orders": [], "message": "Позиция не определена"}
        
        current_order_id = courier['current_order_id']
        
        # Получаем доступные заказы - БЕЗ delivery_status!
        cur.execute("""
            SELECT 
                o.id as order_id,
                o.order_number,
                o.amount_paid as amount,
                o.customer_address,
                o.customer_lat,
                o.customer_lon,
                o.supplier_id,
                o.surprise_bag_id,
                o.delivery_type,
                s.business_name as supplier_name,
                s.address as supplier_address,
                s.lat as supplier_lat,
                s.lon as supplier_lon,
                sb.name as bag_name,
                (6371 * acos(
                    LEAST(1, GREATEST(-1, 
                        sin(radians(%s)) * sin(radians(s.lat)) + 
                        cos(radians(%s)) * cos(radians(s.lat)) * 
                        cos(radians(s.lon) - radians(%s))
                    ))
                )) as distance_km
            FROM orders o
            LEFT JOIN suppliers s ON s.id = o.supplier_id
            LEFT JOIN surprise_bags sb ON sb.id = o.surprise_bag_id
            WHERE o.status = 'confirmed' 
              AND o.assigned_courier_id IS NULL
              AND o.delivery_type = 'delivery'
              AND o.id != %s
              AND s.lat IS NOT NULL 
              AND s.lon IS NOT NULL
            ORDER BY distance_km ASC
            LIMIT 50
        """, (courier_lat, courier_lat, courier_lon, current_order_id or 0))
        
        orders = cur.fetchall()
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "orders": orders,
            "count": len(orders)
        }
        
    except Exception as e:
        cur.close()
        conn.close()
        print(f"❌ Ошибка: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e), "orders": []}
        )
@app.get("/api/couriers/online")
async def get_online_couriers(db: Session = Depends(get_db)):
    """Получить всех онлайн курьеров для карты"""
    
    couriers = db.query(CourierProfile).filter(
        CourierProfile.is_online == True,
        CourierProfile.is_verified == True
    ).all()
    
    result = []
    for c in couriers:
        result.append({
            "id": c.id,
            "user_id": c.user_id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "phone": c.phone,
            "courier_type": c.courier_type,
            "car_model": c.car_model,
            "car_number": c.car_number,
            "current_lat": c.current_lat,
            "current_lon": c.current_lon,
            "current_order_status": c.current_order_status,
            "rating": c.rating,
            "total_deliveries": c.total_deliveries,
            "is_online": c.is_online
        })
    
    return {"success": True, "couriers": result}

# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/courier/respond-to-proposal")
async def respond_to_proposal(request: Request, db: Session = Depends(get_db)):
    """Курьер отвечает на предложение заказа"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
        
        # Проверяем что это курьер
        if payload.get("role") != "courier":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Not a courier"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        data = await request.json()
        response = data.get("response")  # "accept" или "decline"
        
        if response not in ["accept", "decline"]:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Response must be 'accept' or 'decline'"}
            )
        
        from datetime import datetime
        
        courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
        
        if not courier:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Courier not found"}
            )
        
        if not courier.proposed_order_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Нет предложенных заказов"}
            )
        
        # Проверяем, не истекло ли предложение
        if courier.proposed_order_expires_at and courier.proposed_order_expires_at < datetime.utcnow():
            courier.proposed_order_id = None
            db.commit()
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Предложение истекло"}
            )
        
        if response == "accept":
            order = db.query(Order).filter(Order.id == courier.proposed_order_id).first()
            
            if not order:
                courier.proposed_order_id = None
                db.commit()
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "detail": "Order not found"}
                )
            
            # ✅ ИСПРАВЛЕНО: проверка статуса как строка (БЕЗ ENUM)
            if order.status == "pending":
                order.assigned_courier_id = courier.user_id
                order.status = "confirmed"
                order.confirmed_at = datetime.utcnow()
                
                if courier.current_order_id:
                    # Ставим в очередь
                    message = "Заказ добавлен в очередь"
                else:
                    courier.current_order_id = courier.proposed_order_id
                    courier.current_order_status = "confirmed"
                    courier.is_available = False
                    message = "Заказ назначен!"
                
                courier.proposed_order_id = None
                db.commit()
                
                # Уведомляем через WebSocket
                try:
                    await manager.broadcast({
                        "type": "order_assigned",
                        "order_id": order.id,
                        "courier_id": courier.id,
                        "courier_name": f"{courier.first_name} {courier.last_name}"
                    }, channel="orders")
                except Exception as e:
                    print(f"⚠️ Ошибка отправки WebSocket: {e}")
                
                return {
                    "success": True,
                    "message": message,
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "status": order.status
                }
            else:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "detail": f"Order status is not pending: {order.status}"}
                )
        
        else:  # decline
            courier.proposed_order_id = None
            db.commit()
            return {
                "success": True,
                "message": "Предложение отклонено"
            }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )
# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/courier/accept-order/{order_id}")
async def courier_accept_order(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Курьер принимает заказ из списка"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
        
        # Проверяем что это курьер
        if payload.get("role") != "courier":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Not a courier"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        from datetime import datetime
        
        courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
        
        if not courier:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Courier profile not found"}
            )
        
        # Проверяем что курьер активен и верифицирован
        if not courier.is_verified:
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Курьер не верифицирован"}
            )
        
        if not courier.is_available:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Курьер не доступен"}
            )
        
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        # ✅ ИСПРАВЛЕНО: проверка статуса как строка (БЕЗ ENUM)
        if order.status not in ["pending", "confirmed"]:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Заказ уже назначен. Текущий статус: {order.status}"}
            )
        
        if courier.current_order_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "У вас уже есть активный заказ"}
            )
        
        # ✅ ИСПРАВЛЕНО: status = 'confirmed' (строка, БЕЗ ENUM)
        order.assigned_courier_id = courier.user_id
        order.status = "confirmed"
        order.confirmed_at = datetime.utcnow()
        
        courier.current_order_id = order_id
        courier.current_order_status = "confirmed"
        courier.is_available = False
        
        db.commit()
        
        print(f"✅ Курьер {courier.first_name} принял заказ #{order.order_number}")
        
        # Уведомляем через WebSocket
        try:
            await manager.broadcast({
                "type": "order_assigned",
                "order_id": order.id,
                "order_number": order.order_number,
                "courier_id": courier.id,
                "courier_name": f"{courier.first_name} {courier.last_name}"
            }, channel="orders")
        except Exception as e:
            print(f"⚠️ Ошибка отправки WebSocket: {e}")
        
        return {
            "success": True,
            "message": "Заказ принят",
            "order_id": order_id,
            "order_number": order.order_number,
            "status": order.status,
            "courier": {
                "id": courier.id,
                "name": f"{courier.first_name} {courier.last_name}",
                "car_model": courier.car_model,
                "car_number": courier.car_number
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

# backend/main.py - ПРОВЕРЬ ЧТО ЭНДП



@app.get("/api/cart/reservation")
async def get_active_reservation(request: Request):
    """Получить активную резервацию - ЧИСТЫЙ SQL"""
    
    user_id = get_user_id_from_token(request)
    
    if not user_id:
        return {"reservation": None}
    
    try:
        from datetime import datetime
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, bag_id, expires_at
            FROM temporary_reservations
            WHERE user_id = %s AND is_paid = false AND expires_at > NOW()
            ORDER BY expires_at ASC
            LIMIT 1
        """, (user_id,))
        
        reservation = cur.fetchone()
        cur.close()
        conn.close()
        
        if reservation:
            return {
                "reservation": {
                    "id": reservation['id'],
                    "expires_at": reservation['expires_at'].isoformat(),
                    "bag_id": reservation['bag_id']
                }
            }
        
        return {"reservation": None}
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {"reservation": None}

@app.get("/api/courier/me")
async def get_courier_info(request: Request, db: Session = Depends(get_db)):
    """Получить информацию о текущем курьере"""
    token = request.cookies.get("courier_token")
    if not token or token not in courier_sessions:
        return {"authenticated": False}
    
    session = courier_sessions[token]
    if session["expires_at"] < datetime.utcnow():
        del courier_sessions[token]
        return {"authenticated": False}
    
    user = db.query(User).filter(User.id == session["courier_id"]).first()
    courier_profile = db.query(CourierProfile).filter(CourierProfile.user_id == session["courier_id"]).first()
    
    if not user or not courier_profile:
        return {"authenticated": False}
    
    return {
        "authenticated": True,
        "courier": {
            "id": user.id,
            "full_name": user.full_name,
            "phone": user.phone,
            "car_model": courier_profile.car_model,
            "car_number": courier_profile.car_number,
            "rating": courier_profile.rating,
            "total_deliveries": courier_profile.total_deliveries
        }
    }






def get_user_id_from_token(request: Request):
    """Получить user_id из Bearer токена"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            return int(user_id)
    except Exception as e:
        print(f"❌ Ошибка декодирования токена: {e}")
        return None
    
    return None

# backend/main.py - добавьте в конец файла

# ============ COURIER ENDPOINTS ============

# backend/main.py - убедитесь что эндпоинт выглядит так:

# backend/main.py - исправленный эндпоинт
# backend/main.py - ИСПРАВЛЕННАЯ РЕГИСТРАЦИЯ КУРЬЕРА

@app.post("/api/courier/go-online")
async def courier_go_online(request: Request):
    """Курьер выходит на линию - ЧИСТЫЙ SQL"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    data = await request.json()
    lat = data.get("lat")
    lon = data.get("lon")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем верификацию
        cur.execute("""
            SELECT is_verified FROM courier_profiles WHERE user_id = %s
        """, (int(user_id),))
        
        result = cur.fetchone()
        if not result or not result[0]:
            raise HTTPException(status_code=403, detail="Курьер не верифицирован")
        
        cur.execute("""
            UPDATE courier_profiles 
            SET is_online = true,
                is_available = true,
                last_online_at = NOW(),
                current_lat = %s,
                current_lon = %s
            WHERE user_id = %s
        """, (lat, lon, int(user_id)))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Вы на линии", "is_online": True}
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/order/{order_id}/reject")
async def customer_reject_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Клиент отказывается от заказа"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (ОСНОВНОЙ СПОСОБ)
    auth_header = request.headers.get("Authorization")
    user_id = None
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from jose import jwt
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            
            # Проверяем что это клиент (customer)
            if payload.get("role") != "customer":
                return JSONResponse(
                    status_code=403,
                    content={"success": False, "detail": "Only customers can reject orders"}
                )
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Token expired"}
            )
        except jwt.JWTError as e:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": f"Invalid token: {str(e)}"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": f"Authentication error: {str(e)}"}
            )
    
    # ✅ Fallback: проверка через cookies (для обратной совместимости)
    if not user_id:
        user_id = request.cookies.get("user_id")
    
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Not authenticated"}
        )
    
    try:
        data = await request.json()
        reason = data.get("reason", "Не указана")
        
        from datetime import datetime
        
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == int(user_id)
        ).first()
        
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        # ✅ ИСПРАВЛЕНО: проверка статуса как строка (БЕЗ ENUM)
        if order.status != "out_for_delivery":
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Cannot reject order at this stage. Current status: {order.status}"}
            )
        
        # Создаем запрос на возврат
        order.refund_requested_by_customer = True
        order.refund_requested_at = datetime.utcnow()
        order.refund_reason = reason
        order.refund_status = "requested"
        
        db.commit()
        
        print(f"📝 Клиент запросил возврат для заказа #{order.order_number}: {reason}")
        
        return {
            "success": True,
            "message": "Refund requested. Admin will process.",
            "refund_request_id": order.id,
            "order_id": order.id,
            "order_number": order.order_number,
            "refund_requested_at": order.refund_requested_at.isoformat()
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

@app.post("/api/courier/force-clear-order")
async def force_clear_courier_order(request: Request, db: Session = Depends(get_db)):
    """Принудительная очистка заказа у курьера"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"success": False})
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except:
        return JSONResponse(status_code=401, content={"success": False})
    
    courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
    if not courier:
        return JSONResponse(status_code=404, content={"success": False})
    
    old_order_id = courier.current_order_id
    courier.current_order_id = None
    courier.current_order_status = None
    courier.is_available = True
    db.commit()
    
    return {"success": True, "message": f"Очищен заказ #{old_order_id}"}


@app.post("/api/courier/go-offline")
async def courier_go_offline(request: Request):
    """Курьер уходит с линии - ЧИСТЫЙ SQL"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем, есть ли активный заказ
        cur.execute("""
            SELECT current_order_id FROM courier_profiles WHERE user_id = %s
        """, (int(user_id),))
        
        result = cur.fetchone()
        if result and result[0]:
            raise HTTPException(status_code=400, detail="У вас есть активный заказ")
        
        cur.execute("""
            UPDATE courier_profiles 
            SET is_online = false,
                is_available = false,
                last_offline_at = NOW()
            WHERE user_id = %s
        """, (int(user_id),))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Вы офлайн", "is_online": False}
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/courier/update-location")
async def update_courier_location(request: Request):
    """Обновление геолокации курьера - ЧИСТЫЙ SQL"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    data = await request.json()
    lat = data.get("lat")
    lon = data.get("lon")
    
    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Latitude and longitude required")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE courier_profiles 
            SET current_lat = %s,
                current_lon = %s,
                last_location_update = NOW()
            WHERE user_id = %s
        """, (lat, lon, int(user_id)))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Location updated"}
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
# backend/main.py - добавьте поддержку Bearer токена в эндпоинт статуса

# backend/main.py - добавьте поддержку Bearer токена в эндпоинт статуса
# backend/main.py - полный эндпоинт

@app.get("/api/courier/status")
async def get_courier_status(request: Request, db: Session = Depends(get_db)):
    """Получить статус курьера"""
    
    print("🔍 GET /api/courier/status вызван")
    
    # ✅ ПРАВИЛЬНО получаем user_id из Bearer токена
    user_id = None
    
    # 1. Пробуем Authorization header
    auth_header = request.headers.get("Authorization")
    print(f"📨 Authorization header: {auth_header}")
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        print(f"🔑 Токен получен: {token[:50]}...")
        
        try:
            from jose import jwt
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            print(f"✅ user_id из токена: {user_id}")
        except jwt.ExpiredSignatureError:
            print("❌ Токен просрочен")
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Token expired"}
            )
        except jwt.JWTError as e:
            print(f"❌ Ошибка декодирования: {e}")
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": f"Invalid token: {str(e)}"}
            )
        except Exception as e:
            print(f"❌ Другая ошибка: {e}")
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": str(e)}
            )
    
    # 2. Fallback на cookie (для обратной совместимости)
    if not user_id:
        user_id = request.cookies.get("user_id")
        print(f"🍪 user_id из cookie: {user_id}")
    
    if not user_id:
        print("❌ Нет user_id нигде")
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Not authenticated"}
        )
    
    # Получаем профиль курьера
    courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
    
    if not courier:
        print(f"❌ Курьер с user_id={user_id} не найден")
        return JSONResponse(
            status_code=404,
            content={"success": False, "detail": "Courier not found"}
        )
    
    print(f"✅ Курьер найден: {courier.first_name} {courier.last_name}")
    
    return {
        "success": True,
        "is_online": courier.is_online,
        "is_available": courier.is_available,
        "is_verified": courier.is_verified,
        "current_order_id": courier.current_order_id,
        "current_order_status": courier.current_order_status,
        "courier_type": courier.courier_type,
        "rating": courier.rating,
        "total_deliveries": courier.total_deliveries,
        "first_name": courier.first_name,
        "last_name": courier.last_name,
        "phone": courier.phone
    }


@app.get("/api/couriers/online")
async def get_online_couriers(db: Session = Depends(get_db)):
    """Получить всех онлайн курьеров (для карты)"""
    couriers = db.query(CourierProfile).filter(
        CourierProfile.is_online == True,
        CourierProfile.is_verified == True
    ).all()
    
    result = []
    for c in couriers:
        result.append({
            "id": c.id,
            "user_id": c.user_id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "phone": c.phone,
            "courier_type": c.courier_type,
            "car_model": c.car_model,
            "car_number": c.car_number,
            "current_lat": c.current_lat,
            "current_lon": c.current_lon,
            "current_order_status": c.current_order_status,
            "rating": c.rating,
            "total_deliveries": c.total_deliveries
        })
    
    return {"success": True, "couriers": result}
from datetime import datetime, timezone  # ← ДОБАВЬ В НАЧАЛО

@app.post("/api/courier/complete-order/{order_id}")
async def complete_order(order_id: int, request: Request):
    """Курьер отдал заказ клиенту → статус 'waiting_confirmation'"""
    
    print("=" * 50)
    print(f"📦 ЗАВЕРШЕНИЕ ДОСТАВКИ - ЗАКАЗ #{order_id}")
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем заказ
        cur.execute("""
            SELECT id, assigned_courier_id, user_id, order_number, amount_paid, status
            FROM orders 
            WHERE id = %s
        """, (order_id,))
        
        order = cur.fetchone()
        if not order:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Order not found")
        
        assigned_courier = order[1]
        customer_user_id = order[2]
        order_number = order[3]
        amount_paid = order[4]
        current_status = order[5]
        
        print(f"📋 Заказ #{order_id}: статус={current_status}")
        
        if assigned_courier != int(user_id):
            cur.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Order not assigned to you")
        
        # ✅ Проверяем статус
        if current_status == 'delivered':
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Заказ уже доставлен", "status": "delivered"}
            )
        
        if current_status == 'cancelled':
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Заказ отменен", "status": "cancelled"}
            )
        
        if current_status == 'waiting_confirmation':
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Заказ уже ожидает подтверждения", "status": "waiting_confirmation"}
            )
        
        # ✅ Проверяем что заказ в статусе 'nearby'
        if current_status != 'nearby':
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={
                    "success": False, 
                    "message": f"Заказ не в статусе 'nearby'. Текущий статус: {current_status}",
                    "status": current_status
                }
            )
        
        # ✅ МЕНЯЕМ СТАТУС НА 'waiting_confirmation' (ПРОСТАЯ СТРОКА!)
        cur.execute("""
            UPDATE orders 
            SET status = 'waiting_confirmation'
            WHERE id = %s
        """, (order_id,))
        
        # Добавляем в трекинг
        cur.execute("""
            INSERT INTO order_tracking 
            (order_id, status, message, created_at)
            VALUES (%s, 'waiting_confirmation', 'Курьер отдал заказ клиенту, ожидается подтверждение', NOW())
        """, (order_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Заказ #{order_id} передан клиенту, статус: waiting_confirmation")
        
        # Уведомление клиенту
        try:
            if customer_user_id:
                await manager.send_to_user(customer_user_id, {
                    "type": "delivery_waiting_confirmation",
                    "data": {
                        "order_id": order_id,
                        "order_number": order_number,
                        "status": "waiting_confirmation",
                        "message": "Курьер передал вам заказ! Подтвердите получение.",
                        "amount": float(amount_paid) if amount_paid else 0,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                })
        except:
            pass
        
        return {
            "success": True,
            "message": "Заказ передан клиенту. Ожидается подтверждение.",
            "status": "waiting_confirmation"
        }
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        print(f"❌ Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    


# backend/main.py - ДОБАВИТЬ ЭТИ ЭНДПОИНТЫ

import random
import smtplib
from email.mime.text import MIMEText

# Хранилище для кодов (в production использовать Redis)
reset_codes = {}

# ✅ Отправка кода
@app.post("/api/auth/send-reset-code")
async def send_reset_code(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    phone = data.get("phone")
    
    if not phone:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Телефон обязателен"}
        )
    
    # Проверяем, существует ли пользователь
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Пользователь не найден"}
        )
    
    # Генерируем 6-значный код
    code = str(random.randint(100000, 999999))
    
    # Сохраняем код
    reset_codes[phone] = {
        "code": code,
        "expires": datetime.utcnow() + timedelta(minutes=5),
        "attempts": 0
    }
    
    print(f"🔐 Код для {phone}: {code}")
    
    # Отправляем SMS (здесь заглушка)
    # В реальном проекте используйте Twilio или аналоги
    try:
        # await send_sms(phone, f"Ваш код восстановления: {code}")
        pass
    except Exception as e:
        print(f"Ошибка отправки SMS: {e}")
    
    return {
        "success": True,
        "message": "Код отправлен",
        "debug_code": code  # Для тестирования
    }

# ✅ Сброс пароля
# ============ ВОССТАНОВЛЕНИЕ ПАРОЛЯ ============

import random
import secrets
from datetime import datetime, timedelta

# Хранилище для запросов на восстановление


# ✅ 1. КЛИЕНТ ЗАПРАШИВАЕТ ВОССТАНОВЛЕНИЕ ПАРОЛЯ
@app.post("/api/auth/request-password-reset")
async def request_password_reset(request: Request, db: Session = Depends(get_db)):
    """Клиент запрашивает восстановление пароля (БЕЗ КОДА В ОТВЕТЕ!)"""
    try:
        data = await request.json()
        phone = data.get("phone")
        
        if not phone:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Телефон обязателен"}
            )
        
        # Проверяем пользователя
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Пользователь не найден"}
            )
        
        # Сохраняем запрос (БЕЗ КОДА!)
        password_reset_requests[phone] = {
            "user_id": user.id,
            "expires": datetime.utcnow() + timedelta(minutes=15),
            "admin_approved": False,
            "code": None  # Код будет сгенерирован после одобрения
        }
        
        print(f"📝 ЗАПРОС НА ВОССТАНОВЛЕНИЕ: {phone}")
        
        return JSONResponse(content={
            "success": True,
            "message": "Запрос отправлен. Дождитесь одобрения администратора."
        })
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )




# ✅ 2. АДМИН ПОДТВЕРЖДАЕТ ЗАПРОС НА ВОССТАНОВЛЕНИЕ
@app.post("/api/admin/approve-password-reset")
async def admin_approve_password_reset(
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ одобряет или отклоняет запрос"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Admin only"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": f"Invalid token: {str(e)}"}
        )
    
    try:
        data = await request.json()
        phone = data.get("phone")
        approve = data.get("approve", True)
        
        if not phone:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Телефон обязателен"}
            )
        
        # formatted_phone = format_phone_number(phone)
        formatted_phone = phone
        if formatted_phone not in password_reset_requests:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Запрос не найден"}
            )
        
        request_data = password_reset_requests[formatted_phone]
        
        if request_data["expires"] < datetime.utcnow():
            del password_reset_requests[formatted_phone]
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Запрос истек"}
            )
        
        if approve:
          code = str(random.randint(100000, 999999))
          reset_token = secrets.token_urlsafe(32)
        
          request_data["admin_approved"] = True
          request_data["code"] = code
          request_data["reset_token"] = reset_token
          password_reset_requests[phone] = request_data
        
          print(f"🔐 КОД ДЛЯ {phone}: {code}")
        
          # ✅ ОТПРАВЛЯЕМ КОД В ОТВЕТЕ (для теста)
          return JSONResponse(content={
            "success": True,
            "message": "Запрос одобрен",
            "debug_code": code  # <--- ДОБАВЬ ЭТУ СТРОЧКУ
        })
        else:
            del password_reset_requests[formatted_phone]
            return JSONResponse(content={
                "success": True,
                "message": "Запрос отклонен"
            })
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

# ✅ 3. КЛИЕНТ ПОДТВЕРЖДАЕТ КОД
@app.post("/api/auth/verify-reset-code")
async def verify_reset_code(request: Request, db: Session = Depends(get_db)):
    """Клиент проверяет код (который пришел после одобрения)"""
    try:
        data = await request.json()
        phone = data.get("phone")
        code = data.get("code")
        
        if not phone or not code:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Телефон и код обязательны"}
            )
        
        if phone not in password_reset_requests:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Запрос не найден"}
            )
        
        request_data = password_reset_requests[phone]
        
        if request_data["expires"] < datetime.utcnow():
            del password_reset_requests[phone]
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Запрос истек"}
            )
        
        if not request_data["admin_approved"]:
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Запрос еще не одобрен администратором"}
            )
        
        if request_data["code"] != code:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Неверный код"}
            )
        
        return JSONResponse(content={
            "success": True,
            "message": "Код подтвержден",
            "reset_token": request_data.get("reset_token")
        })
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

@app.post("/api/admin/approve-password-reset")
async def admin_approve_password_reset(request: Request, db: Session = Depends(get_db)):
    """Админ одобряет запрос на восстановление пароля"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Admin only"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": f"Invalid token: {str(e)}"}
        )
    
    try:
        data = await request.json()
        phone = data.get("phone")
        approve = data.get("approve", True)
        
        if not phone:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Телефон обязателен"}
            )
        
        if phone not in password_reset_requests:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Запрос не найден"}
            )
        
        request_data = password_reset_requests[phone]
        
        if request_data["expires"] < datetime.utcnow():
            del password_reset_requests[phone]
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Запрос истек"}
            )
        
        if approve:
            import random
            import secrets
            code = str(random.randint(100000, 999999))
            reset_token = secrets.token_urlsafe(32)
            
            request_data["admin_approved"] = True
            request_data["code"] = code
            request_data["reset_token"] = reset_token
            password_reset_requests[phone] = request_data
            
            print(f"🔐 КОД ДЛЯ {phone}: {code}")
            
            return JSONResponse(content={
                "success": True,
                "message": "Запрос одобрен",
                "debug_code": code
            })
        else:
            del password_reset_requests[phone]
            return JSONResponse(content={
                "success": True,
                "message": "Запрос отклонен"
            })
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )
# ✅ 4. СБРОС ПАРОЛЯ
@app.post("/api/auth/reset-password")
async def reset_password(request: Request, db: Session = Depends(get_db)):
    """Сброс пароля после подтверждения кода"""
    try:
        data = await request.json()
        phone = data.get("phone")
        code = data.get("code")
        new_password = data.get("new_password")
        reset_token = data.get("reset_token")
        
        if not phone or not code or not new_password:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Все поля обязательны"}
            )
        
        if len(new_password) < 6:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Пароль минимум 6 символов"}
            )
        
        if phone not in password_reset_requests:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Запрос не найден"}
            )
        
        request_data = password_reset_requests[phone]
        
        if request_data["expires"] < datetime.utcnow():
            del password_reset_requests[phone]
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Запрос истек"}
            )
        
        if not request_data["admin_approved"]:
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Запрос не одобрен администратором"}
            )
        
        if request_data["code"] != code:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Неверный код"}
            )
        
        if reset_token != request_data.get("reset_token"):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Неверный токен"}
            )
        
        import hashlib
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        user = db.query(User).filter(User.id == request_data["user_id"]).first()
        if user:
            user.password = password_hash
            db.commit()
        
        del password_reset_requests[phone]
        
        return JSONResponse(content={
            "success": True,
            "message": "Пароль изменен"
        })
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )



# ✅ 5. АДМИН ПОЛУЧАЕТ ВСЕ ЗАПРОСЫ НА ВОССТАНОВЛЕНИЕ
@app.get("/api/admin/password-reset-requests")
async def admin_get_password_reset_requests(request: Request, db: Session = Depends(get_db)):
    """Админ получает список запросов"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Admin only"}
            )
    except:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Invalid token"}
        )
    
    requests_list = []
    for phone, data in password_reset_requests.items():
        if data["expires"] > datetime.utcnow():
            requests_list.append({
                "phone": phone,
                "user_id": data["user_id"],
                "code": data.get("code"),  # Может быть None (пока не одобрили)
                "admin_approved": data["admin_approved"],
                "status": "approved" if data["admin_approved"] else "pending",
                "time_left": int((data["expires"] - datetime.utcnow()).total_seconds() / 60)
            })
    
    return JSONResponse(content={"success": True, "requests": requests_list})



# backend/main.py - ИСПРАВЛЕННЫЙ ЛОГИН КУРЬЕРА
from datetime import datetime, timedelta, timezone  # ← ДОБАВЬ В НАЧАЛО

@app.post("/api/courier/login")
async def courier_login(request: Request, db: Session = Depends(get_db)):
    """Логин для курьеров с JWT токеном"""
    try:
        data = await request.json()
        phone = data.get("phone", "").strip()
        password = data.get("password", "")
        
        print(f"🔐 Попытка входа курьера: {phone}")
        
        if not phone or not password:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Заполните все поля"}
            )
        
        user = db.query(User).filter(
            User.phone == phone,
            User.role == "courier"
        ).first()
        
        if not user:
            print(f"❌ Курьер не найден: {phone}")
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Неверный телефон или пароль"}
            )
        
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if user.password != password_hash:
            print(f"❌ Неверный пароль для: {phone}")
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Неверный телефон или пароль"}
            )
        
        courier = db.query(CourierProfile).filter(CourierProfile.user_id == user.id).first()
        
        if not courier:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Профиль курьера не найден"}
            )
        
        if not courier.is_verified:
            print(f"⏳ Курьер не верифицирован: {phone}")
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Ваша заявка на рассмотрении"}
            )
        
        if not user.is_active:
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Аккаунт не активирован"}
            )
        
        print(f"✅ Успешный вход курьера: {phone}")
        
        from jose import jwt
        
        # ✅ ИСПРАВЛЕНО: datetime.now(timezone.utc) ВМЕСТО datetime.utcnow()
        token_data = {
            "sub": str(user.id),
            "role": "courier",
            "courier_id": courier.id,
            "phone": user.phone,
            "first_name": courier.first_name,
            "last_name": courier.last_name,
            "exp": datetime.now(timezone.utc) + timedelta(days=30)
        }
        
        access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "success": True,
            "message": "Вход выполнен успешно",
            "token": access_token,
            "courier": {
                "id": user.id,
                "first_name": courier.first_name,
                "last_name": courier.last_name,
                "phone": user.phone,
                "is_verified": courier.is_verified,
                "courier_type": courier.courier_type,
                "car_model": courier.car_model,
                "car_number": courier.car_number,
                "rating": courier.rating,
                "total_deliveries": courier.total_deliveries
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка логина курьера: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

@app.post("/api/couriers/find-nearest")
async def find_nearest_courier(request: Request, db: Session = Depends(get_db)):
    """Найти ближайшего свободного курьера для заказа"""
    data = await request.json()
    
    restaurant_lat = data.get("restaurant_lat")
    restaurant_lon = data.get("restaurant_lon")
    order_id = data.get("order_id")
    
    # Ищем активных и свободных курьеров
    available_couriers = db.query(CourierProfile).filter(
        CourierProfile.is_verified == True,
        CourierProfile.is_active == True,
        CourierProfile.is_available == True
    ).all()
    
    nearest_courier = None
    min_distance = float('inf')
    
    for courier in available_couriers:
        # Если у курьера есть текущая локация
        if courier.current_lat and courier.current_lon:
            distance = haversine_distance(
                restaurant_lat, restaurant_lon,
                courier.current_lat, courier.current_lon
            )
            
            # Проверяем, входит ли ресторан в радиус доставки курьера
            if distance <= courier.delivery_radius_km and distance < min_distance:
                min_distance = distance
                nearest_courier = courier
    
    if nearest_courier:
        # Рассчитываем ETA
        eta_minutes = int((min_distance / nearest_courier.speed_kmh) * 60)
        
        # Назначаем курьера на заказ
        if order_id:
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                order.assigned_courier_id = nearest_courier.user_id
                order.delivery_started_at = datetime.utcnow()
                order.delivery_deadline = datetime.utcnow() + timedelta(minutes=eta_minutes + 30)
                db.commit()
        
        return {
            "success": True,
            "courier": {
                "id": nearest_courier.id,
                "first_name": nearest_courier.first_name,
                "last_name": nearest_courier.last_name,
                "phone": nearest_courier.phone,
                "courier_type": nearest_courier.courier_type,
                "car_model": nearest_courier.car_model,
                "car_number": nearest_courier.car_number,
                "distance_km": round(min_distance, 2),
                "eta_minutes": eta_minutes,
                "rating": nearest_courier.rating
            }
        }
    else:
        return {
            "success": False,
            "message": "Нет доступных курьеров поблизости"
        }



# ============ АДМИН: УПРАВЛЕНИЕ ЗАЯВКАМИ КУРЬЕРОВ ============

@app.get("/admin/api/courier-requests")
async def admin_get_courier_requests(
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ получает список неподтвержденных курьеров"""
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Ищем курьеров, которые не подтверждены
    pending_couriers = db.query(CourierProfile).filter(
        CourierProfile.is_verified == False
    ).all()
    
    result = []
    for cp in pending_couriers:
        user = db.query(User).filter(User.id == cp.user_id).first()
        if user:
            result.append({
                "id": cp.id,
                "user_id": user.id,
                "full_name": user.full_name,
                "phone": user.phone,
                "car_model": cp.car_model,
                "car_number": cp.car_number,
                "created_at": cp.created_at.isoformat() if cp.created_at else None,
                "status": "pending"
            })
    
    return {"requests": result}


@app.get("/admin/api/verified-couriers")
async def admin_get_verified_couriers(
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ получает список подтвержденных курьеров"""
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    verified_couriers = db.query(CourierProfile).filter(
        CourierProfile.is_verified == True
    ).all()
    
    result = []
    for cp in verified_couriers:
        user = db.query(User).filter(User.id == cp.user_id).first()
        if user:
            result.append({
                "id": cp.id,
                "user_id": user.id,
                "full_name": user.full_name,
                "phone": user.phone,
                "car_model": cp.car_model,
                "car_number": cp.car_number,
                "total_deliveries": cp.total_deliveries,
                "rating": cp.rating,
                "verified_at": cp.verified_at.isoformat() if cp.verified_at else None,
                "status": "verified"
            })
    
    return {"couriers": result}

@app.post("/admin/api/courier/approve/{courier_profile_id}")
async def admin_approve_courier(
    courier_profile_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ подтверждает курьера"""
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    courier_profile = db.query(CourierProfile).filter(
        CourierProfile.id == courier_profile_id
    ).first()
    
    if not courier_profile:
        raise HTTPException(status_code=404, detail="Courier profile not found")
    
    if courier_profile.is_verified:
        raise HTTPException(status_code=400, detail="Courier already verified")
    
    # Обновляем статус
    courier_profile.is_verified = True
    courier_profile.verified_at = datetime.utcnow()
    
    # Активируем пользователя
    user = db.query(User).filter(User.id == courier_profile.user_id).first()
    if user:
        user.is_active = True
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Курьер {user.full_name if user else ''} подтвержден",
        "courier_id": courier_profile.id
    }

@app.post("/admin/api/courier/reject/{courier_profile_id}")
async def admin_reject_courier(
    courier_profile_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ отклоняет заявку курьера"""
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = await request.json()
    reason = data.get("reason", "Не указана")
    
    courier_profile = db.query(CourierProfile).filter(
        CourierProfile.id == courier_profile_id
    ).first()
    
    if not courier_profile:
        raise HTTPException(status_code=404, detail="Courier profile not found")
    
    if courier_profile.is_verified:
        raise HTTPException(status_code=400, detail="Courier already verified")
    
    # Сохраняем причину отказа
    courier_profile.rejected_reason = reason
    
    # Удаляем или помечаем как отклоненного
    user = db.query(User).filter(User.id == courier_profile.user_id).first()
    if user:
        user.is_active = False
    
    db.delete(courier_profile)
    db.delete(user)
    db.commit()
    
    return {
        "success": True,
        "message": f"Заявка курьера отклонена. Причина: {reason}"
    }



# ============ REFUND SYSTEM ============

class RefundRequest(BaseModel):
    order_id: int
    reason: str




# ============ АВТОМАТИЧЕСКОЕ НАЗНАЧЕНИЕ КУРЬЕРА ============

def find_best_courier(supplier_id: int, db: Session):
    """Находит лучшего доступного курьера (с наименьшим количеством активных заказов и самым высоким рейтингом)"""
    
    couriers = db.query(CourierProfile).filter(
        CourierProfile.supplier_id == supplier_id
    ).all()
    
    if not couriers:
        return None
    
    courier_stats = []
    for courier in couriers:
        user = db.query(User).filter(User.id == courier.user_id, User.is_active == True).first()
        if not user:
            continue
            
        active_orders_count = db.query(AssignedOrder).filter(
            AssignedOrder.courier_id == courier.user_id,
            AssignedOrder.status == "assigned"
        ).count()
        
        courier_stats.append({
            "profile": courier,
            "user": user,
            "active_orders": active_orders_count,
            "rating": courier.rating or 5.0
        })
    
    if not courier_stats:
        return None
    
    courier_stats.sort(key=lambda x: (x["active_orders"], -x["rating"]))
    
    return courier_stats[0]


# backend/main.py - добавьте в начало файла

from jose import jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("SECRET_KEY", "sarqyn-super-secret-key-2024")
ALGORITHM = "HS256"

security = HTTPBearer()

def verify_supplier_token(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Проверка JWT токена для поставщика"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        
        if role != "supplier":
            raise HTTPException(status_code=403, detail="Supplier only")
        
        # Проверяем что поставщик существует
        supplier = db.query(Supplier).filter(Supplier.user_id == int(user_id)).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return supplier
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/supplier/auto-assign-courier/{order_id}")
async def auto_assign_courier(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Автоматически назначает лучшего курьера на заказ"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        supplier_id = payload.get("supplier_id")
        if not supplier_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
        
        # Проверяем что это поставщик
        if payload.get("role") != "supplier":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Not a supplier"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        from datetime import datetime, timedelta
        
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.supplier_id == int(supplier_id)
        ).first()
        
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        # ✅ ИСПРАВЛЕНО: проверка статуса как строка (БЕЗ ENUM)
        if order.status != "confirmed":
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Order not confirmed yet. Current status: {order.status}"}
            )
        
        # Находим лучшего курьера
        best_courier_data = find_best_courier(int(supplier_id), db)
        
        if not best_courier_data:
            return {
                "success": False,
                "message": "Нет доступных курьеров. Добавьте курьера в разделе 'Курьеры'"
            }
        
        best_courier = best_courier_data["profile"]
        courier_user = best_courier_data["user"]
        
        # Создаем назначение
        assignment = AssignedOrder(
            order_id=order_id,
            courier_id=best_courier.user_id,
            status="assigned",
            assigned_at=datetime.utcnow()
        )
        db.add(assignment)
        
        # ✅ ИСПРАВЛЕНО: status = 'out_for_delivery' (строка, БЕЗ ENUM)
        order.status = "out_for_delivery"
        order.delivery_started_at = datetime.utcnow()
        order.delivery_deadline = datetime.utcnow() + timedelta(minutes=30)
        order.assigned_courier_id = best_courier.user_id
        
        # Обновляем профиль курьера
        best_courier.current_order_id = order_id
        best_courier.current_order_status = "out_for_delivery"
        best_courier.is_available = False
        best_courier.total_deliveries = (best_courier.total_deliveries or 0) + 1
        
        db.commit()
        
        print(f"✅ Автоматически назначен курьер {courier_user.full_name} на заказ #{order.order_number}")
        
        # Уведомляем через WebSocket
        try:
            await manager.broadcast({
                "type": "order_assigned",
                "order_id": order.id,
                "order_number": order.order_number,
                "courier_id": best_courier.id,
                "courier_name": f"{courier_user.full_name}"
            }, channel="orders")
        except Exception as e:
            print(f"⚠️ Ошибка отправки WebSocket: {e}")
        
        return {
            "success": True,
            "message": f"Курьер {courier_user.full_name} автоматически назначен",
            "courier": {
                "id": best_courier.id,
                "name": courier_user.full_name,
                "phone": courier_user.phone,
                "car_model": best_courier.car_model,
                "car_number": best_courier.car_number,
                "rating": best_courier.rating,
                "total_deliveries": best_courier.total_deliveries
            },
            "order": {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "delivery_deadline": order.delivery_deadline.isoformat()
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

@app.get("/admin/login")
async def admin_login_page(request: Request):
    """Страница входа в админ-панель"""
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})

# ============ ЭНДПОИНТ: API ЛОГИНА (POST) ============
@app.post("/admin/api/login")
async def admin_api_login(request: Request, db: Session = Depends(get_db)):
    """API логин для админа - возвращает JWT токен"""
    
    try:
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        
        print(f"🔐 Admin login attempt: {username}")
        
        # Ищем админа
        admin = db.query(Admin).filter(Admin.username == username).first()
        
        if not admin:
            print(f"❌ Admin not found: {username}")
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid credentials"}
            )
        
        # Проверяем пароль
        if not verify_password(password, admin.password_hash):
            print(f"❌ Wrong password for: {username}")
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid credentials"}
            )
        
        # Создаем JWT токен
        access_token = create_access_token(data={
            "sub": str(admin.id),
            "role": "admin",
            "username": admin.username
        })
        
        print(f"✅ Admin logged in: {username}, token created")
        
        return {
            "success": True,
            "token": access_token,
            "admin": {
                "id": admin.id,
                "username": admin.username
            }
        }
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

# ============ ЭНДПОИНТ: АДМИН-ПАНЕЛЬ (GET) ============
@app.get("/admin")
async def admin_panel(request: Request):
    """Админ-панель - проверяет токен из URL или sessionStorage"""
    
    token = request.query_params.get("token")
    
    if not token:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return RedirectResponse(url="/admin/login", status_code=303)
        
        return templates.TemplateResponse("admin.html", {"request": request})
        
    except Exception:
        return RedirectResponse(url="/admin/login", status_code=303)

# ============ ЭНДПОИНТ: ДАШБОРД (GET) ============
@app.get("/admin/dashboard")
async def admin_dashboard_page(request: Request):
    """Панель администратора - проверяет токен из URL"""
    
    token = request.query_params.get("token")
    
    if not token:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return RedirectResponse(url="/admin/login", status_code=303)
        
        return templates.TemplateResponse("admin.html", {"request": request})
        
    except Exception:
        return RedirectResponse(url="/admin/login", status_code=303)

# ============ ЭНДПОИНТ: ВЫХОД ============
@app.get("/admin/logout")
async def admin_logout():
    """Выход из админ-панели"""
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_id")
    return response

# ============ ЭНДПОИНТ: СТАТИСТИКА (GET) ============
@app.get("/api/admin/stats")
async def get_admin_stats(request: Request, db: Session = Depends(get_db)):
    """Получить статистику для админ-панели"""
    
    # Проверка токена
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Admin only"}
            )
    except:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Invalid token"}
        )
    
    try:
        # Считаем статистику
        total_users = db.query(User).count()
        total_suppliers = db.query(Supplier).count()
        total_orders = db.query(Order).count()
        total_bags = db.query(SurpriseBag).count()
        pending_couriers = db.query(CourierProfile).filter(CourierProfile.is_verified == False).count()
        
        # Выручка
        from sqlalchemy import func
        total_revenue = db.query(func.sum(Order.amount_paid)).filter(Order.payment_status == "paid").scalar() or 0
        
        return {
            "total_users": total_users,
            "total_suppliers": total_suppliers,
            "total_orders": total_orders,
            "total_bags": total_bags,
            "pending_couriers": pending_couriers,
            "total_revenue": float(total_revenue)
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ============ ЭНДПОИНТ: РЕДИРЕКТ С /login ============
@app.get("/login")
async def redirect_to_admin_login():
    """Редирект с /login на /admin/login"""
    return RedirectResponse(url="/admin/login", status_code=302)

@app.post("/login")
async def redirect_post_login():
    """Редирект POST запросов с /login на /admin/login"""
    return RedirectResponse(url="/admin/login", status_code=302)

@app.get("/api/supplier/available-couriers")
async def get_available_couriers(request: Request, db: Session = Depends(get_db)):
    """Получить список доступных курьеров для поставщика"""
    supplier_id = request.cookies.get("supplier_id")
    if not supplier_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    couriers = db.query(CourierProfile).filter(
        CourierProfile.supplier_id == int(supplier_id)
    ).all()
    
    result = []
    for c in couriers:
        user = db.query(User).filter(User.id == c.user_id, User.is_active == True).first()
        if user:
            active_orders = db.query(AssignedOrder).filter(
                AssignedOrder.courier_id == c.user_id,
                AssignedOrder.status == "assigned"
            ).count()
            
            result.append({
                "id": c.id,
                "user_id": user.id,
                "name": user.full_name,
                "phone": user.phone,
                "car_model": c.car_model,
                "car_number": c.car_number,
                "rating": c.rating or 5.0,
                "total_deliveries": c.total_deliveries or 0,
                "active_orders": active_orders
            })
    
    return {"couriers": result}


# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/supplier/assign-courier")
async def assign_courier_to_order(request: Request, db: Session = Depends(get_db)):
    """Ручное назначение курьера на заказ"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        supplier_id = payload.get("supplier_id")
        if not supplier_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    
    try:
        data = await request.json()
        order_id = data.get("order_id")
        courier_profile_id = data.get("courier_profile_id")
        
        if not order_id or not courier_profile_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "order_id and courier_profile_id required"}
            )
        
        # Находим заказ
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.supplier_id == int(supplier_id)
        ).first()
        
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        # ✅ ИСПРАВЛЕНО: status = 'confirmed' (строка, БЕЗ ENUM)
        if order.status != "confirmed":
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Order not confirmed yet. Current status: {order.status}"}
            )
        
        # Находим курьера
        courier_profile = db.query(CourierProfile).filter(
            CourierProfile.id == courier_profile_id,
            CourierProfile.supplier_id == int(supplier_id)
        ).first()
        
        if not courier_profile:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Courier not found"}
            )
        
        user = db.query(User).filter(User.id == courier_profile.user_id).first()
        if not user or not user.is_active:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Courier not active"}
        )
        
        from datetime import datetime, timedelta
        
        # Создаем назначение
        assignment = AssignedOrder(
            order_id=order_id,
            courier_id=courier_profile.user_id,
            status="assigned",
            assigned_at=datetime.utcnow()
        )
        db.add(assignment)
        
        # ✅ ИСПРАВЛЕНО: status = 'out_for_delivery' (строка, БЕЗ ENUM)
        order.status = "out_for_delivery"
        order.delivery_started_at = datetime.utcnow()
        order.delivery_deadline = datetime.utcnow() + timedelta(minutes=30)
        order.assigned_courier_id = courier_profile.user_id
        
        # Обновляем профиль курьера
        courier_profile.current_order_id = order_id
        courier_profile.current_order_status = "out_for_delivery"
        courier_profile.is_available = False
        courier_profile.total_deliveries = (courier_profile.total_deliveries or 0) + 1
        
        db.commit()
        
        print(f"✅ Курьер {user.full_name} назначен на заказ #{order.order_number}")
        
        return {
            "success": True,
            "message": f"Курьер {user.full_name} назначен на заказ {order.order_number}",
            "courier": {
                "id": courier_profile.id,
                "name": user.full_name,
                "phone": user.phone,
                "car_model": courier_profile.car_model,
                "car_number": courier_profile.car_number
            },
            "order": {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "delivery_deadline": order.delivery_deadline.isoformat()
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

@app.get("/api/order/{order_id}/delivery-status")
async def get_delivery_status(order_id: int, db: Session = Depends(get_db)):
    """Клиент получает информацию о курьере и доставке"""
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.assigned_courier_id:
        courier = db.query(User).filter(User.id == order.assigned_courier_id).first()
        courier_profile = db.query(CourierProfile).filter(CourierProfile.user_id == order.assigned_courier_id).first()
        
        remaining_seconds = 0
        if order.delivery_deadline:
            remaining = order.delivery_deadline - datetime.utcnow()
            remaining_seconds = max(0, int(remaining.total_seconds()))
        
        return {
            "success": True,
            "has_courier": True,
            "courier": {
                "name": courier.full_name if courier else None,
                "phone": courier.phone if courier else None,
                "car_model": courier_profile.car_model if courier_profile else None,
                "car_number": courier_profile.car_number if courier_profile else None,
                "rating": courier_profile.rating if courier_profile else None
            },
            "delivery_deadline": order.delivery_deadline.isoformat() if order.delivery_deadline else None,
            "remaining_seconds": remaining_seconds,
            "status": order.status.value if order.status else None
        }
    
    return {"success": True, "has_courier": False}


# В main.py добавьте этот эндпоинт
@app.get("/api/order/{order_id}/delivery-info")
async def get_delivery_info(order_id: int, db: Session = Depends(get_db)):
    """Клиент получает полную информацию о доставке"""
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    result = {
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status.value if order.status else "pending",
        "payment_status": order.payment_status,
        "delivery_deadline": order.delivery_deadline.isoformat() if order.delivery_deadline else None,
        "has_courier": False
    }
    
    if order.assigned_courier_id:
        courier = db.query(User).filter(User.id == order.assigned_courier_id).first()
        courier_profile = db.query(CourierProfile).filter(CourierProfile.user_id == order.assigned_courier_id).first()
        
        remaining_seconds = 0
        if order.delivery_deadline:
            remaining = order.delivery_deadline - datetime.utcnow()
            remaining_seconds = max(0, int(remaining.total_seconds()))
        
        result["has_courier"] = True
        result["courier"] = {
            "name": courier.full_name if courier else None,
            "phone": courier.phone if courier else None,
            "car_model": courier_profile.car_model if courier_profile else None,
            "car_number": courier_profile.car_number if courier_profile else None,
            "rating": courier_profile.rating if courier_profile else None
        }
        result["remaining_seconds"] = remaining_seconds
    
    return result




# ============ АДМИН: ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ============
# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/admin/api/order/{order_id}/confirm-payment")
async def admin_confirm_payment(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ подтверждает оплату и запускает доставку"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Admin only"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        if order.payment_status != "paid":
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Order not paid yet. Current status: {order.payment_status}"}
            )
        
        from datetime import datetime, timedelta
        
        # ✅ ИСПРАВЛЕНО: status = 'confirmed' (строка, БЕЗ ENUM)
        order.status = "confirmed"
        order.confirmed_at = datetime.utcnow()
        order.delivery_started_at = datetime.utcnow()
        order.delivery_deadline = datetime.utcnow() + timedelta(minutes=30)
        
        db.commit()
        
        print(f"✅ Админ подтвердил оплату заказа #{order.order_number}")
        
        return {
            "success": True,
            "message": "Payment confirmed, delivery started",
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "delivery_deadline": order.delivery_deadline.isoformat()
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

# ============ КЛИЕНТ: ПОЛУЧИЛ ЗАКАЗ ============
# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/order/{order_id}/receive")
async def customer_receive_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Клиент подтверждает, что получил заказ → статус меняется на DELIVERED"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
        
        # Проверяем что это клиент (customer)
        role = payload.get("role")
        if role != "customer":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Only customers can receive orders"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        from datetime import datetime
        
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == int(user_id)
        ).first()
        
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        # ✅ ИСПРАВЛЕНО: status = 'out_for_delivery' (строка, БЕЗ ENUM)
        if order.status != "out_for_delivery":
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Order is not in delivery. Current status: {order.status}"}
            )
        
        # Проверяем, не истек ли дедлайн
        if order.delivery_deadline and datetime.utcnow() > order.delivery_deadline:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Delivery deadline expired. Auto-refund initiated."}
            )
        
        # ✅ ИСПРАВЛЕНО: status = 'delivered' (строка, БЕЗ ENUM)
        order.status = "delivered"
        order.delivered_at = datetime.utcnow()
        
        # Освобождаем курьера
        if order.assigned_courier_id:
            db.query(CourierProfile).filter(
                CourierProfile.user_id == order.assigned_courier_id
            ).update({
                "current_order_id": None,
                "current_order_status": None,
                "is_available": True,
                "is_online": True
            })
        
        db.commit()
        
        print(f"✅ Клиент получил заказ #{order.order_number}")
        
        return {
            "success": True,
            "message": "Order received successfully",
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "delivered_at": order.delivered_at.isoformat()
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

# ============ КЛИЕНТ: ОТКАЗ ОТ ЗАКАЗА ============
# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/order/{order_id}/reject")
async def customer_reject_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Клиент отказывается от заказа → отправляет запрос админу на возврат"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
        
        # Проверяем что это клиент (customer)
        role = payload.get("role")
        if role != "customer":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Only customers can reject orders"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        data = await request.json()
        reason = data.get("reason", "Не указана")
        
        from datetime import datetime
        
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == int(user_id)
        ).first()
        
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        # ✅ ИСПРАВЛЕНО: status = 'out_for_delivery' (строка, БЕЗ ENUM)
        if order.status != "out_for_delivery":
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Cannot reject order at this stage. Current status: {order.status}"}
            )
        
        # Создаем запрос на возврат
        order.refund_requested_by_customer = True
        order.refund_requested_at = datetime.utcnow()
        order.refund_reason = reason
        order.refund_status = "requested"
        
        db.commit()
        
        print(f"📝 Клиент запросил возврат для заказа #{order.order_number}: {reason}")
        
        return {
            "success": True,
            "message": "Refund requested. Admin will process.",
            "refund_request_id": order.id,
            "order_id": order.id,
            "order_number": order.order_number,
            "refund_requested_at": order.refund_requested_at.isoformat()
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )
@app.delete("/api/supplier/clear-inactive-bags")
async def clear_inactive_surprise_bags(
    request: Request,
    db: Session = Depends(get_db)
):
    """Удаление только НЕАКТИВНЫХ сюрприз-пакетов поставщика"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"success": False, "message": "Unauthorized"})
    
    token = auth_header.split(" ")[1]
    
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        from backend.models import Supplier, SurpriseBag, CartItem, Order, TemporaryReservation
        
        supplier = db.query(Supplier).filter(Supplier.user_id == int(user_id)).first()
        if not supplier:
            return JSONResponse(status_code=404, content={"success": False, "message": "Supplier not found"})
        
        # Находим ТОЛЬКО НЕАКТИВНЫЕ сюрпризы
        inactive_bags = db.query(SurpriseBag).filter(
            SurpriseBag.supplier_id == supplier.id,
            SurpriseBag.is_active == False
        ).all()
        
        if not inactive_bags:
            inactive_bags = db.query(SurpriseBag).filter(
                SurpriseBag.supplier_id == supplier.id,
                SurpriseBag.is_active == 0
            ).all()
        
        if not inactive_bags:
            return JSONResponse(status_code=200, content={
                "success": True, 
                "message": "Нет неактивных сюрпризов для удаления", 
                "deleted_count": 0
            })
        
        inactive_bag_ids = [bag.id for bag in inactive_bags]
        
        # 1. Удаляем временные резервации
        deleted_temp_res = db.query(TemporaryReservation).filter(TemporaryReservation.bag_id.in_(inactive_bag_ids)).delete(synchronize_session=False)
        
        # 2. Удаляем из корзины
        deleted_cart_items = db.query(CartItem).filter(CartItem.surprise_bag_id.in_(inactive_bag_ids)).delete(synchronize_session=False)
        
        # 3. Обновляем заказы
        db.query(Order).filter(Order.surprise_bag_id.in_(inactive_bag_ids)).update(
            {Order.surprise_bag_id: None}, 
            synchronize_session=False
        )
        
        # 4. Удаляем сюрпризы
        deleted_count = 0
        for bag in inactive_bags:
            db.delete(bag)
            deleted_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Удалено {deleted_count} неактивных сюрпризов, {deleted_cart_items} из корзины, {deleted_temp_res} резерваций",
            "deleted_count": deleted_count,
            "deleted_cart_items": deleted_cart_items,
            "deleted_temp_res": deleted_temp_res
        }
        
    except Exception as e:
        print(f"Error clearing inactive bags: {e}")
        db.rollback()
        return JSONResponse(status_code=500, content={"success": False, "message": f"Error: {str(e)}"})
    # backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/admin/api/order/{order_id}/approve-refund")
async def admin_approve_refund(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ подтверждает возврат денег (деньги отправлены клиенту)"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Admin only"}
            )
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        import secrets
        from datetime import datetime
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        if order.refund_status != "requested":
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"No refund request found. Current status: {order.refund_status}"}
            )
        
        # Выполняем возврат
        order.refund_status = "completed"
        order.refund_processed_at = datetime.utcnow()
        order.refund_amount = order.amount_paid
        order.payment_status = "refunded"
        
        # ✅ ИСПРАВЛЕНО: status = 'cancelled' (строка, БЕЗ ENUM)
        order.status = "cancelled"
        order.cancelled_at = datetime.utcnow()
        order.refund_transaction_id = f"REF-{secrets.token_hex(8).upper()}"
        
        # ✅ ОСВОБОЖДАЕМ КУРЬЕРА (если был назначен)
        if order.assigned_courier_id:
            db.query(CourierProfile).filter(
                CourierProfile.user_id == order.assigned_courier_id
            ).update({
                "current_order_id": None,
                "current_order_status": None,
                "is_available": True,
                "is_online": True
            })
            print(f"✅ Курьер освобожден от заказа #{order_id}")
        
        # Возвращаем количество сюрприза
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
        if bag:
            bag.available_quantity += 1
            if bag.available_quantity > 0:
                bag.is_active = True
            print(f"📦 Восстановлен товар '{bag.name}', теперь {bag.available_quantity} шт.")
        
        db.commit()
        
        print(f"✅ Админ одобрил возврат для заказа #{order.order_number}")
        
        return {
            "success": True,
            "message": f"Refund approved for order {order.order_number}",
            "order_id": order.id,
            "order_number": order.order_number,
            "refund_amount": order.refund_amount,
            "refund_transaction_id": order.refund_transaction_id,
            "refund_processed_at": order.refund_processed_at.isoformat(),
            "status": order.status
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

# ============ АДМИН: ОТКЛОНИТЬ ВОЗВРАТ ============
@app.post("/admin/api/order/{order_id}/reject-refund")
async def admin_reject_refund(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ отклоняет запрос на возврат"""
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = await request.json()
    reject_reason = data.get("reason", "No reason provided")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.refund_status != "requested":
        raise HTTPException(status_code=400, detail="No refund request found")
    
    order.refund_status = "rejected"
    order.refund_reason = f"{order.refund_reason}\nОтказ: {reject_reason}"
    
    db.commit()
    
    return {"success": True, "message": "Refund request rejected"}


# ============ АВТОМАТИЧЕСКИЙ ВОЗВРАТ ПО ТАЙМЕРУ ============
# backend/main.py - ИСПРАВЛЕННАЯ ФУНКЦИЯ

async def auto_refund_on_deadline():
    """Каждую минуту проверяем: если 30 минут истекли и клиент не подтвердил получение → авто-возврат"""
    while True:
        try:
            await asyncio.sleep(60)  # Каждую минуту
            
            db = SessionLocal()
            now = datetime.utcnow()
            
            # ✅ ИСПРАВЛЕНО: status = 'out_for_delivery' (строка, БЕЗ ENUM)
            expired_orders = db.query(Order).filter(
                Order.status == "out_for_delivery",
                Order.delivery_deadline <= now,
                Order.auto_refund_processed == False
            ).all()
            
            if expired_orders:
                print(f"⏰ Найдено {len(expired_orders)} заказов с истекшим дедлайном")
            
            for order in expired_orders:
                try:
                    print(f"⏰ АВТО-ВОЗВРАТ: Заказ {order.order_number} не получен за 30 минут")
                    
                    # ✅ ИСПРАВЛЕНО: status = 'cancelled' (строка, БЕЗ ENUM)
                    order.auto_refund_processed = True
                    order.refund_status = "completed"
                    order.refund_processed_at = now
                    order.refund_amount = order.amount_paid
                    order.payment_status = "refunded"
                    order.status = "cancelled"
                    order.cancelled_at = now
                    order.refund_transaction_id = f"AUTO-REF-{secrets.token_hex(8).upper()}"
                    order.refund_reason = "Автоматический возврат: заказ не получен в течение 30 минут"
                    
                    # ✅ ОСВОБОЖДАЕМ КУРЬЕРА (если был назначен)
                    if order.assigned_courier_id:
                        db.query(CourierProfile).filter(
                            CourierProfile.user_id == order.assigned_courier_id
                        ).update({
                            "current_order_id": None,
                            "current_order_status": None,
                            "is_available": True,
                            "is_online": True
                        })
                        print(f"✅ Курьер освобожден от заказа #{order.id}")
                    
                    # ✅ ВОЗВРАЩАЕМ ТОВАР
                    bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
                    if bag:
                        bag.available_quantity += 1
                        if bag.available_quantity > 0:
                            bag.is_active = True
                        print(f"📦 Восстановлен товар '{bag.name}', теперь {bag.available_quantity} шт.")
                    
                    db.commit()
                    
                    # Уведомление через WebSocket
                    try:
                        await manager.broadcast({
                            "type": "auto_refund",
                            "order_id": order.id,
                            "order_number": order.order_number,
                            "amount": order.amount_paid,
                            "message": "Заказ не получен вовремя. Деньги возвращены."
                        })
                    except Exception as e:
                        print(f"⚠️ Ошибка отправки WebSocket: {e}")
                    
                except Exception as e:
                    print(f"❌ Ошибка при обработке заказа {order.id}: {e}")
                    db.rollback()
            
            db.close()
            
        except Exception as e:
            print(f"❌ Ошибка auto_refund: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(5)  # Пауза перед повторной попыткой
# backend/main.py - добавьте фоновую задачу

import asyncio
from datetime import datetime, timedelta
import gc
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

async def cleanup_expired_reservations():
    """Каждую минуту проверяем истекшие резервации и возвращаем товары"""
    print("🟢 cleanup_expired_reservations ЗАПУЩЕНА")
    
    # Счетчик итераций для периодического GC
    iteration = 0
    
    while True:
        db = None
        try:
            db = SessionLocal()
            now = datetime.utcnow()
            
            # Находим все истекшие неоплаченные резервации
            expired = db.query(TemporaryReservation).filter(
                TemporaryReservation.is_paid == False,
                TemporaryReservation.expires_at < now
            ).all()
            
            if expired:
                print(f"🔍 Найдено {len(expired)} истекших резерваций")
                
                for res in expired:
                    try:
                        bag = db.query(SurpriseBag).filter(SurpriseBag.id == res.bag_id).first()
                        if bag:
                            bag.available_quantity += res.quantity
                            bag.is_active = True
                            print(f"✅ Товар '{bag.name}' ID:{bag.id} восстановлен: +{res.quantity}, теперь {bag.available_quantity}")
                            
                            # WebSocket уведомление (не забываем await)
                            await manager.broadcast({
                                "type": "bag_quantity_updated",
                                "data": {
                                    "bag_id": bag.id,
                                    "available_quantity": bag.available_quantity,
                                    "is_active": bag.is_active
                                }
                            }, channel="surprise_bags")
                        
                        # Удаляем из корзины пользователя
                        cart_item = db.query(CartItem).filter(
                            CartItem.user_id == res.user_id,
                            CartItem.surprise_bag_id == res.bag_id
                        ).first()
                        
                        if cart_item:
                            if cart_item.quantity > res.quantity:
                                cart_item.quantity -= res.quantity
                            else:
                                db.delete(cart_item)
                        
                        db.delete(res)
                        
                    except Exception as e:
                        print(f"❌ Ошибка при обработке резервации {res.id}: {e}")
                        db.rollback()
                        continue
                
                db.commit()
                print(f"✅ Обработано {len(expired)} резерваций")
            
            # ✅ Периодический сбор мусора (каждые 10 итераций ~ 10 минут)
            iteration += 1
            if iteration % 10 == 0:
                gc.collect()
                print(f"🧹 Garbage collection выполнена")
            
        except Exception as e:
            print(f"❌ Ошибка в cleanup_expired_reservations: {e}")
            if db:
                db.rollback()
        finally:
            # ✅ ВСЕГДА закрываем соединение с БД
            if db:
                db.close()
        
        # Пауза 60 секунд
        await asyncio.sleep(60)

# backend/main.py - добавьте в начало файла
import psutil
import gc

async def memory_monitor():
    """Мониторинг памяти каждые 5 минут"""
    while True:
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"📊 Memory usage: {memory_mb:.2f} MB / 512 MB")
            
            if memory_mb > 450:
                print(f"⚠️ High memory usage! Forcing GC...")
                gc.collect()
                
        except Exception as e:
            print(f"❌ Memory monitor error: {e}")
        
        await asyncio.sleep(300)  # 5 минут


@app.get("/api/debug/bags")
async def debug_all_bags(db: Session = Depends(get_db)):
    """Проверить все сюрпризы в БД"""
    bags = db.query(SurpriseBag).all()
    
    result = []
    for bag in bags:
        result.append({
            "id": bag.id,
            "name": bag.name,
            "available_quantity": bag.available_quantity,
            "is_active": bag.is_active
        })
    
    print(f"🔍 DEBUG: Найдено {len(result)} сюрпризов")
    for bag in result:
        print(f"  - {bag['name']}: {bag['available_quantity']} шт., active={bag['is_active']}")
    
    return {"bags": result}

# backend/main.py - добавьте

@app.post("/api/admin/force-cleanup")
async def force_cleanup(request: Request, db: Session = Depends(get_db)):
    admin_id = request.cookies.get("admin_id")
    if not admin_id:
        return {"error": "Not admin"}
    
    now = datetime.utcnow()
    expired = db.query(TemporaryReservation).filter(
        TemporaryReservation.is_paid == False,
        TemporaryReservation.expires_at <= now
    ).all()
    
    for res in expired:
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == res.bag_id).first()
        if bag:
            bag.available_quantity += res.quantity
            bag.is_active = True
        db.delete(res)
    
    db.commit()
    return {"message": f"Очищено {len(expired)} резерваций"}


@app.get("/api/debug/bag/{bag_id}")
async def debug_bag(bag_id: int, db: Session = Depends(get_db)):
    """Проверить конкретный сюрприз"""
    bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
    
    if not bag:
        return {"error": "Bag not found"}
    
    return {
        "id": bag.id,
        "name": bag.name,
        "available_quantity": bag.available_quantity,
        "is_active": bag.is_active,
        "original_price": bag.original_price,
        "discounted_price": bag.discounted_price
    }
# backend/main.py - при успешной оплате
# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/payment/confirm-reservation")
async def confirm_reservation(request: Request, db: Session = Depends(get_db)):
    """Подтверждение резервации после успешной оплаты"""
    
    # ✅ Проверяем авторизацию
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        import secrets
        from datetime import datetime
        
        data = await request.json()
        reservation_id = data.get("reservation_id")
        
        if not reservation_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "reservation_id is required"}
            )
        
        reservation = db.query(TemporaryReservation).filter(
            TemporaryReservation.id == reservation_id,
            TemporaryReservation.user_id == int(user_id)
        ).first()
        
        if not reservation:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Резервация не найдена"}
            )
        
        # Проверяем не истекла ли резервация
        if reservation.expires_at < datetime.utcnow():
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Резервация истекла"}
            )
        
        # Помечаем как оплаченную
        reservation.is_paid = True
        
        # Получаем сюрприз
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == reservation.bag_id).first()
        
        if not bag:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Сюрприз не найден"}
            )
        
        # ✅ ИСПРАВЛЕНО: status = 'confirmed' (строка, БЕЗ ENUM)
        order = Order(
            user_id=reservation.user_id,
            supplier_id=bag.supplier_id,
            surprise_bag_id=bag.id,
            order_number=f"ORD-{secrets.token_hex(4).upper()}",
            status="confirmed",
            amount_paid=bag.discounted_price * reservation.quantity,
            created_at=datetime.utcnow(),
            confirmed_at=datetime.utcnow()
        )
        db.add(order)
        db.flush()
        
        # Удаляем из корзины
        cart_item = db.query(CartItem).filter(
            CartItem.user_id == reservation.user_id,
            CartItem.surprise_bag_id == reservation.bag_id
        ).first()
        if cart_item:
            db.delete(cart_item)
        
        db.commit()
        
        print(f"✅ Оплата подтверждена для резервации #{reservation_id}, создан заказ #{order.order_number}")
        
        return {
            "success": True,
            "message": "Оплата подтверждена",
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )
# # Запускаем фоновую задачу при старте приложения
# backend/main.py - добавьте в конец файла

@app.post("/api/admin/fix-all-bags")
async def fix_all_bags(request: Request, db: Session = Depends(get_db)):
    """Восстановить ВСЕ товары (для админов)"""
    admin_id = request.cookies.get("admin_id")
    if not admin_id:
        return {"error": "Not admin"}
    
    # Восстанавливаем ВСЕ товары
    bags = db.query(SurpriseBag).all()
    fixed_count = 0
    
    for bag in bags:
        if bag.available_quantity == 0:
            bag.available_quantity = 10
            bag.is_active = True
            fixed_count += 1
            print(f"✅ Восстановлен товар #{bag.id}: {bag.name}")
    
    # Удаляем ВСЕ неоплаченные резервации
    deleted = db.query(TemporaryReservation).filter(
        TemporaryReservation.is_paid == False
    ).delete()
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Восстановлено {fixed_count} товаров, удалено {deleted} резерваций"
    }


@app.on_event("startup")
async def startup_event():
    print("🚀 ЗАПУСК СЕРВЕРА")
    
    # Запускаем фоновые задачи
    asyncio.create_task(cleanup_expired_reservations())
    asyncio.create_task(memory_monitor())  # ✅ Добавьте это
    asyncio.create_task(auto_cleanup_cancelled_orders()) 
    print("✅ Все фоновые задачи запущены")

@app.post("/api/refund/request")
async def request_refund(
    request: Request,
    refund_data: RefundRequest,
    db: Session = Depends(get_db)
):
    """Клиент запрашивает возврат денег"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    order = db.query(Order).filter(
        Order.id == refund_data.order_id,
        Order.user_id == int(user_id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Проверки
    if order.payment_status != "paid":
        raise HTTPException(status_code=400, detail="Order not paid yet")
    
    if order.refund_status != "none":
        raise HTTPException(status_code=400, detail="Refund already requested or processed")
    
    # Проверка времени (возврат возможен только в течение 1 часа после оплаты)
    if order.paid_at and (datetime.utcnow() - order.paid_at).total_seconds() > 3600:
        raise HTTPException(status_code=400, detail="Refund period expired (1 hour)")
    
    # Создаем запрос на возврат
    order.refund_status = "requested"
    order.refund_requested_at = datetime.utcnow()
    order.refund_reason = refund_data.reason
    
    db.commit()
    
    return {
        "success": True,
        "message": "Refund requested. Admin will process it shortly.",
        "refund_id": order.id
    }

# Админ просматривает все запросы на возврат
@app.get("/admin/api/refund/requests")
async def admin_get_refund_requests(
    request: Request,
    db: Session = Depends(get_db)
):
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    orders = db.query(Order).filter(
        Order.refund_status.in_(["requested", "processing"])
    ).all()
    
    result = []
    for order in orders:
        user = db.query(User).filter(User.id == order.user_id).first()
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
        
        result.append({
            "order_id": order.id,
            "order_number": order.order_number,
            "user_name": user.full_name if user else "Unknown",
            "user_phone": user.phone if user else "—",
            "amount": order.amount_paid or 0,
            "refund_status": order.refund_status,
            "refund_reason": order.refund_reason,
            "requested_at": order.refund_requested_at.isoformat() if order.refund_requested_at else None,
            "bag_name": bag.name if bag else "Surprise Bag"
        })
    
    return {"requests": result}

# Админ обрабатывает возврат (подтверждает)
# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/admin/api/refund/approve/{order_id}")
async def admin_approve_refund(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ одобряет возврат денег клиенту"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Admin only"}
            )
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        import secrets
        from datetime import datetime
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        if order.refund_status not in ["requested", "processing"]:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Refund not requested or already processed. Current status: {order.refund_status}"}
            )
        
        # ========== ИМИТАЦИЯ ВОЗВРАТА ДЕНЕГ ==========
        # В реальном проекте здесь будет вызов API банка
        # await bank_api.refund(order.payment_id, order.amount_paid)
        
        # ✅ ИСПРАВЛЕНО: status = 'cancelled' (строка, БЕЗ ENUM)
        order.refund_status = "completed"
        order.refund_processed_at = datetime.utcnow()
        order.refund_amount = order.amount_paid
        order.payment_status = "refunded"
        order.status = "cancelled"
        order.cancelled_at = datetime.utcnow()
        order.refund_transaction_id = f"REF-{secrets.token_hex(8).upper()}"
        
        # ✅ ОСВОБОЖДАЕМ КУРЬЕРА (если был назначен)
        if order.assigned_courier_id:
            db.query(CourierProfile).filter(
                CourierProfile.user_id == order.assigned_courier_id
            ).update({
                "current_order_id": None,
                "current_order_status": None,
                "is_available": True,
                "is_online": True
            })
            print(f"✅ Курьер освобожден от заказа #{order_id}")
        
        # ✅ ВОЗВРАЩАЕМ ТОВАР
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
        if bag:
            bag.available_quantity += 1
            if bag.available_quantity > 0:
                bag.is_active = True
            print(f"📦 Восстановлен товар '{bag.name}', теперь {bag.available_quantity} шт.")
        
        db.commit()
        
        print(f"✅ Админ одобрил возврат для заказа #{order.order_number}")
        
        return {
            "success": True,
            "message": f"Refund approved for order {order.order_number}",
            "order_id": order.id,
            "order_number": order.order_number,
            "refund_amount": order.refund_amount,
            "refund_transaction_id": order.refund_transaction_id,
            "refund_processed_at": order.refund_processed_at.isoformat(),
            "status": order.status
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )
# Админ отклоняет возврат
@app.post("/admin/api/refund/reject/{order_id}")
async def admin_reject_refund(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = await request.json()
    reject_reason = data.get("reason", "No reason provided")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.refund_status != "requested":
        raise HTTPException(status_code=400, detail="Refund not requested")
    
    order.refund_status = "rejected"
    order.refund_reason = f"{order.refund_reason}\nRejection reason: {reject_reason}"
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Refund rejected for order {order.order_number}"
    }

# BACKEND WITH BOOKING
# ============ АДМИН-ПАНЕЛЬ (НАЧАЛО) ============

from backend.models import Admin

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()



# ⚠️ ВАШИ ДАННЫЕ (измените перед запуском) ⚠️
MY_LOGIN = "ACCOUNTA@#$26"        # ← ВАШ ЛОГИН
MY_PASSWORD = "CEVONICQW%&%y*"  # ← ВАШ ПАРОЛЬ

def create_my_admin():
    """Создает админа ТОЛЬКО при ПЕРВОМ запуске"""
    db = SessionLocal()
    try:
        # Проверяем, есть ли вообще админы
        admin_exists = db.query(Admin).first()
        
        if not admin_exists:
            admin = Admin(
                username=MY_LOGIN,
                password_hash=hash_password(MY_PASSWORD)
            )
            db.add(admin)
            db.commit()
            print("\n" + "="*50)
            print("✅ АДМИН-ПАНЕЛЬ АКТИВИРОВАНА!")
            print(f"🔐 Логин: {MY_LOGIN}")
            print(f"🔐 Пароль: {MY_PASSWORD}")
            print("⚠️ ЗАПОМНИТЕ ПАРОЛЬ! ВОССТАНОВИТЬ НЕВОЗМОЖНО!")
            print("="*50 + "\n")
        else:
            print("✅ Админ уже существует. Пропускаем создание.")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()

# ВЫЗЫВАЕМ (после создания таблиц)
create_my_admin()

# ============ СЕССИИ АДМИНОВ ============



admin_sessions = {}

def get_current_admin(request: Request):
    token = request.cookies.get("admin_token")
    if not token or token not in admin_sessions:
        return None
    session = admin_sessions[token]
    if session["expires_at"] < datetime.utcnow():
        del admin_sessions[token]
        return None
    return session

# ============ СТРАНИЦА ВХОДА ============
# backend/main.py


SECRET_KEY = os.getenv("SECRET_KEY", "sarqyn-super-secret-key-2024")
ALGORITHM = "HS256"

def verify_admin_token(request: Request):
    """Проверка Bearer токена для админ API запросов"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


# ============ АДМИН ЭНДПОИНТЫ ============





# ============ API ДЛЯ ОБНОВЛЕНИЯ ============
# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/admin/api/order/{order_id}/payment-status")
async def admin_update_payment_status(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ обновляет статус оплаты заказа"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Admin only"}
            )
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        from datetime import datetime
        
        data = await request.json()
        new_status = data.get("payment_status")
        
        if not new_status:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "payment_status is required"}
            )
        
        # ✅ Валидные статусы оплаты
        valid_payment_statuses = ["pending", "paid", "refunded", "failed", "cancelled"]
        if new_status not in valid_payment_statuses:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Invalid payment status: {new_status}"}
            )
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        old_status = order.payment_status
        order.payment_status = new_status
        
        # ✅ Если статус стал "paid" - обновляем время оплаты и статус заказа
        if new_status == "paid" and not order.paid_at:
            order.paid_at = datetime.utcnow()
            # ✅ ИСПРАВЛЕНО: status = 'confirmed' (строка, БЕЗ ENUM)
            if order.status == "pending":
                order.status = "confirmed"
                order.confirmed_at = datetime.utcnow()
        
        # ✅ Если статус стал "refunded" - обновляем статус заказа
        if new_status == "refunded":
            order.status = "cancelled"
            order.cancelled_at = datetime.utcnow()
            order.refund_status = "completed"
            order.refund_processed_at = datetime.utcnow()
            
            # ✅ Освобождаем курьера
            if order.assigned_courier_id:
                db.query(CourierProfile).filter(
                    CourierProfile.user_id == order.assigned_courier_id
                ).update({
                    "current_order_id": None,
                    "current_order_status": None,
                    "is_available": True,
                    "is_online": True
                })
            
            # ✅ Возвращаем товар
            bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
            if bag:
                bag.available_quantity += 1
                if bag.available_quantity > 0:
                    bag.is_active = True
        
        db.commit()
        
        print(f"✅ Админ обновил статус оплаты заказа #{order.order_number}: {old_status} -> {new_status}")
        
        return {
            "success": True,
            "message": f"Payment status updated to {new_status}",
            "order_id": order.id,
            "order_number": order.order_number,
            "payment_status": order.payment_status,
            "order_status": order.status,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )
# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/admin/api/order/{order_id}/status")
async def admin_update_order_status(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ меняет статус заказа (с проверками и триггерами)"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Admin only"}
            )
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        import secrets
        from datetime import datetime, timedelta
        
        data = await request.json()
        new_status = data.get("status")
        
        if not new_status:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "status is required"}
            )
        
        # ✅ Валидные статусы заказов
        valid_statuses = [
            "pending", "confirmed", "preparing", "ready_for_pickup",
            "picked_up", "out_for_delivery", "nearby", "delivered", "cancelled"
        ]
        
        if new_status not in valid_statuses:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Invalid status: {new_status}"}
            )
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        old_status = order.status if order.status else "unknown"
        
        # ============ ЛОГИКА ПРИ СМЕНЕ СТАТУСА ============
        
        if new_status == "confirmed":
            # Админ подтверждает оплату (но доставка еще не начата)
            order.confirmed_at = datetime.utcnow()
            
        elif new_status == "out_for_delivery":
            # Админ запускает доставку → устанавливаем дедлайн 30 минут
            if order.payment_status != "paid":
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "detail": "Cannot start delivery: order not paid"}
                )
            # ✅ ИСПРАВЛЕНО: проверка статуса как строка
            if order.status != "confirmed":
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "detail": f"Cannot start delivery: order not confirmed. Current status: {order.status}"}
                )
            
            now = datetime.utcnow()
            order.delivery_started_at = now
            order.delivery_deadline = now + timedelta(minutes=30)
            
        elif new_status == "delivered":
            # Админ вручную отмечает доставку (если клиент не нажал кнопку)
            order.delivered_at = datetime.utcnow()
            
            # ✅ Освобождаем курьера
            if order.assigned_courier_id:
                db.query(CourierProfile).filter(
                    CourierProfile.user_id == order.assigned_courier_id
                ).update({
                    "current_order_id": None,
                    "current_order_status": None,
                    "is_available": True,
                    "is_online": True
                })
            
        elif new_status == "cancelled":
            # Админ отменяет заказ (если есть основания)
            reason = data.get("reason", "Отменено администратором")
            
            if order.payment_status == "paid":
                # Если оплачен, нужно вернуть деньги
                order.refund_status = "completed"
                order.refund_processed_at = datetime.utcnow()
                order.refund_amount = order.amount_paid
                order.payment_status = "refunded"
                order.refund_reason = f"Отменено администратором. Причина: {reason}"
                order.refund_transaction_id = f"ADMIN-REF-{secrets.token_hex(8).upper()}"
            
            order.cancelled_at = datetime.utcnow()
            
            # ✅ Освобождаем курьера
            if order.assigned_courier_id:
                db.query(CourierProfile).filter(
                    CourierProfile.user_id == order.assigned_courier_id
                ).update({
                    "current_order_id": None,
                    "current_order_status": None,
                    "is_available": True,
                    "is_online": True
                })
            
            # ✅ Возвращаем товар
            bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
            if bag:
                bag.available_quantity += 1
                if bag.available_quantity > 0:
                    bag.is_active = True
        
        # ✅ ИСПРАВЛЕНО: обновляем статус как строку (БЕЗ ENUM)
        order.status = new_status
        db.commit()
        
        print(f"✅ Админ изменил статус заказа #{order.order_number}: {old_status} -> {new_status}")
        
        return {
            "success": True,
            "message": f"Статус заказа {order.order_number} изменен с {old_status} на {new_status}",
            "order_id": order.id,
            "order_number": order.order_number,
            "old_status": old_status,
            "new_status": new_status,
            "delivery_deadline": order.delivery_deadline.isoformat() if order.delivery_deadline else None
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )
# Добавьте эти эндпоинты в ваш backend/main.py

from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional

class BookingRequest(BaseModel):
    bag_id: int

class BookingResponse(BaseModel):
    success: bool
    expires_at: Optional[str] = None
    remaining_seconds: int = 0
    message: str

# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/bookings/create")
async def create_booking(
    request: Request,
    db: Session = Depends(get_db)
):
    """Забронировать сюрприз-пакет на 15 минут"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
        
        # Проверяем что это клиент (customer)
        if payload.get("role") != "customer":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Only customers can book"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        import secrets
        from datetime import datetime, timedelta
        
        data = await request.json()
        bag_id = data.get("bag_id")
        
        if not bag_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "bag_id is required"}
            )
        
        # Check if bag exists and is available
        bag = db.query(SurpriseBag).filter(
            SurpriseBag.id == bag_id,
            SurpriseBag.is_active == True,
            SurpriseBag.available_quantity > 0
        ).first()
        
        if not bag:
            return {
                "success": False,
                "message": "Пакет недоступен"
            }
        
        # Check if there's an active booking (pending order less than 15 min old)
        # ✅ ИСПРАВЛЕНО: статус как строка (БЕЗ ENUM)
        existing_booking = db.query(Order).filter(
            Order.surprise_bag_id == bag_id,
            Order.status == "pending",
            Order.payment_status == "pending",
            Order.created_at > datetime.utcnow() - timedelta(minutes=15)
        ).first()
        
        if existing_booking:
            expires_at = existing_booking.created_at + timedelta(minutes=15)
            remaining = int((expires_at - datetime.utcnow()).total_seconds())
            return {
                "success": False,
                "message": "Этот пакет уже забронирован",
                "remaining_seconds": remaining
            }
        
        # Create booking (pending order)
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        order_number = f"BOOK-{secrets.token_hex(4).upper()}"
        
        # ✅ ИСПРАВЛЕНО: статус как строка (БЕЗ ENUM)
        order = Order(
            user_id=int(user_id),
            supplier_id=bag.supplier_id,
            surprise_bag_id=bag.id,
            order_number=order_number,
            status="pending",
            payment_status="pending",
            amount_paid=bag.discounted_price,
            created_at=datetime.utcnow()
        )
        
        db.add(order)
        
        # Decrease available quantity
        bag.available_quantity -= 1
        
        db.commit()
        db.refresh(order)
        
        print(f"✅ Бронирование создано: {order_number} для пользователя {user_id}")
        
        return {
            "success": True,
            "expires_at": expires_at.isoformat(),
            "remaining_seconds": 15 * 60,
            "message": f"Пакет '{bag.name}' забронирован на 15 минут",
            "order_id": order.id,
            "order_number": order.order_number
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )


# backend/main.py - ДОБАВЛЯЕМ ФИЛЬТРАЦИЮ ПО ГОРОДУ

@app.get("/api/surprise-bags")
async def get_all_surprise_bags(
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить сюрпризы ТОЛЬКО из города пользователя"""
    
    lat = request.query_params.get("lat")
    lon = request.query_params.get("lon")
    
    # Определяем город пользователя по координатам
    user_city = None
    if lat and lon:
        try:
            lat = float(lat)
            lon = float(lon)
            user_city = get_city_from_coords(lat, lon)
        except:
            pass
    
    # Если город не определился - показываем все (или Актобе по умолчанию)
    if not user_city:
        user_city = "Ақтөбе"  # или ваш город
    
    print(f"📍 Пользователь из города: {user_city}")
    
    # ✅ ТОЛЬКО СЮРПРИЗЫ ИЗ ГОРОДА ПОЛЬЗОВАТЕЛЯ
    bags = db.query(SurpriseBag).filter(
        SurpriseBag.is_active == True,
        SurpriseBag.available_quantity > 0,
        SurpriseBag.hide_contents == False,
        SurpriseBag.city == user_city  # ← ФИЛЬТР ПО ГОРОДУ
    ).all()
    
    result = []
    for bag in bags:
        supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
        if supplier and supplier.is_active:
            items = db.query(SurpriseBagItem).filter(
                SurpriseBagItem.surprise_bag_id == bag.id
            ).all()
            
            items_list = []
            for item in items:
                items_list.append({
                    "product_id": item.product_id,
                    "name": item.product_name,
                    "price": item.product_price,
                    "quantity": item.quantity
                })
            
            result.append({
                "id": bag.id,
                "supplier_id": bag.supplier_id,
                "supplier_name": supplier.business_name,
                "name": bag.name,
                "description": bag.description,
                "original_price": bag.original_price,
                "discounted_price": bag.discounted_price,
                "discount_percentage": bag.discount_percentage,
                "image_url": bag.image_url,
                "available_quantity": bag.available_quantity,
                "hide_contents": bag.hide_contents,
                "city": bag.city,
                "items": items_list
            })
    
    return JSONResponse(content=result)


@app.get("/api/surprise-bags/surprise")
async def get_surprise_bags_hidden(
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить скрытые сюрпризы ТОЛЬКО из города пользователя"""
    
    lat = request.query_params.get("lat")
    lon = request.query_params.get("lon")
    
    user_city = None
    if lat and lon:
        try:
            lat = float(lat)
            lon = float(lon)
            user_city = get_city_from_coords(lat, lon)
        except:
            pass
    
    if not user_city:
        user_city = "Ақтөбе"
    
    print(f"📍 Surprise страница, пользователь из: {user_city}")
    
    # ✅ ТОЛЬКО СЮРПРИЗЫ ИЗ ГОРОДА ПОЛЬЗОВАТЕЛЯ
    bags = db.query(SurpriseBag).filter(
        SurpriseBag.is_active == True,
        SurpriseBag.available_quantity > 0,
        SurpriseBag.hide_contents == True,
        SurpriseBag.city == user_city  # ← ФИЛЬТР ПО ГОРОДУ
    ).all()
    
    result = []
    for bag in bags:
        supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
        if supplier and supplier.is_active:
            result.append({
                "id": bag.id,
                "supplier_id": bag.supplier_id,
                "supplier_name": supplier.business_name,
                "name": bag.name,
                "description": bag.description,
                "original_price": bag.original_price,
                "discounted_price": bag.discounted_price,
                "discount_percentage": bag.discount_percentage,
                "image_url": bag.image_url,
                "available_quantity": bag.available_quantity,
                "hide_contents": bag.hide_contents,
                "city": bag.city,
                "items": [],
                "surprise_message": "🎁 Сюрприз! Состав не раскрывается до получения"
            })
    
    return JSONResponse(content=result)


# ============ ФУНКЦИЯ ОПРЕДЕЛЕНИЯ ГОРОДА ============
def get_city_from_coords(lat: float, lon: float):
    """Определяет город по координатам"""
    
    CITIES = {
        'Алматы': {'lat': 43.238, 'lon': 76.945, 'radius': 30},
        'Астана': {'lat': 51.169, 'lon': 71.449, 'radius': 30},
        'Шымкент': {'lat': 42.341, 'lon': 69.590, 'radius': 30},
        'Ақтөбе': {'lat': 50.283, 'lon': 57.167, 'radius': 30},
        'Қарағанды': {'lat': 49.801, 'lon': 73.102, 'radius': 30},
        'Атырау': {'lat': 47.115, 'lon': 51.917, 'radius': 30},
        'Өскемен': {'lat': 49.950, 'lon': 82.618, 'radius': 30},
        'Павлодар': {'lat': 52.287, 'lon': 76.973, 'radius': 30},
        'Тараз': {'lat': 42.899, 'lon': 71.365, 'radius': 30},
        'Қызылорда': {'lat': 44.848, 'lon': 65.482, 'radius': 30},
    }
    
    closest_city = None
    min_distance = float('inf')
    
    for city, coords in CITIES.items():
        distance = haversine_distance(lat, lon, coords['lat'], coords['lon'])
        if distance < coords['radius'] and distance < min_distance:
            min_distance = distance
            closest_city = city
    
    return closest_city


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.get("/api/bookings/check/{bag_id}")
async def check_booking(
    bag_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Проверить статус бронирования"""
    
    # ✅ Проверяем авторизацию (опционально, можно и без токена)
    auth_header = request.headers.get("Authorization")
    user_id = None
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from jose import jwt
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
        except:
            pass
    
    try:
        from datetime import datetime, timedelta
        
        # ✅ ИСПРАВЛЕНО: статус как строка (БЕЗ ENUM)
        booking = db.query(Order).filter(
            Order.surprise_bag_id == bag_id,
            Order.status == "pending",
            Order.payment_status == "pending",
            Order.created_at > datetime.utcnow() - timedelta(minutes=15)
        ).first()
        
        if not booking:
            return {
                "is_booked": False,
                "remaining_seconds": 0,
                "is_my_booking": False
            }
        
        expires_at = booking.created_at + timedelta(minutes=15)
        remaining = int((expires_at - datetime.utcnow()).total_seconds())
        
        # ✅ Проверяем, принадлежит ли бронирование текущему пользователю
        is_my_booking = user_id and booking.user_id == int(user_id)
        
        return {
            "is_booked": True,
            "remaining_seconds": max(0, remaining),
            "expires_at": expires_at.isoformat(),
            "order_id": booking.id,
            "order_number": booking.order_number,
            "is_my_booking": is_my_booking
        }
        
    except Exception as e:
        print(f"❌ Ошибка проверки бронирования: {e}")
        return {
            "is_booked": False,
            "remaining_seconds": 0,
            "error": str(e)
        }

# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.delete("/api/bookings/release/{bag_id}")
async def release_booking(
    bag_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Освободить бронь (если пользователь отменил)"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        from datetime import datetime
        
        # ✅ ИСПРАВЛЕНО: ищем активное бронирование (статус как строка)
        booking = db.query(Order).filter(
            Order.surprise_bag_id == bag_id,
            Order.user_id == int(user_id),
            Order.status == "pending",
            Order.payment_status == "pending"
        ).first()
        
        if booking:
            # Return quantity to bag
            bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
            if bag:
                bag.available_quantity += 1
                if bag.available_quantity > 0:
                    bag.is_active = True
                print(f"📦 Освобожден товар '{bag.name}', теперь {bag.available_quantity} шт.")
            
            # ✅ ИСПРАВЛЕНО: статус как строка (БЕЗ ENUM)
            booking.status = "cancelled"
            booking.cancelled_at = datetime.utcnow()
            db.commit()
            
            print(f"✅ Бронирование #{booking.order_number} отменено пользователем {user_id}")
            
            return {
                "success": True,
                "message": "Бронирование отменено",
                "order_id": booking.id,
                "order_number": booking.order_number
            }
        
        return {
            "success": False,
            "message": "Бронь не найдена или уже отменена"
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

# Обновите эндпоинт получения сюрприз-пакетов, чтобы исключить забронированные
# backend/main.py - обновите эндпоинт получения сюрпризов

@app.put("/api/supplier/surprise-bags/{bag_id}/toggle-type")
async def toggle_surprise_type(
    bag_id: int,
    request: Request,
    supplier: Supplier = Depends(verify_supplier_token),
    db: Session = Depends(get_db)
):
    """Поставщик меняет тип сюрприза: Surprise <-> Search"""
    
    bag = db.query(SurpriseBag).filter(
        SurpriseBag.id == bag_id,
        SurpriseBag.supplier_id == supplier.id
    ).first()
    
    if not bag:
        raise HTTPException(status_code=404, detail="Bag not found")
    
    # Меняем тип
    old_type = bag.hide_contents
    bag.hide_contents = not bag.hide_contents
    db.commit()
    
    new_type_display = "Surprise (скрытый состав)" if bag.hide_contents else "Search (видимый состав)"
    old_type_display = "Surprise (скрытый состав)" if old_type else "Search (видимый состав)"
    
    # Отправляем WebSocket уведомление об изменении
    try:
        await manager.broadcast({
            "type": "bag_type_changed",
            "data": {
                "bag_id": bag.id,
                "hide_contents": bag.hide_contents,
                "name": bag.name,
                "old_type": old_type_display,
                "new_type": new_type_display
            }
        }, channel="surprise_bags")
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    return {
        "success": True,
        "bag_id": bag.id,
        "hide_contents": bag.hide_contents,
        "old_type": old_type_display,
        "new_type": new_type_display,
        "message": f"Тип изменен с '{old_type_display}' на '{new_type_display}'"
    }


# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ




# backend/main.py - ЭНДПОИНТЫ ДЛЯ УПРАВЛЕНИЯ ТОВАРАМИ

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Supplier, SupplierProduct, SurpriseBag, SurpriseBagItem
import json



# ============================================================
# ЭНДПОИНТЫ ДЛЯ УПРАВЛЕНИЯ ТОВАРАМИ ПОСТАВЩИКА
# ============================================================

# ======== ПОЛУЧИТЬ ВСЕ ТОВАРЫ ПОСТАВЩИКА ========


# ======== ДОБАВИТЬ НОВЫЙ ТОВАР ========

# ======== ОБНОВИТЬ ТОВАР ========
@app.put("/api/supplier/products/{product_id}")
async def update_supplier_product(
    product_id: int,
    request: Request,
    supplier_id: int = Depends(get_supplier_id_from_token)
):
    """Обновить товар поставщика"""
    try:
        data = await request.json()
        
        name_ru = data.get("name_ru", "").strip()
        name_kz = data.get("name_kz", "").strip()
        name_en = data.get("name_en", "").strip()
        price = float(data.get("price", 0))
        category_id = data.get("category_id")
        image_url = data.get("image_url", "").strip()
        description_ru = data.get("description_ru", "").strip()
        description_kz = data.get("description_kz", "").strip()
        preparation_time = int(data.get("preparation_time", 15))
        is_available = data.get("is_available", True)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверяем что товар принадлежит поставщику
        cur.execute("SELECT id FROM supplier_products WHERE id = %s AND supplier_id = %s", (product_id, supplier_id))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return {"success": False, "error": "Товар не найден"}
        
        # Если указана категория - проверяем что она принадлежит поставщику
        if category_id:
            cur.execute("""
                SELECT id FROM supplier_categories 
                WHERE id = %s AND supplier_id = %s AND is_active = true
            """, (category_id, supplier_id))
            if not cur.fetchone():
                cur.close()
                conn.close()
                return {"success": False, "error": "Категория не найдена или неактивна"}
        
        cur.execute("""
            UPDATE supplier_products SET
                name_ru = %s,
                name_kz = %s,
                name_en = %s,
                description_ru = %s,
                description_kz = %s,
                price = %s,
                category_id = %s,
                image_url = %s,
                is_available = %s,
                preparation_time = %s,
                updated_at = NOW()
            WHERE id = %s AND supplier_id = %s
        """, (name_ru, name_kz, name_en, description_ru, description_kz,
              price, category_id, image_url, is_available, preparation_time,
              product_id, supplier_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Товар обновлен"}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

# ======== УДАЛИТЬ ТОВАР ========
@app.get("/api/supplier/surprise-bags/{bag_id}")
async def get_surprise_bag(
    bag_id: int,
    supplier_id: int = Depends(get_supplier_id_from_token)
):
    """Получить сюрприз по ID"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT * FROM surprise_bags
            WHERE id = %s AND supplier_id = %s
        """, (bag_id, supplier_id))
        
        bag = cur.fetchone()
        
        if not bag:
            cur.close()
            conn.close()
            return {"success": False, "error": "Сюрприз не найден"}
        
        # Получаем товары в сюрпризе
        cur.execute("""
            SELECT 
                sbi.id,
                sbi.supplier_product_id,
                sbi.product_name,
                sbi.product_price,
                sbi.quantity,
                sp.name_ru as product_name_ru,
                sp.name_kz as product_name_kz,
                sp.price as product_price_original
            FROM surprise_bag_items sbi
            LEFT JOIN supplier_products sp ON sp.id = sbi.supplier_product_id
            WHERE sbi.surprise_bag_id = %s
        """, (bag_id,))
        
        items = cur.fetchall()
        cur.close()
        conn.close()
        
        bag['items'] = items
        
        return {"success": True, "bag": bag}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}
@app.put("/api/supplier/surprise-bags/{bag_id}")
async def update_surprise_bag(
    bag_id: int,
    request: Request,
    supplier_id: int = Depends(get_supplier_id_from_token)
):
    """Обновить сюрприз"""
    try:
        data = await request.json()
        
        name = data.get("name", "").strip()
        description = data.get("description", "").strip()
        original_price = float(data.get("original_price", 0))
        discounted_price = float(data.get("discounted_price", 0))
        discount_percentage = int(data.get("discount_percentage", 0))
        available_quantity = int(data.get("available_quantity", 1))
        total_quantity = int(data.get("total_quantity", 1))
        pickup_start = data.get("pickup_start_time", "")
        pickup_end = data.get("pickup_end_time", "")
        image_url = data.get("image_url", "")
        is_active = data.get("is_active", True)
        hide_contents = data.get("hide_contents", False)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE surprise_bags SET
                name = %s,
                description = %s,
                original_price = %s,
                discounted_price = %s,
                discount_percentage = %s,
                available_quantity = %s,
                total_quantity = %s,
                pickup_start_time = %s,
                pickup_end_time = %s,
                image_url = %s,
                is_active = %s,
                hide_contents = %s
            WHERE id = %s AND supplier_id = %s
        """, (name, description, original_price, discounted_price,
              discount_percentage, available_quantity, total_quantity,
              pickup_start, pickup_end, image_url, is_active, hide_contents,
              bag_id, supplier_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Сюрприз обновлен"}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}
    


@app.get("/api/supplier/categories/{category_id}")
async def get_supplier_category(
    category_id: int,
    supplier_id: int = Depends(get_supplier_id_from_token)
):
    """Получить категорию по ID"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT * FROM supplier_categories
            WHERE id = %s AND supplier_id = %s AND is_active = true
        """, (category_id, supplier_id))
        
        category = cur.fetchone()
        cur.close()
        conn.close()
        
        if not category:
            return {"success": False, "error": "Категория не найдена"}
        
        return {"success": True, "category": category}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


@app.put("/api/supplier/categories/{category_id}")
async def update_supplier_category(
    category_id: int,
    request: Request,
    supplier_id: int = Depends(get_supplier_id_from_token)
):
    """Обновить категорию поставщика"""
    try:
        data = await request.json()
        
        name = data.get("name", "").strip()
        icon = data.get("icon", "📦")
        is_active = data.get("is_active", True)
        
        if not name:
            return {"success": False, "error": "Введите название категории"}
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE supplier_categories 
            SET name = %s, icon = %s, is_active = %s, updated_at = NOW()
            WHERE id = %s AND supplier_id = %s AND is_custom = true
        """, (name, icon, is_active, category_id, supplier_id))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return {"success": False, "error": "Категория не найдена или является стандартной"}
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Категория обновлена"}
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {"success": False, "error": str(e)}


# ======== ПОЛУЧИТЬ ТОВАРЫ ДЛЯ ВЫБОРА В СЮРПРИЗЕ ========
@app.get("/api/supplier/products/for-bag")
async def get_products_for_bag(
    supplier_id: int = Depends(get_supplier_id_from_token)
):
    """Получить товары для добавления в сюрприз (только доступные)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                sp.id,
                sp.name_ru,
                sp.name_kz,
                sp.price,
                sp.category_id,
                sc.name_ru as category_name_ru,
                sc.icon as category_icon
            FROM supplier_products sp
            LEFT JOIN supplier_categories sc ON sc.id = sp.category_id
            WHERE sp.supplier_id = %s AND sp.is_available = true
            ORDER BY sc.name_ru ASC, sp.name_ru ASC
        """, (supplier_id,))
        
        products = cur.fetchall()
        cur.close()
        conn.close()
        
        return {"success": True, "products": products}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}
# ============================================================
# ЭНДПОИНТЫ ДЛЯ УПРАВЛЕНИЯ СЮРПРИЗАМИ (ОБНОВЛЕНЫ)
# ============================================================
# ============================================================
# ПОЛУЧИТЬ СЮРПРИЗ ПО ID
# ============================================================

@app.get("/api/surprise-bags/{bag_id}")
async def get_surprise_bag_by_id(
    bag_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить конкретный сюрприз по ID"""
    
    print(f"🔍 Запрос сюрприза #{bag_id}")
    
    # Находим сюрприз
    bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
    
    if not bag:
        print(f"❌ Сюрприз #{bag_id} не найден")
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Сюрприз не найден"}
        )
    
    # Получаем поставщика
    supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
    
    # Получаем товары в сюрпризе (если они есть)
    items = db.query(SurpriseBagItem).filter(
        SurpriseBagItem.surprise_bag_id == bag.id
    ).all()
    
    items_list = []
    for item in items:
        items_list.append({
            "product_id": item.product_id or 0,
            "name": item.product_name or "",
            "price": float(item.product_price) if item.product_price else 0,
            "quantity": int(item.quantity) if item.quantity else 1
        })
    
    result = {
        "id": bag.id,
        "supplier_id": bag.supplier_id,
        "supplier_name": supplier.business_name if supplier else "Неизвестно",
        "name": bag.name,
        "description": bag.description,
        "original_price": float(bag.original_price) if bag.original_price else 0,
        "discounted_price": float(bag.discounted_price) if bag.discounted_price else 0,
        "discount_percentage": int(bag.discount_percentage) if bag.discount_percentage else 0,
        "image_url": bag.image_url or "",
        "available_quantity": int(bag.available_quantity) if bag.available_quantity else 0,
        "hide_contents": bool(bag.hide_contents) if bag.hide_contents is not None else False,
        "city": bag.city or "",
        "is_active": bool(bag.is_active) if bag.is_active is not None else False,
        "items": items_list
    }
    
    print(f"✅ Сюрприз #{bag_id} найден: {bag.name}")
    
    return JSONResponse(content=result)
@app.post("/api/supplier/surprise-bags")
async def create_surprise_bag(
    request: Request,
    supplier_id: int = Depends(get_supplier_id_from_token)
):
    """Создать сюрприз с товарами поставщика"""
    try:
        data = await request.json()
        
        name = data.get("name", "").strip()
        description = data.get("description", "").strip()
        original_price = float(data.get("original_price", 0))
        discounted_price = float(data.get("discounted_price", 0))
        discount_percentage = int(data.get("discount_percentage", 0))
        available_quantity = int(data.get("available_quantity", 1))
        total_quantity = int(data.get("total_quantity", 1))
        pickup_start = data.get("pickup_start_time", "")
        pickup_end = data.get("pickup_end_time", "")
        image_url = data.get("image_url", "")
        hide_contents = data.get("hide_contents", False)
        products_data = data.get("products", [])
        
        print(f"📥 Создание сюрприза: {name}, поставщик: {supplier_id}")
        
        if not name:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Введите название сюрприза"}
            )
        
        if not products_data or len(products_data) == 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Добавьте хотя бы один товар"}
            )
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Получаем город поставщика
        cur.execute("""
            SELECT city FROM suppliers WHERE id = %s
        """, (supplier_id,))
        
        supplier = cur.fetchone()
        supplier_city = supplier[0] if supplier and supplier[0] else "Ақтөбе"
        
        print(f"🏙️ Город поставщика: {supplier_city}")
        
        # 1. Создаем сюрприз (БЕЗ КОММЕНТАРИЕВ В SQL!)
        cur.execute("""
            INSERT INTO surprise_bags (
                supplier_id, name, description, original_price, discounted_price,
                discount_percentage, image_url, available_quantity, total_quantity,
                pickup_start_time, pickup_end_time, hide_contents, 
                city, is_active, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true, NOW()
            ) RETURNING id
        """, (supplier_id, name, description, original_price, discounted_price,
              discount_percentage, image_url, available_quantity, total_quantity,
              pickup_start, pickup_end, hide_contents, supplier_city))
        
        bag_id = cur.fetchone()[0]
        print(f"✅ Создан сюрприз ID: {bag_id} в городе: {supplier_city}")
        
        # 2. Добавляем товары в сюрприз
        for item in products_data:
            product_id = item.get("id")
            product_name = item.get("name", "")
            product_price = item.get("price", 0)
            quantity = item.get("quantity", 1)
            
            cur.execute("""
                INSERT INTO surprise_bag_items (
                    surprise_bag_id, supplier_product_id, 
                    product_name, product_price, quantity
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (bag_id, product_id, product_name, product_price, quantity))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return JSONResponse(content={
            "success": True,
            "message": f"Сюрприз создан в городе {supplier_city}",
            "bag_id": bag_id,
            "city": supplier_city
        })
        
    except Exception as e:
        print(f"❌ Ошибка создания сюрприза: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )    # ============================================================

@app.get("/api/supplier/categories")
async def get_supplier_categories(supplier_id: int = Depends(get_supplier_id_from_token)):
    """Получить все категории поставщика"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # ✅ ТОЛЬКО name (БЕЗ name_ru, name_kz, name_en)
        cur.execute("""
            SELECT id, name, icon, is_custom, is_active, created_at
            FROM supplier_categories
            WHERE supplier_id = %s AND is_active = true
            ORDER BY is_custom ASC, name ASC
        """, (supplier_id,))
        
        categories = cur.fetchall()
        cur.close()
        conn.close()
        
        return {"success": True, "categories": categories}
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {"success": False, "error": str(e)}
# ============================================================
# ДОБАВИТЬ НОВУЮ КАТЕГОРИЮ
# ============================================================
@app.post("/api/supplier/categories")
async def create_supplier_category(request: Request, supplier_id: int = Depends(get_supplier_id_from_token)):
    """Создать новую категорию поставщика (ОДНО ПОЛЕ name)"""
    try:
        data = await request.json()
        
        name = data.get("name", "").strip()
        icon = data.get("icon", "📦")
        
        if not name:
            return {"success": False, "error": "Введите название категории"}
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # ✅ ТОЛЬКО name (БЕЗ name_ru, name_kz)
        cur.execute("""
            INSERT INTO supplier_categories (supplier_id, name, icon, is_custom, is_active)
            VALUES (%s, %s, %s, true, true)
            RETURNING id
        """, (supplier_id, name, icon))
        
        category_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "message": "Категория создана",
            "category_id": category_id
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {"success": False, "error": str(e)}# ============================================================
# УДАЛИТЬ КАТЕГОРИЮ (ТОЛЬКО СВОЮ)
# ============================================================
@app.delete("/api/supplier/categories/{category_id}")
async def delete_supplier_category(
    category_id: int,
    supplier_id: int = Depends(get_supplier_id_from_token)
):
    """Удалить категорию поставщика (только свою)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id FROM supplier_categories 
            WHERE id = %s AND supplier_id = %s AND is_custom = true
        """, (category_id, supplier_id))
        
        if not cur.fetchone():
            cur.close()
            conn.close()
            return {"success": False, "error": "Категория не найдена или является стандартной"}
        
        cur.execute("""
            UPDATE supplier_products SET category_id = NULL 
            WHERE category_id = %s AND supplier_id = %s
        """, (category_id, supplier_id))
        
        cur.execute("DELETE FROM supplier_categories WHERE id = %s", (category_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return {"success": True, "message": "Категория удалена"}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# ОБНОВЛЕННЫЙ ЭНДПОИНТ ДЛЯ ТОВАРОВ (С КАТЕГОРИЯМИ)
# ============================================================


@app.get("/api/supplier/products")
async def get_supplier_products(supplier_id: int = Depends(get_supplier_id_from_token)):
    """Получить все товары поставщика"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                sp.id,
                sp.name,
                sp.price,
                sp.category_id,
                sc.name as category_name,
                sp.description,
                sp.preparation_time,
                sp.is_available,
                sp.created_at
            FROM supplier_products sp
            LEFT JOIN supplier_categories sc ON sc.id = sp.category_id
            WHERE sp.supplier_id = %s
            ORDER BY sp.created_at DESC
        """, (supplier_id,))
        
        products = cur.fetchall()
        cur.close()
        conn.close()
        
        return {"success": True, "products": products}
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/supplier/products")
async def create_supplier_product(request: Request, supplier_id: int = Depends(get_supplier_id_from_token)):
    """Создать новый товар поставщика"""
    try:
        data = await request.json()
        
        name = data.get("name", "").strip()
        price = float(data.get("price", 0))
        category_value = data.get("category_id")
        image_url = data.get("image_url", "").strip()
        description = data.get("description", "").strip()
        preparation_time = int(data.get("preparation_time", 15))
        is_available = data.get("is_available", True)
        
        if not name:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Введите название товара"}
            )
        
        if price <= 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Цена должна быть больше 0"}
            )
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        category_id = None
        
        if category_value:
            if str(category_value).isdigit():
                category_id = int(category_value)
                cur.execute("""
                    SELECT id FROM supplier_categories 
                    WHERE id = %s AND supplier_id = %s AND is_active = true
                """, (category_id, supplier_id))
                if not cur.fetchone():
                    cur.close()
                    conn.close()
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "error": "Категория не найдена"}
                    )
            else:
                cur.execute("""
                    SELECT id FROM supplier_categories 
                    WHERE name = %s AND supplier_id = %s AND is_active = true
                """, (category_value, supplier_id))
                result = cur.fetchone()
                if result:
                    category_id = result[0]
                else:
                    cur.execute("""
                        INSERT INTO supplier_categories (supplier_id, name, icon, is_custom, is_active)
                        VALUES (%s, %s, '📦', false, true)
                        RETURNING id
                    """, (supplier_id, category_value))
                    category_id = cur.fetchone()[0]
                    print(f"✅ Создана категория: {category_value}")
        
        cur.execute("""
            INSERT INTO supplier_products (
                supplier_id, name, price, category_id, image_url, 
                description, preparation_time, is_available, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (supplier_id, name, price, category_id, image_url,
              description, preparation_time, is_available))
        
        product_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return JSONResponse(content={
            "success": True,
            "message": "Товар добавлен",
            "product_id": product_id
        })
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============================================================
# ОБНОВЛЕННЫЙ ЭНДПОИНТ ДЛЯ УДАЛЕНИЯ ТОВАРА
# ============================================================
@app.delete("/api/supplier/products/{product_id}")
async def delete_supplier_product(product_id: int, supplier_id: int = Depends(get_supplier_id_from_token)):
    """Удалить товар поставщика"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "DELETE FROM supplier_products WHERE id = %s AND supplier_id = %s",
            (product_id, supplier_id)
        )
        
        affected = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        if affected == 0:
            return {"success": False, "error": "Товар не найден"}
        
        return {"success": True, "message": "Товар удален"}
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {"success": False, "error": str(e)}
# ============================================================
# ПОЛУЧИТЬ ЗАКАЗЫ
# ============================================================
@app.get("/api/supplier/orders")
async def get_supplier_orders(
    supplier: Supplier = Depends(get_current_supplier),
    db: Session = Depends(get_db)
):
    """Получить заказы поставщика"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                o.id,
                o.order_number,
                o.customer_address,
                o.amount_paid,
                o.status,
                o.created_at,
                o.delivery_deadline,
                o.assigned_courier_id,
                sb.name as bag_name
            FROM orders o
            LEFT JOIN surprise_bags sb ON sb.id = o.surprise_bag_id
            WHERE o.supplier_id = %s
            ORDER BY o.created_at DESC
        """, (supplier.id,))
        
        orders = cur.fetchall()
        cur.close()
        conn.close()
        
        return {"success": True, "orders": orders}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# ПОЛУЧИТЬ СЮРПРИЗЫ
# ============================================================
@app.get("/api/supplier/surprise-bags")
async def get_supplier_bags(
    supplier: Supplier = Depends(get_current_supplier),
    db: Session = Depends(get_db)
):
    """Получить все сюрпризы поставщика"""
    try:
        bags = db.query(SurpriseBag).filter(
            SurpriseBag.supplier_id == supplier.id
        ).order_by(SurpriseBag.created_at.desc()).all()
        
        result = []
        for bag in bags:
            items = db.query(SurpriseBagItem).filter(
                SurpriseBagItem.surprise_bag_id == bag.id
            ).all()
            
            items_data = []
            for item in items:
                items_data.append({
                    "id": item.id,
                    "product_name": item.product_name,
                    "product_price": item.product_price,
                    "quantity": item.quantity,
                    "supplier_product_id": item.supplier_product_id
                })
            
            result.append({
                "id": bag.id,
                "name": bag.name,
                "description": bag.description,
                "original_price": bag.original_price,
                "discounted_price": bag.discounted_price,
                "discount_percentage": bag.discount_percentage,
                "image_url": bag.image_url,
                "available_quantity": bag.available_quantity,
                "total_quantity": bag.total_quantity,
                "pickup_start_time": bag.pickup_start_time,
                "pickup_end_time": bag.pickup_end_time,
                "is_active": bag.is_active,
                "hide_contents": bag.hide_contents,
                "created_at": bag.created_at,
                "items": items_data
            })
        
        return {"success": True, "bags": result}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

# ============ PAYMENT IMITATION SYSTEM ============
import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import Optional, Literal


class PaymentMethod(str, Enum):
    KASPI = "kaspi"
    HALYK = "halyk"
    MASTERCARD = "mastercard"
    VISA = "visa"

class PaymentRequest(BaseModel):
    order_id: int
    payment_method: PaymentMethod
    amount: float
    card_number: Optional[str] = None
    card_expiry: Optional[str] = None
    card_cvv: Optional[str] = None
    card_holder: Optional[str] = None

class PaymentResponse(BaseModel):
    success: bool
    payment_id: str
    transaction_id: str
    amount: float
    status: str  # completed, failed, pending
    message: str
    payment_method: str
    timestamp: str

# Store payment transactions (in production, use database)
payment_transactions = {}


# backend/main.py - Add all payment endpoints

# ============ PAYMENT SYSTEM (IMITATION MODE) ============
import uuid
import asyncio
import random
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Literal
from backend.schemas import PaymentRequest, PaymentResponse, PaymentMethod

# Store payment transactions (in production, move to database)
payment_transactions = {}

# Payment configuration
PAYMENT_CONFIG = {
    "mode": "demo",  # Change to "production" when using real APIs
    "demo_success_rate": 0.95,  # 95% success rate for demo
    "kaspi": {
        "merchant_id": os.getenv("KASPI_MERCHANT_ID", "demo_merchant_123"),
        "secret_key": os.getenv("KASPI_SECRET_KEY", "demo_secret_456"),
        "api_url": os.getenv("KASPI_API_URL", "https://api.kaspi.kz/payment/v1"),
        "enabled": False  # Set to True when ready
    },
    "halyk": {
        "merchant_id": os.getenv("HALYK_MERCHANT_ID", "demo_merchant_789"),
        "secret_key": os.getenv("HALYK_SECRET_KEY", "demo_secret_000"),
        "api_url": os.getenv("HALYK_API_URL", "https://epay.halykbank.kz"),
        "enabled": False  # Set to True when ready
    }
}

# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/payment/initiate")
async def initiate_payment(request: Request, db: Session = Depends(get_db)):
    """
    Initiate payment - IMITATION MODE
    When real APIs are available, switch PAYMENT_CONFIG["mode"] to "production"
    """
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        import uuid
        import asyncio
        import random
        from datetime import datetime
        
        data = await request.json()
        order_id = data.get("order_id")
        amount = data.get("amount")
        payment_method = data.get("payment_method", "kaspi")
        card_number = data.get("card_number", "")
        
        if not order_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "order_id is required"}
            )
        
        if not amount or amount <= 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Invalid amount"}
            )
        
        # Verify order exists and belongs to user
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == int(user_id)
        ).first()
        
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        # Check if order is already paid
        if order.payment_status == "paid":
            return {
                "success": True,
                "payment_id": order.payment_id or f"PAY-{uuid.uuid4().hex[:12].upper()}",
                "transaction_id": order.transaction_id or f"TXN-{uuid.uuid4().hex[:16].upper()}",
                "amount": amount,
                "status": "completed",
                "message": "Order already paid",
                "payment_method": payment_method,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Generate unique IDs
        payment_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        transaction_id = f"TXN-{uuid.uuid4().hex[:16].upper()}"
        
        # Simulate payment processing delay
        await asyncio.sleep(1.5)
        
        # DEMO MODE: Simulate payment result
        PAYMENT_CONFIG = {
            "mode": "demo",
            "demo_success_rate": 0.95,
            "kaspi": {"enabled": True},
            "halyk": {"enabled": True}
        }
        
        if PAYMENT_CONFIG.get("mode") == "demo":
            # 95% success rate for realistic testing
            is_successful = random.random() < PAYMENT_CONFIG.get("demo_success_rate", 0.95)
            
            if is_successful:
                # ✅ ИСПРАВЛЕНО: статус как строка (БЕЗ ENUM)
                order.payment_id = payment_id
                order.transaction_id = transaction_id
                order.payment_status = "paid"
                order.payment_method = payment_method
                order.paid_at = datetime.utcnow()
                order.payment_amount = amount
                order.status = "confirmed"
                order.confirmed_at = datetime.utcnow()
                db.commit()
                
                # Create tracking record
                tracking = OrderTracking(
                    order_id=order.id,
                    status=order.status,
                    message=f"✅ Payment completed via {payment_method} (Demo Mode)",
                    created_at=datetime.utcnow()
                )
                db.add(tracking)
                db.commit()
                
                # Store transaction for reference
                payment_transactions = {}
                payment_transactions[payment_id] = {
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "amount": amount,
                    "payment_method": payment_method,
                    "card_last4": card_number[-4:] if card_number else "0000",
                    "status": "completed",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                result = {
                    "success": True,
                    "payment_id": payment_id,
                    "transaction_id": transaction_id,
                    "amount": amount,
                    "status": "completed",
                    "message": f"✅ Payment successful via {payment_method}",
                    "payment_method": payment_method,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Simulate payment failure
                result = {
                    "success": False,
                    "payment_id": payment_id,
                    "transaction_id": transaction_id,
                    "amount": amount,
                    "status": "failed",
                    "message": "❌ Payment failed. Insufficient funds or card declined. Please try another card.",
                    "payment_method": payment_method,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return result
        
        # PRODUCTION MODE: Real API integration
        else:
            # This will be implemented when you get real API keys
            if payment_method == "kaspi" and PAYMENT_CONFIG.get("kaspi", {}).get("enabled", False):
                # return await process_real_kaspi_payment(order, data, payment_id, transaction_id, db)
                return {
                    "success": False,
                    "message": "Real Kaspi API not configured yet. Please enable in production."
                }
            elif payment_method == "halyk" and PAYMENT_CONFIG.get("halyk", {}).get("enabled", False):
                # return await process_real_halyk_payment(order, data, payment_id, transaction_id, db)
                return {
                    "success": False,
                    "message": "Real Halyk API not configured yet. Please enable in production."
                }
            else:
                return {
                    "success": False,
                    "message": f"Real {payment_method} API not configured yet. Please enable in production."
                }
        
    except Exception as e:
        print(f"❌ Ошибка оплаты: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )
    

async def process_real_kaspi_payment(order: Order, payment_data: PaymentRequest, payment_id: str, transaction_id: str, db: Session):
    """Process real Kaspi payment (to be implemented when you have API keys)"""
    # TODO: Implement when you get Kaspi API credentials
    # Example structure:
    """
    async with httpx.AsyncClient() as client:
        payload = {
            "merchantId": PAYMENT_CONFIG["kaspi"]["merchant_id"],
            "orderId": order.order_number,
            "amount": payment_data.amount,
            "currency": "KZT",
            "cardNumber": payment_data.card_number,
            "expiryDate": payment_data.card_expiry,
            "cvv": payment_data.card_cvv
        }
        
        # Generate signature
        signature = generate_kaspi_signature(payload)
        payload["signature"] = signature
        
        response = await client.post(
            f"{PAYMENT_CONFIG['kaspi']['api_url']}/pay",
            json=payload,
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                # Update order...
                return PaymentResponse(success=True, ...)
    """
    return {"success": False, "message": "Kaspi API integration pending"}

async def process_real_halyk_payment(order: Order, payment_data: PaymentRequest, payment_id: str, transaction_id: str, db: Session):
    """Process real Halyk payment (to be implemented when you have API keys)"""
    # TODO: Implement when you get Halyk API credentials
    return {"success": False, "message": "Halyk API integration pending"}

@app.get("/api/payment/status/{payment_id}")
async def get_payment_status(payment_id: str, db: Session = Depends(get_db)):
    """Get payment status by payment_id"""
    
    # First check database
    order = db.query(Order).filter(Order.payment_id == payment_id).first()
    
    if order:
        return {
            "payment_id": payment_id,
            "order_id": order.id,
            "order_number": order.order_number,
            "amount": order.payment_amount or order.amount_paid,
            "status": order.payment_status,
            "payment_method": order.payment_method,
            "card_last4": None,
            "timestamp": order.paid_at.isoformat() if order.paid_at else None
        }
    
    # Check transaction cache
    transaction = payment_transactions.get(payment_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {
        "payment_id": payment_id,
        "order_id": transaction["order_id"],
        "order_number": transaction["order_number"],
        "amount": transaction["amount"],
        "status": transaction["status"],
        "payment_method": transaction["payment_method"],
        "card_last4": transaction["card_last4"],
        "timestamp": transaction["timestamp"]
    }

@app.get("/api/payment/history")
async def get_payment_history(request: Request, db: Session = Depends(get_db)):
    """Get user's payment history"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    orders = db.query(Order).filter(
        Order.user_id == int(user_id),
        Order.payment_status == "paid"
    ).order_by(Order.paid_at.desc()).all()
    
    history = []
    for order in orders:
        history.append({
            "order_id": order.id,
            "order_number": order.order_number,
            "amount": order.payment_amount or order.amount_paid,
            "payment_method": order.payment_method,
            "payment_id": order.payment_id,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "status": order.payment_status
        })
    
    return {"history": history}

@app.get("/api/payment/receipt/{order_id}")
async def get_payment_receipt(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Generate payment receipt for order"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == int(user_id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.payment_status != "paid":
        raise HTTPException(status_code=400, detail="Order not paid yet")
    
    supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
    bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
    
    return {
        "receipt": {
            "receipt_number": f"RCP-{order.order_number}",
            "order_number": order.order_number,
            "date": order.paid_at.isoformat() if order.paid_at else order.created_at.isoformat(),
            "supplier_name": supplier.business_name if supplier else "Sarqyn Food",
            "supplier_address": supplier.address if supplier else "Almaty, Kazakhstan",
            "items": [
                {
                    "name": bag.name if bag else "Surprise Bag",
                    "quantity": 1,
                    "price": order.amount_paid,
                    "total": order.amount_paid
                }
            ],
            "subtotal": order.amount_paid,
            "total": order.amount_paid,
            "payment_method": order.payment_method,
            "payment_id": order.payment_id,
            "transaction_id": order.transaction_id,
            "status": order.payment_status
        }
    }

# Helper endpoint to switch payment mode (admin only - add security in production)
@app.post("/api/admin/payment-mode")
async def set_payment_mode(request: Request):
    """Switch between demo and production payment mode"""
    data = await request.json()
    mode = data.get("mode", "demo")
    
    if mode in ["demo", "production"]:
        PAYMENT_CONFIG["mode"] = mode
        return {"success": True, "mode": mode, "message": f"Payment mode switched to {mode}"}
    
    raise HTTPException(status_code=400, detail="Invalid mode. Use 'demo' or 'production'")

# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/payment/initiate")
async def initiate_payment(request: Request, db: Session = Depends(get_db)):
    """Initiate payment - IMITATION MODE (ready for real API)"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        import uuid
        import asyncio
        import random
        from datetime import datetime
        
        data = await request.json()
        
        order_id = data.get("order_id")
        amount = data.get("amount")
        payment_method = data.get("payment_method", "kaspi")
        card_number = data.get("card_number", "")
        
        if not order_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "order_id is required"}
            )
        
        if not amount or amount <= 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Invalid amount"}
            )
        
        # Verify order exists and belongs to user
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == int(user_id)
        ).first()
        
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        # Check if order is already paid
        if order.payment_status == "paid":
            return {
                "success": True,
                "payment_id": order.payment_id or f"PAY-{uuid.uuid4().hex[:12].upper()}",
                "transaction_id": order.transaction_id or f"TXN-{uuid.uuid4().hex[:16].upper()}",
                "amount": amount,
                "status": "completed",
                "message": "Order already paid",
                "payment_method": payment_method,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Generate unique IDs
        payment_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        transaction_id = f"TXN-{uuid.uuid4().hex[:16].upper()}"
        
        # Simulate payment processing (1 second delay)
        await asyncio.sleep(1)
        
        # IMITATION: Always succeed (with 95% success rate for realism)
        is_successful = random.random() < 0.95  # 95% success rate
        
        # Store transactions globally
        if 'payment_transactions' not in globals():
            global payment_transactions
            payment_transactions = {}
        
        if is_successful:
            # ✅ ИСПРАВЛЕНО: статус как строка (БЕЗ ENUM)
            order.payment_id = payment_id
            order.payment_status = "paid"
            order.payment_method = payment_method
            order.paid_at = datetime.utcnow()
            order.status = "confirmed"
            order.confirmed_at = datetime.utcnow()
            db.commit()
            
            # Create tracking record
            tracking = OrderTracking(
                order_id=order.id,
                status=order.status,
                message=f"✅ Payment completed via {payment_method} (Imitation)",
                created_at=datetime.utcnow()
            )
            db.add(tracking)
            db.commit()
            
            # Store transaction for reference
            payment_transactions[payment_id] = {
                "order_id": order.id,
                "order_number": order.order_number,
                "amount": amount,
                "payment_method": payment_method,
                "card_last4": card_number[-4:] if card_number else "0000",
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            print(f"✅ Оплата успешна: {order.order_number} через {payment_method}")
            
            return {
                "success": True,
                "payment_id": payment_id,
                "transaction_id": transaction_id,
                "amount": amount,
                "status": "completed",
                "message": f"✅ Payment successful via {payment_method}",
                "payment_method": payment_method,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Simulate payment failure
            print(f"❌ Оплата отклонена: {order.order_number} через {payment_method}")
            
            return {
                "success": False,
                "payment_id": payment_id,
                "transaction_id": transaction_id,
                "amount": amount,
                "status": "failed",
                "message": "❌ Payment failed. Insufficient funds or card declined.",
                "payment_method": payment_method,
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        print(f"❌ Ошибка оплаты: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

@app.get("/api/payment/status/{payment_id}")
async def get_payment_status(payment_id: str):
    """Get payment status"""
    transaction = payment_transactions.get(payment_id)
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {
        "payment_id": payment_id,
        "order_id": transaction["order_id"],
        "order_number": transaction["order_number"],
        "amount": transaction["amount"],
        "status": transaction["status"],
        "payment_method": transaction["payment_method"],
        "card_last4": transaction["card_last4"],
        "timestamp": transaction["timestamp"]
    }



# ============ FUTURE: REAL BANK API INTEGRATION (Template) ============

"""
Future implementation for real Kaspi API:

class RealKaspiPayment:
    def __init__(self):
        self.merchant_id = os.getenv("KASPI_MERCHANT_ID")
        self.secret_key = os.getenv("KASPI_SECRET_KEY")
        self.api_url = os.getenv("KASPI_API_URL", "https://api.kaspi.kz/payment/v1")
    
    async def process_payment(self, order, card_details, amount):
        async with httpx.AsyncClient() as client:
            payload = {
                "merchantId": self.merchant_id,
                "orderId": order.order_number,
                "amount": amount,
                "currency": "KZT",
                "cardNumber": card_details["number"],
                "expiryDate": card_details["expiry"],
                "cvv": card_details["cvv"]
            }
            
            # Generate signature
            signature = self.generate_signature(payload)
            payload["signature"] = signature
            
            response = await client.post(f"{self.api_url}/pay", json=payload)
            return response.json()
    
    def generate_signature(self, payload):
        # Kaspi signature generation logic
        pass

Future implementation for real Halyk API:

class RealHalykPayment:
    def __init__(self):
        self.merchant_id = os.getenv("HALYK_MERCHANT_ID")
        self.api_url = os.getenv("HALYK_API_URL", "https://epay.halykbank.kz")
    
    async def process_payment(self, order, card_details, amount):
        async with httpx.AsyncClient() as client:
            payload = {
                "merchant_id": self.merchant_id,
                "order_id": order.order_number,
                "amount": amount,
                "currency": "KZT",
                "card": {
                    "number": card_details["number"],
                    "expiry": card_details["expiry"],
                    "cvv": card_details["cvv"]
                }
            }
            
            response = await client.post(f"{self.api_url}/payment", json=payload)
            return response.json()
"""
# ============ CART API ENDPOINTS ============

# backend/main.py - добавь эти эндпоинты

# ============ CART API ENDPOINTS ============
@app.get("/api/cart")
async def get_cart(request: Request, db: Session = Depends(get_db)):
    """Get current user's cart"""
    user_id = get_user_id_from_request(request)
    
    if not user_id:
        return {"success": False, "error": "Not authenticated", "items": [], "total": 0, "count": 0}
    
    cart_items = db.query(CartItem).filter(
        CartItem.user_id == user_id
    ).all()
    
    items = []
    for item in cart_items:
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == item.surprise_bag_id).first()
        if bag:
            supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
            items.append({
                "id": bag.id,
                "name": bag.name,
                "price": bag.discounted_price,
                "original_price": bag.original_price,
                "discount_percentage": bag.discount_percentage,
                "image_url": bag.image_url,
                "quantity": item.quantity,
                "businessName": supplier.business_name if supplier else "Sarqyn"
            })
    
    total = sum(item["price"] * item["quantity"] for item in items)
    count = sum(item["quantity"] for item in items)
    
    return {
        "success": True,
        "items": items,
        "total": total,
        "count": count
    }


# backend/main.py - добавьте или обновите эндпоинт добавления в корзину

# backend/main.py - обновите эндпоинт добавления в корзину

# backend/main.py - исправленный эндпоинт

# backend/main.py - исправленный эндпоинт
# backend/main.py - УБЕДИСЬ, ЧТО ЭТОТ ЭНДПОИНТ ТОЧНО УМЕНЬШАЕТ КОЛИЧЕСТВО
# backend/main.py - полный эндпоинт добавления в корзину

# backend/main.py - убедитесь, что эндпоинт возвращает success
# backend/main.py - замените ваш существующий эндпоинт
# backend/main.py - исправленный эндпоинт

@app.post("/api/cart/add")
async def add_to_cart(request: Request, db: Session = Depends(get_db)):
    """Добавление товара в корзину"""
    
    # ✅ Получаем user_id из Bearer токена
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Token error: {str(e)}"}
        )
    
    try:
        data = await request.json()
        bag_id = data.get("bag_id")
        quantity = data.get("quantity", 1)
        
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
        
        if not bag:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Товар не найден"}
            )
        
        if bag.available_quantity < quantity:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Доступно только {bag.available_quantity} шт."}
            )
        
        # Уменьшаем количество
        bag.available_quantity -= quantity
        if bag.available_quantity <= 0:
            bag.is_active = False
        
        # Создаем временную резервацию
        reservation = TemporaryReservation(
            bag_id=bag_id,
            user_id=int(user_id),
            quantity=quantity,
            reserved_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            is_paid=False
        )
        db.add(reservation)
        
        # Добавляем в корзину
        existing = db.query(CartItem).filter(
            CartItem.user_id == int(user_id),
            CartItem.surprise_bag_id == bag_id
        ).first()
        
        if existing:
            existing.quantity += quantity
        else:
            cart_item = CartItem(
                user_id=int(user_id),
                surprise_bag_id=bag_id,
                quantity=quantity
            )
            db.add(cart_item)
        
        db.commit()
        
        return JSONResponse(content={
            "success": True,
            "message": "Товар добавлен в корзину",
            "available_quantity": bag.available_quantity,
            "reservation_id": reservation.id,
            "expires_at": reservation.expires_at.isoformat()
        })
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": f"Ошибка сервера: {str(e)}"}
        )
# backend/main.py - добавьте

# backend/main.py - добавьте этот эндпоинт

@app.delete("/api/cart/remove/{bag_id}")
async def remove_from_cart(bag_id: int, request: Request, db: Session = Depends(get_db)):
    """Remove item from cart"""
    user_id = get_user_id_from_request(request)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.surprise_bag_id == bag_id
    ).first()
    
    if cart_item:
        db.delete(cart_item)
        db.commit()
    
    return {"success": True, "message": "Removed from cart"}






@app.put("/api/cart/update/{bag_id}")
async def update_cart_quantity(bag_id: int, request: Request, db: Session = Depends(get_db)):
    """Update item quantity in cart"""
    user_id = get_user_id_from_request(request)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    quantity = data.get("quantity", 1)
    
    if quantity <= 0:
        return await remove_from_cart(bag_id, request, db)
    
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.surprise_bag_id == bag_id
    ).first()
    
    if cart_item:
        cart_item.quantity = quantity
        cart_item.updated_at = datetime.utcnow()
        db.commit()
    
    return {"success": True, "message": "Cart updated"}
# backend/main.py - добавь этот эндпоинт для проверки

@app.get("/api/debug/users")
async def debug_all_users():
    """Посмотреть всех пользователей и их статус"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT id, phone, first_name, last_name, is_active, role, created_at
        FROM users
        ORDER BY id DESC
    """)
    
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    return {
        "total": len(users),
        "users": users
    }
@app.post("/api/debug/activate-all")
async def activate_all_users():
    """Активировать ВСЕХ пользователей"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE users 
        SET is_active = true 
        WHERE is_active = false
    """)
    
    updated = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        "success": True,
        "activated_count": updated,
        "message": f"Активировано {updated} пользователей"
    }

@app.delete("/api/cart/clear")
async def clear_cart(request: Request, db: Session = Depends(get_db)):
    """Clear all items from cart"""
    user_id = get_user_id_from_request(request)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    db.commit()
    
    return {"success": True, "message": "Cart cleared"}

# backend/main.py - обнови create_orders_from_cart
# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/orders/create-from-cart")
async def create_orders_from_cart(request: Request, db: Session = Depends(get_db)):
    """Create orders from all items in cart"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
        
        # Проверяем что это клиент
        if payload.get("role") != "customer":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Only customers can create orders"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        import secrets
        import json
        from datetime import datetime
        
        data = await request.json()
        customer_lat = data.get("lat")
        customer_lon = data.get("lon")
        customer_address = data.get("address")
        delivery_type = data.get("delivery_type", "delivery")
        
        if delivery_type == "delivery" and (not customer_lat or not customer_lon or not customer_address):
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Delivery address is required for delivery"}
            )
        
        cart_items = db.query(CartItem).filter(CartItem.user_id == int(user_id)).all()
        
        if not cart_items:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Cart is empty"}
            )
        
        orders_created = []
        total_amount = 0
        
        for cart_item in cart_items:
            bag = db.query(SurpriseBag).filter(
                SurpriseBag.id == cart_item.surprise_bag_id,
                SurpriseBag.is_active == True,
                SurpriseBag.available_quantity >= cart_item.quantity
            ).first()
            
            if not bag:
                continue
            
            supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
            
            order_number = f"ORD-{secrets.token_hex(4).upper()}"
            amount = bag.discounted_price * cart_item.quantity
            
            # ✅ ИСПРАВЛЕНО: статус как строка (БЕЗ ENUM)
            order = Order(
                user_id=int(user_id),
                supplier_id=bag.supplier_id,
                surprise_bag_id=bag.id,
                order_number=order_number,
                status="pending",
                delivery_type=delivery_type,
                customer_lat=customer_lat if delivery_type == "delivery" else None,
                customer_lon=customer_lon if delivery_type == "delivery" else None,
                customer_address=customer_address,
                amount_paid=amount,
                total_amount=amount,
                items=json.dumps([{
                    "bag_id": bag.id,
                    "name": bag.name,
                    "price": bag.discounted_price,
                    "quantity": cart_item.quantity,
                    "original_price": bag.original_price,
                    "image_url": bag.image_url
                }]),
                pickup_time=f"{bag.pickup_start_time} - {bag.pickup_end_time}" if bag.pickup_start_time else None,
                created_at=datetime.utcnow()
            )
            
            db.add(order)
            db.flush()
            
            bag.available_quantity -= cart_item.quantity
            if bag.available_quantity <= 0:
                bag.is_active = False
            
            total_amount += amount
            orders_created.append(order)
        
        # Удаляем все товары из корзины
        for cart_item in cart_items:
            db.delete(cart_item)
        
        db.commit()
        
        # Отправляем уведомления курьерам ТОЛЬКО для доставки
        if delivery_type == "delivery":
            for order in orders_created:
                try:
                    supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
                    supplier_name = supplier.business_name if supplier else "Ресторан"
                    
                    await manager.broadcast({
                        "type": "new_order_for_courier",
                        "data": {
                            "order_id": order.id,
                            "order_number": order.order_number,
                            "supplier_name": supplier_name,
                            "amount": order.amount_paid,
                            "bag_name": "Заказ из корзины",
                            "customer_address": order.customer_address,
                            "supplier_lat": supplier.lat if supplier else None,
                            "supplier_lon": supplier.lon if supplier else None,
                            "customer_lat": order.customer_lat,
                            "customer_lon": order.customer_lon
                        }
                    }, channel="couriers")
                    print(f"📢 Уведомление о заказе #{order.id} отправлено курьерам")
                except Exception as e:
                    print(f"❌ Ошибка отправки уведомления для заказа #{order.id}: {e}")
        
        await manager.broadcast({
            "type": "order_created",
            "user_id": int(user_id),
            "order_count": len(orders_created),
            "total_amount": total_amount
        })
        
        return {
            "success": True,
            "orders": [
                {
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "amount": order.amount_paid,
                    "status": order.status
                } for order in orders_created
            ],
            "total_amount": total_amount,
            "message": f"Created {len(orders_created)} order(s)"
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.put("/api/supplier/orders/{order_id}/confirm")
async def confirm_order_by_supplier(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Ресторан подтверждает заказ"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
        
        # Проверяем что это поставщик
        if payload.get("role") != "supplier":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Not a supplier"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        # Проверяем, что пользователь - владелец ресторана
        supplier = db.query(Supplier).filter(Supplier.user_id == int(user_id)).first()
        if not supplier:
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Supplier profile not found"}
            )
        
        # Получаем заказ
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.supplier_id == supplier.id
        ).first()
        
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        # ✅ ИСПРАВЛЕНО: статус как строка (БЕЗ ENUM)
        order.status = "confirmed"
        order.confirmed_at = datetime.utcnow()
        db.commit()
        
        print(f"✅ Поставщик {supplier.business_name} подтвердил заказ #{order.order_number}")
        
        # ✅ ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ КУРЬЕРАМ
        if not order.assigned_courier_id:
            try:
                await manager.broadcast({
                    "type": "new_order_for_courier",
                    "data": {
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "supplier_name": supplier.business_name,
                        "amount": order.amount_paid,
                        "bag_name": order.bag_name or "Заказ подтвержден",
                        "customer_address": order.customer_address,
                        "supplier_lat": supplier.lat,
                        "supplier_lon": supplier.lon,
                        "customer_lat": order.customer_lat,
                        "customer_lon": order.customer_lon
                    }
                }, channel="courier_notifications")
                print(f"📢 Уведомление о подтверждении заказа #{order.id} отправлено курьерам")
            except Exception as e:
                print(f"❌ Ошибка отправки уведомления: {e}")
        
        return {
            "success": True,
            "message": "Order confirmed",
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

@app.get("/api/orders/my")
async def get_my_orders(request: Request, db: Session = Depends(get_db)):
    """Get all orders for current user"""
    user_id = get_user_id_from_request(request)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    orders = db.query(Order).filter(
        Order.user_id == user_id
    ).order_by(Order.created_at.desc()).all()
    
    
    
    result = []
    for order in orders:
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
        supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        
        # Parse items if stored as JSON
        items = []
        if order.items:
            try:
                items = json.loads(order.items)
            except:
                pass
        
        result.append({
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status.value if order.status else "pending",
            "amount": order.amount_paid or 0,
            "total_amount": order.total_amount or order.amount_paid or 0,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "customer_address": order.customer_address,
            "supplier_name": supplier.business_name if supplier else "Sarqyn",
            "bag_name": bag.name if bag else "Surprise Bag",
            "items": items,
            "item_count": len(items) if items else 1
        })
    
    return {"success": True, "orders": result}
# ============ WEBSOCKET MANAGER ============
# Добавь эту функцию где-нибудь после определения manager
async def notify_new_surprise(bag_data: dict):
    """Notify all connected clients about a new surprise bag"""
    await manager.broadcast({
        "type": "new_bag",
        "data": bag_data,
        "timestamp": datetime.utcnow().isoformat()
    })
    print(f"📢 Broadcasted new surprise: {bag_data.get('name')}")

async def notify_bag_update(bag_data: dict):
    """Notify about bag update (price change, quantity change)"""
    await manager.broadcast({
        "type": "update_bag",
        "data": bag_data,
        "timestamp": datetime.utcnow().isoformat()
    })

async def notify_bag_deleted(bag_id: int):
    """Notify about bag deletion"""
    await manager.broadcast({
        "type": "delete_bag",
        "data": {"bag_id": bag_id},
        "timestamp": datetime.utcnow().isoformat()
    })
# backend/main.py - убедитесь что менеджер правильно настроен

# backend/main.py - найдите класс ConnectionManager и добавьте метод disconnect



# ============ WEBSOCKET ENDPOINT ============
# backend/main.py - добавьте WebSocket обработку

# backend/main.py - исправленный WebSocket эндпоинт

# backend/main.py - ИСПРАВЛЕННЫЙ WebSocket эндпоинт

# Глобальная переменная для единственного админа
admin_websocket = None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для общих уведомлений (user, courier, supplier, admin)"""
    global admin_websocket
    
    # ✅ КРИТИЧЕСКИ ВАЖНО: Сначала ПРИНИМАЕМ соединение
    try:
        await websocket.accept()
        print("✅ WebSocket /ws connection accepted")
    except Exception as e:
        print(f"❌ Failed to accept WebSocket connection: {e}")
        return
    
    # ТОЛЬКО ПОСЛЕ accept() можно получать параметры
    try:
        # Получаем параметры из query string
        token = websocket.query_params.get("token")
        user_type = websocket.query_params.get("type", "user")  # user, courier, supplier, admin
        user_id_str = websocket.query_params.get("user_id")
        
        print(f"🔍 WebSocket connection: type={user_type}, token={token[:30] if token else 'None'}...")
        
        # 👑 ДЛЯ АДМИНА - специальная обработка
        if user_type == "admin":
            # Закрываем старое соединение если было
            if admin_websocket:
                try:
                    await admin_websocket.close()
                    print("🔌 Closed old admin connection")
                except:
                    pass
            
            admin_websocket = websocket
            print(f"👑 ADMIN connected (single)")
            
            # Отправляем подтверждение админу
            await websocket.send_json({
                "type": "connected",
                "message": "Admin WebSocket connected",
                "role": "admin",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Основной цикл для админа
            try:
                while True:
                    try:
                        data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                        try:
                            message = json.loads(data)
                            msg_type = message.get("type")
                            
                            if msg_type == "ping":
                                await websocket.send_json({"type": "pong"})
                                print("💓 Admin heartbeat pong sent")
                            elif msg_type == "subscribe":
                                channel = message.get("channel")
                                print(f"📡 Admin subscribed to {channel}")
                                
                        except json.JSONDecodeError:
                            pass
                            
                    except asyncio.TimeoutError:
                        try:
                            await websocket.send_json({"type": "ping"})
                            print("💓 Admin heartbeat ping sent")
                        except:
                            break
                            
            except WebSocketDisconnect:
                print("🔌 Admin WebSocket disconnected normally")
            finally:
                admin_websocket = None
            return
        
        # 👤 ДЛЯ ОБЫЧНЫХ ПОЛЬЗОВАТЕЛЕЙ (user, courier, supplier)
        # Если есть токен, декодируем user_id
        if token and not user_id_str:
            try:
                from jose import jwt
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id_str = payload.get("sub")
                role = payload.get("role")
                print(f"🔑 Token decoded: user_id={user_id_str}, role={role}")
            except Exception as e:
                print(f"❌ Token decode error: {e}")
        
        # Отправляем приветственное сообщение
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Если нет user_id - используем connect_legacy (для обратной совместимости)
        if not user_id_str:
            await manager.connect_legacy(websocket)
            print("📡 Client connected via legacy mode")
        else:
            user_id = int(user_id_str)
            await manager.connect(websocket, user_type, user_id)
            print(f"📡 {user_type} {user_id} connected")
        
        # Основной цикл для обычных пользователей
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                try:
                    message = json.loads(data)
                    msg_type = message.get("type")
                    
                    if msg_type == "ping":
                        await manager.send_personal_message({"type": "pong"}, websocket)
                        print("💓 Heartbeat pong sent")
                        
                    elif msg_type == "subscribe":
                        channel = message.get("channel")
                        if channel and channel.startswith("supplier_"):
                            supplier_id = channel.replace("supplier_", "")
                            await manager.subscribe_supplier(websocket, supplier_id)
                            print(f"📡 Subscribed to supplier {supplier_id}")
                            
                except json.JSONDecodeError:
                    pass
                    
            except asyncio.TimeoutError:
                try:
                    await manager.send_personal_message({"type": "ping"}, websocket)
                    print("💓 Heartbeat ping sent")
                except:
                    break
                    
    except WebSocketDisconnect:
        print("🔌 WebSocket disconnected normally")
        try:
            if 'user_id_str' in locals() and user_id_str:
                await manager.disconnect(websocket, user_type, int(user_id_str))
            else:
                await manager.disconnect_legacy(websocket)
        except:
            pass
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        try:
            if 'user_id_str' in locals() and user_id_str:
                await manager.disconnect(websocket, user_type, int(user_id_str))
            else:
                await manager.disconnect_legacy(websocket)
        except:
            pass

        # backend/main.py - ДОБАВЬТЕ ЭТУ ФУНКЦИЮ



def decode_polyline(encoded):
    """Декодирует polyline строку в список координат [lat, lon]"""
    index = 0
    lat = 0
    lng = 0
    coordinates = []
    
    while index < len(encoded):
        result = 1
        shift = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result += (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        lat += (result & 1) and ~(result >> 1) or (result >> 1)
        
        result = 1
        shift = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result += (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        lng += (result & 1) and ~(result >> 1) or (result >> 1)
        
        coordinates.append([lat / 100000.0, lng / 100000.0])
    
    return coordinates

async def get_ors_route(start_lat, start_lon, end_lat, end_lon):
    """Получает реальный маршрут от ORS"""
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": ORS_API_KEY,
            "Content-Type": "application/json"
        }
        body = {
            "coordinates": [[start_lon, start_lat], [end_lon, end_lat]]
        }
        
        response = await client.post(
            "https://api.openrouteservice.org/v2/directions/driving-car",
            json=body,
            headers=headers,
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            route = data['routes'][0]
            encoded = route['geometry']
            decoded = decode_polyline(encoded)
            
            waypoints = []
            for point in decoded:
                waypoints.append({"lat": point[0], "lon": point[1]})
            
            distance = route['summary']['distance'] / 1000
            duration = route['summary']['duration'] / 60
            
            print(f"✅ ORS: {len(waypoints)} точек, {distance:.1f} км, {duration:.0f} мин")
            return waypoints, distance, duration
        else:
            print(f"❌ ORS ошибка: {response.status_code}")
            return [], 0, 0
@app.get("/simple-map")
async def simple_map(request: Request):
    return templates.TemplateResponse("test_ors_animation.html", {
        "request": request
    })
@app.get("/track-order/{order_id}")
async def track_order_page(request: Request, order_id: int, lang: str = "kz", db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
    
    supplier_lat = supplier.lat if supplier and supplier.lat else 43.238
    supplier_lon = supplier.lon if supplier and supplier.lon else 76.945
    customer_lat = order.customer_lat if order.customer_lat else 43.258
    customer_lon = order.customer_lon if order.customer_lon else 76.925
    
    # Расстояние
    from math import radians, sin, cos, sqrt, atan2
    def calc_distance(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    
    distance = calc_distance(supplier_lat, supplier_lon, customer_lat, customer_lon)
    eta = int((distance / 40) * 60)
    
    # Статус и прогресс
    status_progress = {
        'pending': 0, 'confirmed': 10, 'preparing': 25,
        'ready_for_pickup': 50, 'out_for_delivery': 70,
        'nearby': 85, 'delivered': 100
    }
    progress = status_progress.get(order.status.value if order.status else 'pending', 0)
    
    status_names = {
        'pending': 'Ожидает', 'confirmed': 'Подтвержден', 'preparing': 'Готовится',
        'ready_for_pickup': 'Готов', 'out_for_delivery': 'В пути',
        'nearby': 'Рядом', 'delivered': 'Доставлен'
    }
    
    return templates.TemplateResponse("delivery_tracking.html", {
        "request": request,
        "order_id": order.id,
        "order_number": order.order_number,
        "supplier_name": supplier.business_name if supplier else "Sarqyn",
        "supplier_lat": supplier_lat,
        "supplier_lon": supplier_lon,
        "customer_lat": customer_lat,
        "customer_lon": customer_lon,
        "customer_address": order.customer_address or "Адрес не указан",
        "current_status": status_names.get(order.status.value if order.status else 'pending', 'Ожидает'),
        "current_progress": progress,
        "total_distance": round(distance, 1),
        "total_eta": eta,
        "lang": request.query_params.get("lang", "ru")
    })
# ============ PASSWORD HASHING ============
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()
# ============ PHONE FORMATTING FUNCTION ============
def format_phone_number(phone: str) -> str:
    """Format phone number to international format"""
    import re
    digits = re.sub(r'\D', '', phone)
    
    # КАЗАХСТАН (+7 или +77 или 8)
    if digits.startswith('77') and len(digits) == 11:
        return '+' + digits
    elif digits.startswith('7') and len(digits) == 11:
        return '+' + digits
    elif digits.startswith('8') and len(digits) == 11:
        return '+7' + digits[1:]  # 87071234567 -> +77071234567
    elif len(digits) == 10:
        return '+77' + digits  # 7071234567 -> +77071234567
    # КЫРГЫЗСТАН (+996)
    elif digits.startswith('996') and len(digits) == 12:
        return '+' + digits
    # УЗБЕКИСТАН (+998)
    elif digits.startswith('998') and len(digits) == 12:
        return '+' + digits
    else:
        return '+' + digits if digits else phone


def verify_password(plain_password: str, hashed_password: str):
    """Проверка пароля"""
    computed_hash = hash_password(plain_password)
    print(f"🔍 VERIFY PASSWORD:")
    print(f"   Plain: {plain_password}")
    print(f"   Computed hash: {computed_hash}")
    print(f"   Stored hash: {hashed_password}")
    print(f"   Match: {computed_hash == hashed_password}")
    return computed_hash == hashed_password

# ============ CREATE DATABASE TABLES ============

# ============ PYDANTIC MODELS ============
class PhoneVerificationRequest(BaseModel):
    phone_number: str

class PhoneRegisterRequest(BaseModel):
    phone_number: str
    full_name: str
    password: str
    verification_code: str

# ============ HELPER FUNCTIONS ============


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in kilometers between two coordinates"""
    return haversine_distance(lat1, lon1, lat2, lon2)

def calculate_eta(distance_km: float, speed_kmh: float = 40) -> int:
    """Calculate estimated time in minutes"""
    time_hours = distance_km / speed_kmh
    return int(time_hours * 60)

def generate_waypoints(start_lat: float, start_lon: float, end_lat: float, end_lon: float, num_points: int = 100):
    """Generate intermediate points between start and end coordinates"""
    waypoints = []
    for i in range(num_points + 1):
        t = i / num_points
        lat = start_lat + (end_lat - start_lat) * t
        lon = start_lon + (end_lon - start_lon) * t
        waypoints.append({"lat": lat, "lon": lon, "progress": round(t * 100, 1)})
    return waypoints

# ============ PHONE REGISTRATION ROUTES ============
@app.get("/register")
async def phone_register_page(request: Request, lang: str = "kz"):
    return templates.TemplateResponse("phone_register.html", {
        "request": request,
        "lang": lang
    })
@app.post("/api/debug-login")
async def debug_login(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    phone = data.get("phone")
    password = data.get("password")
    
    formatted_phone = format_phone_number(phone)
    
    # Найти пользователя
    user = db.query(User).filter(User.phone == formatted_phone).first()
    
    if not user:
        return {"error": "User not found"}
    
    # Хешируем введенный пароль
    computed_hash = hashlib.sha256(password.encode()).hexdigest()
    
    return {
        "user_phone": user.phone,
        "stored_hash": user.password,
        "computed_hash": computed_hash,
        "hashes_match": computed_hash == user.password,
        "password_length": len(password),
        "password_chars": [ord(c) for c in password],
        "password_repr": repr(password)
    }
# В main.py добавьте async к функциям
from backend.twilio_service import send_verification_code, verify_code


# Store verification data temporarily (in production, use Redis or database)
verification_sessions = {}

@app.post("/api/send-verification")
async def send_verification(request: Request):
    """Send SMS verification code"""
    try:
        data = await request.json()
        phone_number = data.get('phone_number')
        
        if not phone_number:
            raise HTTPException(status_code=400, detail="Phone number required")
        
        # Store phone number in session temp storage
        result = await send_verification_code(phone_number)
        
        if result['success']:
            # Store for verification (in production, use Redis with TTL)
            verification_sessions[phone_number] = {
                'code': result.get('fallback_code', '123456') if result.get('demo') else None,
                'expires': datetime.utcnow() + timedelta(minutes=5),
                'verified': False
            }
            
            return {
                "success": True,
                "message": "Verification code sent via SMS",
                "demo": result.get('demo', False)
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to send SMS'))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/verify-phone")
async def verify_phone(request: Request):
    """Verify phone number with code"""
    try:
        data = await request.json()
        phone_number = data.get('phone_number')
        code = data.get('code')
        
        if not phone_number or not code:
            raise HTTPException(status_code=400, detail="Phone number and code required")
        
        # For demo mode, check against stored session
        if phone_number in verification_sessions:
            session = verification_sessions[phone_number]
            if session.get('demo') or session.get('fallback'):
                is_valid = (code == session.get('code', '123456'))
                if is_valid and session['expires'] > datetime.utcnow():
                    session['verified'] = True
                    return {
                        "success": True,
                        "message": "Phone verified successfully"
                    }
                else:
                    raise HTTPException(status_code=400, detail="Code expired or invalid")
        
        # Real Twilio verification
        result = await verify_code(phone_number, code)
        
        if result['success']:
            verification_sessions[phone_number] = {
                'verified': True,
                'expires': datetime.utcnow() + timedelta(hours=24)
            }
            return {
                "success": True,
                "message": "Phone verified successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Invalid verification code'))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# backend/main.py - замените ваш существующий эндпоинт регистрации

# backend/main.py - ДОБАВИТЬ ЭТОТ ЭНДПОИНТ


@app.post("/api/verify-and-register")
async def verify_and_register(request: Request):
    """Регистрация с верификацией кода"""
    try:
        data = await request.json()
        
        phone = data.get("phone", "").strip()
        full_name = data.get("full_name", "").strip()
        password = data.get("password", "")
        verification_code = data.get("verification_code", "")
        
        print(f"📥 Регистрация с верификацией: {phone}")
        print(f"📝 Код: {verification_code}")
        
        if not phone:
            return {"success": False, "detail": "Введите номер телефона"}
        
        if not full_name:
            return {"success": False, "detail": "Введите полное имя"}
        
        if not password or len(password) < 6:
            return {"success": False, "detail": "Пароль должен быть минимум 6 символов"}
        
        if not verification_code or len(verification_code) != 6:
            return {"success": False, "detail": "Введите 6-значный код подтверждения"}
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверка телефона
        cur.execute("SELECT id FROM users WHERE phone = %s", (phone,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return {"success": False, "detail": "Пользователь с таким телефоном уже существует"}
        
        # Создание пользователя (role = 'customer' - VARCHAR)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        name_parts = full_name.split()
        first_name = name_parts[0] if len(name_parts) > 0 else full_name
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        cur.execute("""
            INSERT INTO users (
                first_name,
                last_name,
                full_name,
                phone,
                password,
                role,
                is_active,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, 'customer', true, NOW())
            RETURNING id
        """, (first_name, last_name, full_name, phone, password_hash))
        
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Зарегистрирован новый клиент: {full_name}")
        
        # Создание токена
        token_data = {
            "sub": str(user_id),
            "role": "customer",
            "phone": phone,
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }
        
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "success": True,
            "message": "Регистрация успешна",
            "user_id": user_id,
            "token": token,
            "user": {
                "id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "full_name": full_name,
                "phone": phone,
                "role": "customer"
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        traceback.print_exc()
        return {"success": False, "detail": str(e)}

@app.get("/api/auth/verify-token")
async def verify_token(request: Request):
    """Проверка валидности токена"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"valid": False, "error": "No token provided"}
        
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        return {
            "valid": True,
            "user_id": payload.get("sub"),
            "role": payload.get("role"),
            "phone": payload.get("phone"),
            "exp": payload.get("exp")
        }
        
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token expired"}
    except jwt.JWTError:
        return {"valid": False, "error": "Invalid token"}
    except Exception as e:
        return {"valid": False, "error": str(e)}



async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Получить текущего авторизованного пользователя"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        return {"authenticated": False}
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return {"authenticated": False}
    
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "phone": user.phone,
            "full_name": user.full_name,
            "is_active": user.is_active
        }
    }

from fastapi.responses import JSONResponse

from fastapi.responses import JSONResponse

# backend/main.py - замените ваш существующий эндпоинт логина
@app.post("/api/login")
async def api_login(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        phone = data.get("phone")
        password = data.get("password")
        
        formatted_phone = format_phone_number(phone)
        user = db.query(User).filter(User.phone == formatted_phone).first()
        
        if not user or not verify_password(password, user.password):
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Неверный телефон или пароль"}
            )
        
        # Создаем JWT токен
        access_token = create_access_token(data={
            "sub": str(user.id),
            "role": user.role.value if user.role else "customer"
        })
        
        # ✅ ТОЛЬКО JSON, БЕЗ COOKIES!
        return JSONResponse({
            "success": True,
            "message": "Вход выполнен успешно",
            "token": access_token,
            "user": {
                "id": user.id,
                "phone": user.phone,
                "full_name": user.full_name,
                "role": user.role.value if user.role else "customer"
            }
        })
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Ошибка сервера"}
        )

# backend/main.py - добавьте этот эндпоинт
@app.options("/{path:path}")
async def options_handler():
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400"
        },
        content={}
    )

# ============================================================
# ЭНДПОИНТЫ АУТЕНТИФИКАЦИИ
# ============================================================
verification_codes = {}
# 1. РЕГИСТРАЦИЯ
@app.post("/api/auth/register")
async def register_user(request: Request):
    try:
        data = await request.json()
        
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        phone = data.get("phone", "").strip()
        password = data.get("password", "")
        
        if not first_name or not last_name:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Введите имя и фамилию"}
            )
        
        if not phone:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Введите номер телефона"}
            )
        
        if not password or len(password) < 6:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Пароль должен быть минимум 6 символов"}
            )
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM users WHERE phone = %s", (phone,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Пользователь с таким телефоном уже существует"}
            )
        
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cur.execute("""
            INSERT INTO users (first_name, last_name, phone, password, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, 'customer', true, NOW())
            RETURNING id
        """, (first_name, last_name, phone, password_hash))
        
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        code = str(random.randint(100000, 999999))
        
        verification_codes[phone] = {
            "code": code,
            "user_id": user_id,
            "expires": datetime.utcnow() + timedelta(minutes=5),
            "attempts": 0
        }
        
        print(f"Код для {phone}: {code}")
        
        return JSONResponse(content={
            "success": True,
            "message": "Регистрация успешна. Введите код подтверждения.",
            "user_id": user_id,
            "phone": phone,
            "code": code,
            "first_name": first_name,
            "last_name": last_name
        })
        
    except Exception as e:
        print(f"Ошибка регистрации: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/auth/verify-code")
async def verify_code(request: Request):
    try:
        data = await request.json()
        
        phone = data.get("phone")
        code = data.get("code")
        user_id = data.get("user_id")
        
        if not phone or not code:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Телефон и код обязательны"}
            )
        
        if phone not in verification_codes:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Код не найден. Запросите новый."}
            )
        
        stored_data = verification_codes[phone]
        
        if stored_data["expires"] < datetime.utcnow():
            del verification_codes[phone]
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Код истек. Запросите новый."}
            )
        
        if stored_data["attempts"] >= 5:
            del verification_codes[phone]
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Слишком много попыток. Запросите новый код."}
            )
        
        if stored_data["code"] != code:
            stored_data["attempts"] += 1
            verification_codes[phone] = stored_data
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Неверный код. Осталось попыток: {5 - stored_data['attempts']}"}
            )
        
        # ✅ ПРОСТО ОБНОВЛЯЕМ phone_verified (БЕЗ verified_at)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE users 
            SET phone_verified = true
            WHERE id = %s
        """, (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        del verification_codes[phone]
        
        from jose import jwt
        token_data = {
            "sub": str(user_id),
            "role": "customer",
            "phone": phone,
            "exp": datetime.utcnow() + timedelta(days=30)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, first_name, last_name, phone, role
            FROM users 
            WHERE id = %s
        """, (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        return JSONResponse(content={
            "success": True,
            "message": "Код подтвержден успешно",
            "token": token,
            "user": {
                "id": user["id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "phone": user["phone"],
                "role": user["role"] or "customer"
            }
        })
        
    except Exception as e:
        print(f"Ошибка верификации: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )


@app.post("/api/auth/resend-code")
async def resend_code(request: Request):
    try:
        data = await request.json()
        phone = data.get("phone")
        
        if not phone:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Телефон обязателен"}
            )
        
        if phone in verification_codes:
            del verification_codes[phone]
        
        code = str(random.randint(100000, 999999))
        
        verification_codes[phone] = {
            "code": code,
            "expires": datetime.utcnow() + timedelta(minutes=5),
            "attempts": 0
        }
        
        print(f"Новый код для {phone}: {code}")
        
        return JSONResponse(content={
            "success": True,
            "message": "Новый код отправлен",
            "code": code,
            "expires_in": 300
        })
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

# 2. ЛОГИН
# backend/main.py - ИСПРАВЛЕННЫЙ ЛОГИН

from datetime import datetime, timedelta  # ✅ В САМОМ НАЧАЛЕ
@app.post("/api/auth/login")
async def login_user(request: Request):
    try:
        data = await request.json()
        
        phone = data.get("phone", "").strip()
        password = data.get("password", "")
        
        print(f"📥 Логин: {phone}")
        
        if not phone or not password:
            return {"success": False, "detail": "Заполните все поля"}
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. ПОЛУЧАЕМ ПОЛЬЗОВАТЕЛЯ
        cur.execute("""
            SELECT id, first_name, last_name, phone, password, role, is_active
            FROM users
            WHERE phone = %s
        """, (phone,))
        
        user = cur.fetchone()
        
        if not user:
            cur.close()
            conn.close()
            return {"success": False, "detail": "Неверный телефон или пароль"}
        
        # 2. ПРОВЕРЯЕМ ПАРОЛЬ
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if user.get("password") != password_hash:
            cur.close()
            conn.close()
            return {"success": False, "detail": "Неверный телефон или пароль"}
        
        # 3. ✅ ЕСЛИ ДЕАКТИВИРОВАН - АКТИВИРУЕМ
        if not user.get("is_active"):
            print(f"⚠️ Пользователь {phone} деактивирован. Активируем...")
            
            # Закрываем старый курсор, открываем новый для UPDATE
            cur.close()
            cur = conn.cursor()
            cur.execute("""
                UPDATE users 
                SET is_active = true 
                WHERE id = %s
            """, (user["id"],))
            conn.commit()
            
            print(f"✅ Пользователь {phone} активирован")
            
            # Обновляем данные пользователя
            user["is_active"] = True
        
        cur.close()
        conn.close()
        
        # 4. СОЗДАЕМ ТОКЕН
        from jose import jwt
        from datetime import datetime, timedelta
        
        token_data = {
            "sub": str(user["id"]),
            "role": user["role"] or "customer",
            "phone": user["phone"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "exp": datetime.utcnow() + timedelta(days=30)
        }
        
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user["id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "phone": user["phone"],
                "role": user["role"] or "customer",
                "is_active": user["is_active"]
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка логина: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "detail": str(e)}
    
# 3. ПОЛУЧЕНИЕ ПРОФИЛЯ
@app.get("/api/auth/me")
async def get_current_user(request: Request):
    """Получение текущего пользователя"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"success": False, "detail": "Unauthorized"}
        
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id = payload.get("sub")
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, first_name, last_name, phone, role, is_active
            FROM users
            WHERE id = %s
        """, (user_id,))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user:
            return {"success": False, "detail": "User not found"}
        
        return {
            "success": True,
            "user": {
                "id": user["id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "phone": user["phone"],
                "role": user["role"] or "customer"
            }
        }
        
    except Exception as e:
        return {"success": False, "detail": str(e)}


# 4. ВЫХОД
@app.post("/api/auth/logout")
async def logout_user():
    """Выход пользователя"""
    return {"success": True, "message": "Logged out"}

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    response.delete_cookie("user_phone")
    response.delete_cookie("user_name")
    return response

# ============ DELIVERY TRACKING ROUTES ============
@app.post("/api/delivery/{order_id}/start")
async def start_real_delivery(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Начать реальную доставку заказа"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
        
        # Проверяем что это курьер
        if payload.get("role") != "courier":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Not a courier"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        from datetime import datetime
        import math
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        # Проверяем что заказ назначен этому курьеру
        if order.assigned_courier_id != int(user_id):
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Order not assigned to you"}
            )
        
        supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        if not supplier:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Supplier not found"}
            )
        
        if not supplier.lat or not supplier.lon:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Supplier location not available"}
            )
        
        if not order.customer_lat or not order.customer_lon:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Customer location not available"}
            )
        
        # Расчет расстояния и ETA
        distance = calculate_distance(supplier.lat, supplier.lon, order.customer_lat, order.customer_lon)
        eta_minutes = calculate_eta(distance, 40)
        
        # Генерация промежуточных точек
        waypoints = generate_waypoints(supplier.lat, supplier.lon, order.customer_lat, order.customer_lon, 100)
        
        # Сохраняем данные в кэш
        if 'delivery_cache' not in globals():
            global delivery_cache
            delivery_cache = {}
        
        delivery_cache[str(order_id)] = {
            "waypoints": waypoints,
            "current_index": 0,
            "total_distance": distance,
            "eta_minutes": eta_minutes,
            "is_active": True,
            "started_at": datetime.utcnow().isoformat()
        }
        
        # ✅ ИСПРАВЛЕНО: статус как строка (БЕЗ ENUM)
        order.status = "out_for_delivery"
        order.delivery_started_at = datetime.utcnow()
        order.driver_lat = supplier.lat
        order.driver_lon = supplier.lon
        
        # Обновляем статус курьера
        courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
        if courier:
            courier.current_order_status = "out_for_delivery"
            courier.is_available = False
        
        db.commit()
        
        print(f"✅ Курьер начал доставку заказа #{order.order_number}, ETA: {eta_minutes} мин")
        
        # Уведомляем клиента
        try:
            await manager.broadcast({
                "type": "delivery_started",
                "order_id": order.id,
                "order_number": order.order_number,
                "eta_minutes": eta_minutes,
                "distance_km": round(distance, 2)
            }, channel=f"user_{order.user_id}")
        except Exception as e:
            print(f"⚠️ Ошибка отправки уведомления клиенту: {e}")
        
        return {
            "success": True,
            "order_id": order_id,
            "order_number": order.order_number,
            "distance_km": round(distance, 2),
            "eta_minutes": eta_minutes,
            "status": order.status
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

@app.get("/api/delivery/{order_id}/position")
async def get_delivery_position(order_id: int, request: Request):
    """Получить текущую позицию доставки - ЧИСТЫЙ SQL"""
    
    cache_key = str(order_id)
    
    # Проверяем кэш
    if cache_key in delivery_cache and delivery_cache[cache_key]["is_active"]:
        waypoints = delivery_cache[cache_key]["waypoints"]
        current_index = delivery_cache[cache_key]["current_index"]
        
        if current_index < len(waypoints):
            current_pos = waypoints[current_index]
            delivery_cache[cache_key]["current_index"] = current_index + 1
            
            # ✅ Обновляем позицию в БД через чистый SQL
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE orders 
                    SET driver_lat = %s,
                        driver_lon = %s,
                        last_location_update = NOW()
                    WHERE id = %s
                """, (current_pos["lat"], current_pos["lon"], order_id))
                conn.commit()
            except Exception as e:
                print(f"❌ Ошибка обновления позиции: {e}")
            finally:
                cur.close()
                conn.close()
            
            return {
                "success": True,
                "lat": current_pos["lat"],
                "lon": current_pos["lon"],
                "progress": current_pos["progress"],
                "remaining_steps": len(waypoints) - current_index,
                "is_complete": False
            }
        else:
            delivery_cache[cache_key]["is_active"] = False
            
            # ✅ Завершаем доставку - БЕЗ delivery_status!
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE orders 
                    SET status = 'delivered',
                        delivered_at = NOW()
                    WHERE id = %s AND status != 'delivered'
                """, (order_id,))
                
                # Добавляем запись в трекинг
                cur.execute("""
                    INSERT INTO order_tracking 
                    (order_id, status, message, created_at)
                    VALUES (%s, 'delivered', 'Доставка завершена (автоматически)', NOW())
                """, (order_id,))
                
                conn.commit()
            except Exception as e:
                print(f"❌ Ошибка завершения доставки: {e}")
            finally:
                cur.close()
                conn.close()
            
            return {"success": True, "is_complete": True}
    
    # ✅ Проверяем статус через чистый SQL
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT status FROM orders WHERE id = %s
        """, (order_id,))
        order = cur.fetchone()
    except Exception as e:
        print(f"❌ Ошибка проверки статуса: {e}")
        return {"success": False, "is_complete": False}
    finally:
        cur.close()
        conn.close()
    
    if order and order[0] == 'delivered':
        return {"success": True, "is_complete": True}
    
    return {"success": False, "is_complete": False}
@app.get("/delivery/track/{order_id}")
async def delivery_tracking(request: Request, order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
    
    # Координаттарды тексеру
    supplier_lat = supplier.lat if supplier and supplier.lat else 43.238
    supplier_lon = supplier.lon if supplier and supplier.lon else 76.945
    customer_lat = order.customer_lat if order.customer_lat else 43.258
    customer_lon = order.customer_lon if order.customer_lon else 76.925
    
    # Қашықтықты есептеу
    from math import radians, sin, cos, sqrt, atan2
    def calc_distance(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    
    distance = calc_distance(supplier_lat, supplier_lon, customer_lat, customer_lon)
    eta = int((distance / 40) * 60)
    
    # Статус бойынша прогресс
    status_progress = {
        'pending': 0, 'confirmed': 10, 'preparing': 25,
        'ready_for_pickup': 50, 'out_for_delivery': 70,
        'nearby': 85, 'delivered': 100
    }
    progress = status_progress.get(order.status.value if order.status else 'pending', 0)
    
    status_names = {
        'pending': 'Күтілуде', 'confirmed': 'Расталды', 'preparing': 'Дайындалуда',
        'ready_for_pickup': 'Дайын', 'out_for_delivery': 'Жолда',
        'nearby': 'Жақын жерде', 'delivered': 'Жеткізілді'
    }
    
    return templates.TemplateResponse("delivery_tracking_real.html", {
        "request": request,
        "order_id": order.id,
        "order_number": order.order_number,
        "supplier_name": supplier.business_name if supplier else "Sarqyn",
        "supplier_lat": supplier_lat,
        "supplier_lon": supplier_lon,
        "customer_lat": customer_lat,
        "customer_lon": customer_lon,
        "customer_address": order.customer_address or "Мекенжай көрсетілмеген",
        "current_status": status_names.get(order.status.value if order.status else 'pending', 'Белгісіз'),
        "current_progress": progress,
        "total_distance": round(distance, 1),
        "total_eta": eta,
        "lang": request.query_params.get("lang", "ru")
    })
        
    
from typing import Optional

@app.get("/api/suppliers/nearby")
async def get_nearby_suppliers(
    lat: Optional[str] = None,  # ← ВРЕМЕННО как строка
    lon: Optional[str] = None, 
    radius: float = 10,
    db: Session = Depends(get_db)
):
    """Получить поставщиков рядом с пользователем"""
    
    # ✅ Проверяем и конвертируем
    if lat is None or lon is None:
        print("⚠️ Координаты не переданы")
        return {"count": 0, "suppliers": []}
    
    try:
        lat_float = float(lat)
        lon_float = float(lon)
    except (ValueError, TypeError) as e:
        print(f"❌ Ошибка конвертации: lat={lat}, lon={lon}")
        return {"count": 0, "suppliers": [], "error": "Invalid coordinates"}
    
    print(f"🔍 Поиск поставщиков рядом с {lat_float}, {lon_float}, радиус {radius}км")
    
    # Получаем всех активных поставщиков
    all_suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    
    nearby = []
    for supplier in all_suppliers:
        if not supplier.lat or not supplier.lon:
            continue
        
        # Рассчитываем расстояние
        distance = haversine_distance(lat_float, lon_float, supplier.lat, supplier.lon)
        
        if distance <= radius:
            active_bags = db.query(SurpriseBag).filter(
                SurpriseBag.supplier_id == supplier.id,
                SurpriseBag.is_active == True,
                SurpriseBag.available_quantity > 0
            ).all()
            
            if active_bags:
                nearby.append({
                    "id": supplier.id,
                    "business_name": supplier.business_name,
                    "address": supplier.address or "",
                    "lat": supplier.lat,
                    "lon": supplier.lon,
                    "distance_km": round(distance, 2),
                    "rating": supplier.rating or 0,
                    "surprise_bags_count": len(active_bags)
                })
    
    # Сортируем по расстоянию
    nearby.sort(key=lambda x: x["distance_km"])
    print(f"🎯 ИТОГО: {len(nearby)} поставщиков")
    
    return {"count": len(nearby), "suppliers": nearby}


# ============ API ROUTES ============
@app.get("/api/suppliers")
async def get_all_suppliers(db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    result = []
    for supplier in suppliers:
        result.append({
            "id": supplier.id,
            "business_name": supplier.business_name,
            "business_type": supplier.business_type,
            "city": getattr(supplier, 'city', 'Unknown'),
            "address": supplier.address,
            "lat": supplier.lat,
            "lon": supplier.lon,
            "rating": supplier.rating,
            "is_active": supplier.is_active
        })
    return result

# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ







@app.get("/api/surprise-bags/{bag_id}")
async def get_surprise_bag(bag_id: int, db: Session = Depends(get_db)):
    """Получить конкретный сюрприз с учетом типа"""
    
    bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
    if not bag:
        raise HTTPException(status_code=404, detail="Surprise bag not found")
    
    supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
    
    # ✅ Получаем состав ТОЛЬКО если hide_contents == False (search type)
    items_list = []
    if not bag.hide_contents:
        items = db.query(SurpriseBagItem).filter(SurpriseBagItem.surprise_bag_id == bag_id).all()
        items_list = [
            {
                "product_id": item.product_id,
                "name": item.product_name,
                "price": item.product_price,
                "quantity": item.quantity
            }
            for item in items
        ]
    
    return {
        "id": bag.id,
        "supplier_id": bag.supplier_id,
        "supplier_name": supplier.business_name if supplier else "Unknown",
        "name": bag.name,
        "description": bag.description,
        "original_price": bag.original_price,
        "discounted_price": bag.discounted_price,
        "discount_percentage": bag.discount_percentage,
        "image_url": bag.image_url,
        "available_quantity": bag.available_quantity,
        "hide_contents": bag.hide_contents,
        "items": items_list,
        "surprise_badge": "🎁 Surprise" if bag.hide_contents else "📦 Standard"
    }
# ============ ОЦЕНКА МАГАЗИНОВ ============

@app.get("/api/suppliers/{supplier_id}/rating")
async def get_supplier_rating(
    supplier_id: int, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """Получить рейтинг магазина и оценку текущего пользователя"""
    
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        return JSONResponse(status_code=404, content={"success": False, "message": "Supplier not found"})
    
    # Получаем оценку текущего пользователя из Bearer token
    user_rating = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from jose import jwt
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            
            review = db.query(SupplierReview).filter(
                SupplierReview.supplier_id == supplier_id,
                SupplierReview.user_id == int(user_id)
            ).first()
            if review:
                user_rating = review.rating
        except:
            pass
    
    return {
        "success": True,
        "rating": supplier.rating or 0,
        "total_reviews": supplier.total_reviews or 0,
        "user_rating": user_rating
    }



@app.post("/api/suppliers/{supplier_id}/rate")
async def rate_supplier(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Оценить магазин (поставить звезды 1-5)"""
    
    # Проверяем Bearer token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"success": False, "message": "Unauthorized"})
    
    token = auth_header.split(" ")[1]
    
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except:
        return JSONResponse(status_code=401, content={"success": False, "message": "Invalid token"})
    
    data = await request.json()
    rating = data.get("rating")
    
    if not rating or rating < 1 or rating > 5:
        return JSONResponse(status_code=400, content={"success": False, "message": "Rating must be between 1 and 5"})
    
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        return JSONResponse(status_code=404, content={"success": False, "message": "Supplier not found"})
    
    # Проверяем, оценивал ли пользователь уже этот магазин
    existing_review = db.query(SupplierReview).filter(
        SupplierReview.supplier_id == supplier_id,
        SupplierReview.user_id == int(user_id)
    ).first()
    
    if existing_review:
        # Обновляем существующую оценку
        existing_review.rating = rating
        existing_review.updated_at = datetime.utcnow()
        
        # Пересчитываем средний рейтинг
        all_reviews = db.query(SupplierReview).filter(
            SupplierReview.supplier_id == supplier_id
        ).all()
        total_rating = sum(r.rating for r in all_reviews)
        supplier.rating = total_rating / len(all_reviews)
    else:
        # Новая оценка
        new_review = SupplierReview(
            supplier_id=supplier_id,
            user_id=int(user_id),
            rating=rating,
            created_at=datetime.utcnow()
        )
        db.add(new_review)
        
        # Пересчитываем средний рейтинг
        all_reviews = db.query(SupplierReview).filter(
            SupplierReview.supplier_id == supplier_id
        ).all()
        total_rating = sum(r.rating for r in all_reviews) + rating
        supplier.total_reviews = len(all_reviews) + 1
        supplier.rating = total_rating / supplier.total_reviews
    
    db.commit()
    
    return {
        "success": True,
        "rating": supplier.rating,
        "total_reviews": supplier.total_reviews,
        "user_rating": rating,
        "message": "Спасибо за оценку магазина!"
    }





# ============ ОЦЕНКА СЮРПРИЗОВ ============

# @app.get("/api/surprise-bags/{bag_id}/rating")
# async def get_surprise_bag_rating(
#     bag_id: int,
#     request: Request,
#     db: Session = Depends(get_db)
# ):
#     """Получить рейтинг сюрприза"""
    
#     bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
#     if not bag:
#         return JSONResponse(
#             status_code=404,
#             content={"success": False, "message": "Surprise bag not found"}
#         )
    
#     # Получаем оценку текущего пользователя
#     user_rating = None
#     auth_header = request.headers.get("Authorization")
#     if auth_header and auth_header.startswith("Bearer "):
#         token = auth_header.split(" ")[1]
#         try:
#             from jose import jwt
#             payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#             user_id = payload.get("sub")
            
#             review = db.query(SurpriseBagReview).filter(
#                 SurpriseBagReview.surprise_bag_id == bag_id,
#                 SurpriseBagReview.user_id == int(user_id)
#             ).first()
#             if review:
#                 user_rating = review.rating
#         except:
#             pass
    
#     return {
#         "success": True,
#         "rating": bag.rating or 0,
#         "total_reviews": bag.total_reviews or 0,
#         "user_rating": user_rating
#     }


@app.post("/api/surprise-bags/{bag_id}/rate")
async def rate_surprise_bag(
    bag_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Оценить сюрприз (поставить звезды 1-5)"""
    
    # Проверяем Bearer token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"success": False, "message": "Unauthorized"})
    
    token = auth_header.split(" ")[1]
    
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except:
        return JSONResponse(status_code=401, content={"success": False, "message": "Invalid token"})
    
    data = await request.json()
    rating = data.get("rating")
    
    if not rating or rating < 1 or rating > 5:
        return JSONResponse(status_code=400, content={"success": False, "message": "Rating must be between 1 and 5"})
    
    bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
    if not bag:
        return JSONResponse(status_code=404, content={"success": False, "message": "Surprise bag not found"})
    
    existing_review = db.query(SurpriseBagReview).filter(
        SurpriseBagReview.surprise_bag_id == bag_id,
        SurpriseBagReview.user_id == int(user_id)
    ).first()
    
    if existing_review:
        existing_review.rating = rating
        existing_review.updated_at = datetime.utcnow()
        
        all_reviews = db.query(SurpriseBagReview).filter(
            SurpriseBagReview.surprise_bag_id == bag_id
        ).all()
        total_rating = sum(r.rating for r in all_reviews)
        bag.rating = total_rating / len(all_reviews)
    else:
        new_review = SurpriseBagReview(
            surprise_bag_id=bag_id,
            user_id=int(user_id),
            rating=rating,
            created_at=datetime.utcnow()
        )
        db.add(new_review)
        
        all_reviews = db.query(SurpriseBagReview).filter(
            SurpriseBagReview.surprise_bag_id == bag_id
        ).all()
        total_rating = sum(r.rating for r in all_reviews) + rating
        bag.total_reviews = len(all_reviews) + 1
        bag.rating = total_rating / bag.total_reviews
    
    db.commit()
    
    return {
        "success": True,
        "rating": bag.rating,
        "total_reviews": bag.total_reviews,
        "user_rating": rating,
        "message": "Спасибо за оценку сюрприза!"
    }
# backend/main.py - обновите nearby suppliers
# backend/main.py - ИСПРАВЛЕННЫЙ эндпоинт


# ============ HOME PAGE ============
@app.get("/")
async def home(request: Request, lang: str = "kz", category: str = "all", db: Session = Depends(get_db)):

    
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')
    address = request.query_params.get('address', '')
    
    # Get current user from cookie
    user_id = request.cookies.get("user_id")
    user = None
    if user_id:
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
        except:
            pass
    
    suppliers_list = []
    
    if lat and lon:
        lat = float(lat)
        lon = float(lon)
        all_suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
        
        for supplier in all_suppliers:
            if supplier.lat and supplier.lon:
                distance = haversine_distance(lat, lon, supplier.lat, supplier.lon)
                if distance <= 10:
                    active_bags = db.query(SurpriseBag).filter(
                        SurpriseBag.supplier_id == supplier.id,
                        SurpriseBag.is_active == True,
                        SurpriseBag.available_quantity > 0
                    ).all()
                    
                    if active_bags:
                        suppliers_list.append({
                            "id": supplier.id,
                            "business_name": supplier.business_name,
                            "distance": round(distance, 1),
                            "rating": supplier.rating,
                            "cover_image": supplier.cover_image,
                            "surprise_bags": [
                                {
                                    "id": bag.id,
                                    "name": bag.name,
                                    "original_price": bag.original_price,
                                    "discounted_price": bag.discounted_price,
                                    "discount_percentage": bag.discount_percentage,
                                    "image_url": bag.image_url,
                                    "available_quantity": bag.available_quantity
                                } for bag in active_bags
                            ]
                        })
    
    foods = db.query(Food).all()
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
            "rating": 4.5
        })
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "foods": foods_list,
        "suppliers": suppliers_list,
        "categories": categories,
        "active_category": category,
        "lang": lang,
        "user_address": address,
        "user_logged_in": user is not None,
        "user_name": user.full_name if user else None,
        "user_phone": user.phone if user else None
    })
@app.get("/profile")
async def profile_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "lang": request.query_params.get("lang", "kz")
    })
@app.get("/logout")
async def logout(request: Request):
    """Выход из системы"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    response.delete_cookie("user_phone")
    response.delete_cookie("user_email")
    response.delete_cookie("user_name")
    response.delete_cookie("supplier_id")
    response.delete_cookie("supplier_city")
    return response

# backend/main.py - add this endpoint
@app.get("/api/my-orders")
async def get_my_orders(request: Request):
    """Получить заказы текущего пользователя"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, order_number, status, created_at, amount_paid,
               assigned_courier_id, address, delivery_type
        FROM orders 
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    
    orders = cur.fetchall()
    cur.close()
    conn.close()
    
    return {
        "success": True,
        "orders": [
            {
                "id": o[0],
                "order_number": o[1],
                "status": o[2],
                "created_at": o[3].isoformat() if o[3] else None,
                "amount": float(o[4]) if o[4] else 0,
                "courier_id": o[5],
                "address": o[6],
                "delivery_type": o[7]
            }
            for o in orders
        ]
    }

@app.get("/api/my_orders")
async def get_my_orders_json(request: Request, db: Session = Depends(get_db)):
    """API endpoint для получения заказов в JSON формате"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"error": "Not authenticated", "orders": []}
        )
    
    user_id = int(user_id)
    orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
    
    orders_list = []
    for order in orders:
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
        supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        
        orders_list.append({
            "id": order.id,
            "order_number": order.order_number or f"ORD-{order.id}",
            "bag_name": bag.name if bag else "Surprise Bag",
            "supplier_name": supplier.business_name if supplier else "Restaurant",
            "amount_paid": order.amount_paid or 0,
            "status": order.status.value if order.status else "pending",
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "customer_address": order.customer_address or "Address not specified"
        })
    
    return {"orders": orders_list}

# ============ TRACK ORDER PAGE ============
# Add these imports at the top

# Add these endpoints to your existing FastAPI app
@app.get("/api/suppliers/bag/{bag_id}")
async def get_bag_by_id(bag_id: int, db: Session = Depends(get_db)):
    bag = db.query(SurpriseBag).filter(
        SurpriseBag.id == bag_id,
        SurpriseBag.is_active == True,
        SurpriseBag.available_quantity > 0
    ).first()
    
    if not bag:
        raise HTTPException(status_code=404, detail="Surprise bag not found")
    
    supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
    
    return {
        "id": bag.id,
        "name": bag.name,
        "description": bag.description,
        "original_price": bag.original_price,
        "discounted_price": bag.discounted_price,
        "discount_percentage": bag.discount_percentage,
        "image_url": bag.image_url,
        "supplier_name": supplier.business_name if supplier else "",
        "supplier_id": supplier.id if supplier else None,
        "available_quantity": bag.available_quantity,
        "pickup_start_time": bag.pickup_start_time,
        "pickup_end_time": bag.pickup_end_time,
        "is_active": bag.is_active
    }

# Get nearby suppliers

# ============ WEBSOCKET FOR SUPPLIERS ============

# Хранилище для supplier WebSocket соединений
supplier_connections = {}  # {supplier_id: [websocket1, websocket2]}
# backend/main.py - исправленный Supplier WebSocket


@app.websocket("/ws/supplier")
async def supplier_websocket(websocket: WebSocket):
    """WebSocket для поставщиков"""
    
    # ✅ Сначала ACCEPT
    try:
        await websocket.accept()
        print("✅ Supplier WebSocket accepted")
    except Exception as e:
        print(f"❌ Failed to accept supplier WebSocket: {e}")
        return
    
    # Получаем supplier_id из query params
    supplier_id = websocket.query_params.get("supplier_id")
    
    if not supplier_id:
        await websocket.close(code=1008, reason="supplier_id required")
        return
    
    # ✅ Используем ConnectionManager (вся логика уже внутри)
    await manager.connect(websocket, "supplier", int(supplier_id))
    
    try:
        await websocket.send_json({
            "type": "connected",
            "supplier_id": supplier_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        # ✅ ДОБАВИТЬ await
        await manager.disconnect(websocket, "supplier", int(supplier_id))


        
# ============ ФОНОВАЯ ОЧИСТКА МЕРТВЫХ СОЕДИНЕНИЙ ============
async def cleanup_dead_connections():
    """Фоновая очистка мертвых WebSocket соединений"""
    while True:
        await asyncio.sleep(300)  # 5 минут
        
        dead = []
        for conn in active_connections:
            try:
                await asyncio.wait_for(conn.send_json({"type": "ping"}), timeout=1.0)
            except:
                dead.append(conn)
        
        for conn in dead:
            active_connections.discard(conn)
        
        if dead:
            print(f"🧹 Очищено {len(dead)} мертвых соединений")


# Функция для отправки уведомлений поставщикам
async def notify_supplier_new_order(supplier_id: int, order_data: dict):
    """Отправить уведомление поставщику о новом заказе"""
    supplier_id_str = str(supplier_id)
    
    if supplier_id_str in supplier_connections:
        disconnected = []
        for connection in supplier_connections[supplier_id_str]:
            try:
                await connection.send_json({
                    "type": "new_order",
                    "data": order_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
                print(f"📢 Notified supplier {supplier_id} about new order")
            except:
                disconnected.append(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            if conn in supplier_connections[supplier_id_str]:
                supplier_connections[supplier_id_str].remove(conn)
        
        if not supplier_connections[supplier_id_str]:
            del supplier_connections[supplier_id_str]
    else:
        print(f"⚠️ Supplier {supplier_id} has no active WebSocket connection")


# Альтернативная простая версия (если WebSocket сложно настроить)
async def notify_supplier_new_order_simple(supplier_id: int, order_data: dict):
    """Простая версия - только лог, без WebSocket"""
    print(f"📢 [NEW ORDER] Supplier {supplier_id}: {order_data}")
    # Здесь можно добавить email или SMS уведомление
    pass
class OrderCreate(BaseModel):
    bag_id: int
    lat: float
    lon: float
    address: str
from fastapi import Request  # Убедитесь, что импортирован

# backend/main.py - исправленный эндпоинт создания заказа


class OrderCreate(BaseModel):
    bag_id: int
    lat: float
    lon: float
    address: str

class OrderResponse(BaseModel):
    order_id: int
    status: str
    message: str




@app.get("/api/geocode")
async def geocode(lat: float, lon: float):
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&accept-language=ru"
        )
        data = response.json()
        city = data.get('address', {}).get('city', 'Не определен')
        return {"city": city}
# ============================================================
# НОВЫЙ ЭНДПОИНТ ДЛЯ ЗАКАЗА (РАБОТАЕТ 100%)
# ============================================================

@app.post("/api/create-order-now")
async def create_order_now(request: Request, db: Session = Depends(get_db)):
    """Создание заказа - НОВЫЙ РАБОЧИЙ ЭНДПОИНТ"""
    
    print("🔥 /api/create-order-now ВЫЗВАН!")
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
        print(f"✅ User ID: {user_id}")
    except Exception as e:
        print(f"❌ Token error: {e}")
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Token error: {str(e)}"}
        )
    
    try:
        data = await request.json()
        print(f"📦 Data: {data}")
        
        bag_id = data.get("bag_id")
        delivery_type = data.get("delivery_type", "pickup")
        customer_address = data.get("address", "Самовывоз")
        customer_lat = data.get("lat")
        customer_lon = data.get("lon")
        
        if not bag_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "bag_id is required"}
            )
        
        # Проверяем сюрприз
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
        if not bag:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Товар не найден"}
            )
        
        if bag.available_quantity < 1 or not bag.is_active:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Товар недоступен"}
            )
        
        import secrets
        order_number = f"ORD-{secrets.token_hex(4).upper()}"
        now = datetime.utcnow()
        
        # Уменьшаем количество
        bag.available_quantity -= 1
        if bag.available_quantity <= 0:
            bag.is_active = False
        
        # Создаем резервацию
        reservation = TemporaryReservation(
            bag_id=bag_id,
            user_id=int(user_id),
            quantity=1,
            reserved_at=now,
            expires_at=now + timedelta(minutes=15),
            is_paid=False
        )
        db.add(reservation)
        db.flush()
        
        # Создаем заказ
        order = Order(
            user_id=int(user_id),
            supplier_id=bag.supplier_id,
            surprise_bag_id=bag.id,
            order_number=order_number,
            status="pending",
            payment_status="pending",
            customer_address=customer_address if customer_address else "Самовывоз",
            customer_lat=customer_lat if delivery_type == "delivery" else None,
            customer_lon=customer_lon if delivery_type == "delivery" else None,
            amount_paid=bag.discounted_price,
            delivery_type=delivery_type,
            created_at=now
        )
        db.add(order)
        db.commit()
        
        print(f"✅ Order created: {order_number}")
        
        return JSONResponse(content={
            "success": True,
            "order_id": order.id,
            "order_number": order_number,
            "status": "pending",
            "message": "Order created successfully"
        })
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": f"Ошибка: {str(e)}"}
        )

@app.get("/api/orders/{order_id}")
async def get_order_by_id(order_id: int, request: Request):
    """Получить заказ по ID - ЧИСТЫЙ SQL БЕЗ delivery_status"""
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT 
                o.id,
                o.order_number,
                o.status::text as status,
                o.amount_paid,
                o.payment_status,
                o.customer_address,
                o.customer_lat,
                o.customer_lon,
                o.created_at,
                o.delivery_deadline,
                o.delivery_type,
                o.supplier_id,
                o.user_id,
                s.business_name as supplier_name,
                s.address as supplier_address,
                s.lat as supplier_lat,
                s.lon as supplier_lon,
                sb.name as bag_name
            FROM orders o
            LEFT JOIN suppliers s ON s.id = o.supplier_id
            LEFT JOIN surprise_bags sb ON sb.id = o.surprise_bag_id
            WHERE o.id = %s
        """, (order_id,))
        
        order = cur.fetchone()
        
        if not order:
            cur.close()
            conn.close()
            return JSONResponse(
                status_code=404,
                content={"error": "Order not found", "order_id": order_id}
            )
        
        cur.close()
        conn.close()
        
        return {
            "id": order['id'],
            "order_id": order['id'],
            "order_number": order['order_number'],
            "status": order['status'] or "pending",
            "amount_paid": float(order['amount_paid']) if order['amount_paid'] else 0,
            "payment_status": order['payment_status'] or "pending",
            "customer_address": order['customer_address'] or "Адрес не указан",
            "customer_lat": float(order['customer_lat']) if order['customer_lat'] else None,
            "customer_lon": float(order['customer_lon']) if order['customer_lon'] else None,
            "created_at": order['created_at'].isoformat() if order['created_at'] else None,
            "delivery_deadline": order['delivery_deadline'].isoformat() if order['delivery_deadline'] else None,
            "delivery_type": order['delivery_type'] or "pickup",
            "supplier": {
                "id": order['supplier_id'],
                "business_name": order['supplier_name'],
                "address": order['supplier_address'],
                "lat": float(order['supplier_lat']) if order['supplier_lat'] else None,
                "lon": float(order['supplier_lon']) if order['supplier_lon'] else None
            },
            "bag_name": order['bag_name'] or "Surprise Bag"
        }
        
    except Exception as e:
        cur.close()
        conn.close()
        print(f"❌ Error in get_order_by_id: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "order_id": order_id}
        )

        
@app.get("/test-ors")
async def test_ors():
    import httpx
    import json
    
    ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjYyMDU3ZGE4OTkxODQ2M2JhNmVlZDgzM2QzMDE2OTYwIiwiaCI6Im11cm11cjY0In0="
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": ORS_API_KEY,
            "Content-Type": "application/json"
        }
        body = {
            "coordinates": [[76.945, 43.238], [76.925, 43.258]]
        }
        
        response = await client.post(
            "https://api.openrouteservice.org/v2/directions/driving-car",
            json=body,
            headers=headers,
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            encoded = data['routes'][0]['geometry']
            return {"status": "ok", "encoded": encoded[:100]}
        else:
            return {"status": "error", "code": response.status_code, "text": response.text}



def calculate_distance(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def calculate_eta(distance_km, speed_kmh=40):
    return int((distance_km / speed_kmh) * 60)
# ============ ADMIN ROUTES ============


@app.post("/admin/add-food")
async def add_food(
    name_ru: str = Form(...),
    name_kz: str = Form(...),
    price: float = Form(...),
    image: str = Form(...),
    discount: int = Form(0),
    db: Session = Depends(get_db)
):
    new_food = Food(name_ru=name_ru, name_kz=name_kz, price=price, image=image, discount=discount)
    db.add(new_food)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/admin/delete-food/{food_id}")
async def delete_food(food_id: int, db: Session = Depends(get_db)):
    food = db.query(Food).filter(Food.id == food_id).first()
    if food:
        db.delete(food)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)
# backend/main.py - ИСПРАВЛЕННАЯ РЕГИСТРАЦИЯ ПОСТАВЩИКА

@app.post("/supplier/register", response_class=HTMLResponse)
async def supplier_register_form_handler(
    request: Request,
    db: Session = Depends(get_db)
):
    """Обработка POST запроса с HTML формы регистрации поставщика"""
    
    try:
        # Получаем данные из формы
        form_data = await request.form()
        
        print(f"📥 Form data received: {dict(form_data)}")
        
        # Извлекаем данные
        business_name = form_data.get("business_name")
        business_type = form_data.get("business_type", "restaurant")
        email = form_data.get("email")
        phone = form_data.get("phone")
        password = form_data.get("password")
        confirm_password = form_data.get("confirm_password")
        city = form_data.get("city")
        address = form_data.get("address")
        
        # Координаты
        lat_str = form_data.get("lat")
        lon_str = form_data.get("lon")
        
        pickup_start = form_data.get("pickup_start")
        pickup_end = form_data.get("pickup_end")
        description = form_data.get("description", "")
        
        # Валидация пароля
        if password != confirm_password:
            return templates.TemplateResponse("supplier_register.html", {
                "request": request,
                "error": "Пароли не совпадают",
                "lang": "ru"
            })
        
        # Конвертируем координаты
        try:
            lat = float(lat_str) if lat_str else 0
            lon = float(lon_str) if lon_str else 0
        except ValueError:
            lat, lon = 0, 0
        
        # Валидация обязательных полей
        if not all([business_name, email, phone, password, city, address, lat, lon, pickup_start, pickup_end]):
            missing = []
            if not business_name: missing.append("business_name")
            if not email: missing.append("email")
            if not phone: missing.append("phone")
            if not password: missing.append("password")
            if not city: missing.append("city")
            if not address: missing.append("address")
            if not lat: missing.append("lat")
            if not lon: missing.append("lon")
            if not pickup_start: missing.append("pickup_start")
            if not pickup_end: missing.append("pickup_end")
            
            print(f"❌ Missing fields: {missing}")
            
            return templates.TemplateResponse("supplier_register.html", {
                "request": request,
                "error": f"Все обязательные поля должны быть заполнены. Отсутствуют: {', '.join(missing)}",
                "lang": "ru"
            })
        
        # Проверка существующего пользователя
        existing = db.query(User).filter(
            (User.email == email) | (User.phone == phone)
        ).first()
        
        if existing:
            return templates.TemplateResponse("supplier_register.html", {
                "request": request,
                "error": "Пользователь с таким email или телефоном уже существует",
                "lang": "ru"
            })
        
        # ✅ ИСПРАВЛЕНО: создаем пользователя с role = 'supplier' (строка, БЕЗ ENUM)
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        user = User(
            email=email,
            phone=phone,
            password=password_hash,
            full_name=business_name,
            role="supplier",  # ✅ СТРОКА, БЕЗ ENUM
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.flush()
        
        # Создаем профиль поставщика
        supplier = Supplier(
            user_id=user.id,
            business_name=business_name,
            business_type=business_type,
            description=description,
            city=city,
            address=address,
            lat=lat,
            lon=lon,
            phone=phone,
            email=email,
            pickup_start_time=pickup_start,
            pickup_end_time=pickup_end,
            created_at=datetime.utcnow()
        )
        db.add(supplier)
        db.commit()
        
        print(f"✅ Supplier registered: {email}")
        
        # Создаем JWT токен
        from jose import jwt
        import datetime
        
        token_data = {
            "sub": str(user.id),
            "role": "supplier",
            "supplier_id": supplier.id,
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(days=30)
        }
        
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        # Редирект на дашборд с токеном
        response = RedirectResponse(url=f"/supplier/dashboard?token={token}", status_code=303)
        
        return response
        
    except Exception as e:
        print(f"❌ Registration error: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("supplier_register.html", {
            "request": request,
            "error": f"Ошибка регистрации: {str(e)}",
            "lang": "ru"
        })
    
@app.get("/supplier/register")
async def supplier_register_page(request: Request, lang: str = "ru"):
    """Страница регистрации поставщика"""
    return templates.TemplateResponse("supplier_register.html", {
        "request": request,
        "lang": lang
    })
# ============ SUPPLIER ROUTES ============
@app.post("/supplier/api/register")
async def supplier_api_register(request: Request):
    """API регистрация поставщика - БЕЗ КУКИ, только JWT, ЧИСТЫЙ SQL"""
    try:
        data = await request.json()
        
        print(f"📥 API Register: {data.get('email')}")
        
        # ======== ПРОВЕРКА ОБЯЗАТЕЛЬНЫХ ПОЛЕЙ ========
        required_fields = ['business_name', 'email', 'phone', 'password', 'city', 'address', 'lat', 'lon', 'pickup_start', 'pickup_end']
        for field in required_fields:
            if field not in data or not data.get(field):
                return {"success": False, "message": f"Missing field: {field}"}
        
        business_name = data.get("business_name", "").strip()
        business_type = data.get("business_type", "restaurant")
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        password = data.get("password", "")
        city = data.get("city", "").strip()
        address = data.get("address", "").strip()
        lat = float(data.get("lat"))
        lon = float(data.get("lon"))
        pickup_start = data.get("pickup_start", "19:30")
        pickup_end = data.get("pickup_end", "20:00")
        description = data.get("description", "").strip()
        
        # ======== ВАЛИДАЦИЯ ========
        if len(password) < 6:
            return {"success": False, "message": "Пароль должен быть минимум 6 символов"}
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверка email
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return {"success": False, "message": "Пользователь с таким email уже существует"}
        
        # Проверка телефона
        cur.execute("SELECT id FROM users WHERE phone = %s", (phone,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return {"success": False, "message": "Пользователь с таким телефоном уже существует"}
        
        # Проверка названия магазина
        cur.execute("SELECT id FROM suppliers WHERE business_name = %s", (business_name,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return {"success": False, "message": "Магазин с таким названием уже существует"}
        
        # ======== СОЗДАЕМ ПОЛЬЗОВАТЕЛЯ ========
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # ✅ ИСПОЛЬЗУЕМ full_name (как в модели User)
        cur.execute("""
            INSERT INTO users (full_name, email, phone, password, role, created_at)
            VALUES (%s, %s, %s, %s, 'supplier', NOW())
            RETURNING id
        """, (business_name, email, phone, password_hash))
        
        user_id = cur.fetchone()[0]
        
        # ======== СОЗДАЕМ ПОСТАВЩИКА ========
        cur.execute("""
            INSERT INTO suppliers (
                user_id, business_name, business_type, city, address, phone, 
                email, lat, lon, pickup_start_time, pickup_end_time,
                description, rating, is_active, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, true, NOW())
            RETURNING id
        """, (user_id, business_name, business_type, city, address, phone, 
              email, lat, lon, pickup_start, pickup_end, description))
        
        supplier_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Зарегистрирован новый поставщик: {business_name} (тип: {business_type})")
        
        # ======== СОЗДАЕМ JWT ТОКЕН ========
        from jose import jwt
        import datetime
        
        token_data = {
            "sub": str(user_id),
            "role": "supplier",
            "supplier_id": supplier_id,
            "email": email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "success": True,
            "message": "Регистрация успешна!",
            "token": token,
            "supplier": {
                "id": supplier_id,
                "business_name": business_name,
                "business_type": business_type,
                "email": email,
                "city": city,
                "address": address
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка регистрации: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e)}


# backend/main.py - РЕГИСТРАЦИЯ КЛИЕНТА

@app.post("/api/auth/login")
async def register_user(request: Request):
    """Регистрация нового клиента"""
    try:
        data = await request.json()
        
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        phone = data.get("phone", "").strip()
        password = data.get("password", "")
        
        # ======== ВАЛИДАЦИЯ ========
        if not first_name or not last_name:
            return {"success": False, "detail": "Введите имя и фамилию"}
        
        if not phone:
            return {"success": False, "detail": "Введите номер телефона"}
        
        if not password or len(password) < 6:
            return {"success": False, "detail": "Пароль должен быть минимум 6 символов"}
        
        # ======== ПОДКЛЮЧЕНИЕ К БД ========
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверка телефона
        cur.execute("SELECT id FROM users WHERE phone = %s", (phone,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return {"success": False, "detail": "Пользователь с таким телефоном уже существует"}
        
        # ======== СОЗДАЕМ ПОЛЬЗОВАТЕЛЯ ========
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        full_name = f"{first_name} {last_name}"
        
        cur.execute("""
            INSERT INTO users (first_name, last_name, full_name, phone, password, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, 'customer', true, NOW())
            RETURNING id
        """, (first_name, last_name, full_name, phone, password_hash))
        
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Зарегистрирован новый клиент: {first_name} {last_name} (телефон: {phone})")
        
        # ======== СОЗДАЕМ JWT ТОКЕН ========
        from jose import jwt
        import datetime
        
        token_data = {
            "sub": str(user_id),
            "role": "customer",
            "phone": phone,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }
        
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "success": True,
            "message": "Регистрация успешна",
            "user_id": user_id,
            "token": token,
            "user": {
                "id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "full_name": full_name,
                "phone": phone,
                "role": "customer"
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка регистрации: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "detail": str(e)}

@app.delete("/api/admin/delete-all-bags")
async def admin_delete_all_bags(
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ удаляет ВСЕ сюрпризы из БД"""
    
    # Проверяем админ-токен
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"success": False, "message": "Unauthorized"})
    
    token = auth_header.split(" ")[1]
    
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        
        if role != "admin":
            return JSONResponse(status_code=403, content={"success": False, "message": "Admin only"})
    except:
        return JSONResponse(status_code=401, content={"success": False, "message": "Invalid token"})
    
    # Удаляем все сюрпризы
    bags = db.query(SurpriseBag).all()
    deleted_count = len(bags)
    
    # Сначала удаляем связанные записи (items)
    for bag in bags:
        db.query(SurpriseBagItem).filter(SurpriseBagItem.surprise_bag_id == bag.id).delete()
        db.delete(bag)
    
    db.commit()
    
    # Отправляем уведомление через WebSocket
    try:
        from backend.websocket_manager import manager
        await manager.broadcast({
            "type": "delete_bag",
            "data": {"all": True}
        }, channel="surprise_bags")
    except:
        pass
    
    return {
        "success": True, 
        "deleted_count": deleted_count,
        "message": f"Удалено {deleted_count} сюрпризов"
    }


@app.delete("/api/debug/delete-all")
async def debug_delete_all(db: Session = Depends(get_db)):
    """Временный эндпоинт - удалить все сюрпризы"""
    try:
        # Сначала удаляем связи
        db.query(SurpriseBagItem).delete()
        # Потом сами сюрпризы
        deleted = db.query(SurpriseBag).delete()
        db.commit()
        return {"success": True, "deleted": deleted}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}


@app.get("/supplier/login")
async def supplier_login_page(request: Request, lang: str = "ru"):
    """Страница логина поставщика"""
    return templates.TemplateResponse("supplier_login.html", {"request": request, "lang": lang})
# backend/main.py - добавьте
# backend/main.py - ИСПРАВЛЕННЫЙ ЛОГИН ПОСТАВЩИКА

@app.post("/supplier/api/login")
async def supplier_api_login(request: Request):
    try:
        data = await request.json()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        if not email or not password:
            return {"success": False, "message": "Email и пароль обязательны"}
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # ✅ ОДИН ЗАПРОС - ВСЕ ДАННЫЕ
        cur.execute("""
            SELECT 
                u.id, u.email, u.password, u.is_active,
                s.id as supplier_id, s.business_name, s.business_type,
                s.phone, s.city, s.address, s.is_active as supplier_active
            FROM users u
            JOIN suppliers s ON s.user_id = u.id
            WHERE u.email = %s AND u.role = 'supplier'
        """, (email,))
        
        user = cur.fetchone()
        
        if not user:
            cur.close()
            conn.close()
            return {"success": False, "message": "Неверный email или пароль"}
        
        # Проверка пароля
        import hashlib
        if user['password'] != hashlib.sha256(password.encode()).hexdigest():
            cur.close()
            conn.close()
            return {"success": False, "message": "Неверный email или пароль"}
        
        # ✅ АКТИВАЦИЯ ЕСЛИ НАДО
        if not user['is_active'] or not user['supplier_active']:
            cur2 = conn.cursor()
            cur2.execute("""
                UPDATE users SET is_active = true WHERE id = %s;
                UPDATE suppliers SET is_active = true WHERE user_id = %s;
            """, (user['id'], user['id']))
            conn.commit()
            cur2.close()
        
        cur.close()
        conn.close()
        
        # Токен
        from jose import jwt
        import datetime
        token = jwt.encode({
            "sub": str(user['id']),
            "role": "supplier",
            "supplier_id": user['supplier_id'],
            "email": user['email'],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "success": True,
            "token": token,
            "supplier": {
                "id": user['supplier_id'],
                "business_name": user['business_name'],
                "business_type": user['business_type'],
                "email": user['email'],
                "phone": user['phone'],
                "city": user['city'],
                "address": user['address']
            }
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "message": str(e)}# backend/main.py - ЭНДПОИНТ ЛОГИНА
@app.get("/api/debug/supplier-status")
async def debug_supplier_status_get(request: Request, db: Session = Depends(get_db)):
    """Проверить статус поставщика по email (GET)"""
    try:
        email = request.query_params.get("email")
        
        if not email:
            return {"error": "Email required"}
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {"error": f"User with email {email} not found"}
        
        supplier = db.query(Supplier).filter(Supplier.user_id == user.id).first()
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active,
                "role": user.role
            },
            "supplier": {
                "id": supplier.id if supplier else None,
                "business_name": supplier.business_name if supplier else None,
                "is_active": supplier.is_active if supplier else None
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/debug/activate-all-suppliers")
async def activate_all_suppliers(db: Session = Depends(get_db)):
    """Активировать ВСЕХ поставщиков"""
    try:
        users = db.query(User).filter(User.role == "supplier").all()
        user_count = 0
        for user in users:
            if not user.is_active:
                user.is_active = True
                user_count += 1
        
        suppliers = db.query(Supplier).all()
        supplier_count = 0
        for supplier in suppliers:
            if not supplier.is_active:
                supplier.is_active = True
                supplier_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "users_activated": user_count,
            "suppliers_activated": supplier_count,
            "total_users": len(users),
            "total_suppliers": len(suppliers)
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}


@app.post("/api/debug/activate-supplier")
async def activate_supplier_by_email(request: Request, db: Session = Depends(get_db)):
    """Активировать поставщика по email"""
    try:
        data = await request.json()
        email = data.get("email", "").strip()
        
        if not email:
            return {"success": False, "error": "Email required"}
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {"success": False, "error": f"User with email {email} not found"}
        
        old_status = user.is_active
        user.is_active = True
        db.commit()
        
        supplier = db.query(Supplier).filter(Supplier.user_id == user.id).first()
        supplier_activated = False
        if supplier:
            supplier.is_active = True
            db.commit()
            supplier_activated = True
        
        return {
            "success": True,
            "message": f"User {email} activated",
            "user_id": user.id,
            "old_status": old_status,
            "new_status": True,
            "supplier_activated": supplier_activated,
            "supplier_id": supplier.id if supplier else None
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    
@app.get("/supplier/api/status")
async def supplier_status(request: Request, db: Session = Depends(get_db)):
    """Проверить статус поставщика"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"authenticated": False}
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        supplier_id = payload.get("supplier_id")
        
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            return {"authenticated": False}
        
        user = db.query(User).filter(User.id == supplier.user_id).first()
        
        return {
            "authenticated": True,
            "is_active": user.is_active if user else False,
            "supplier_active": supplier.is_active
        }
    except:
        return {"authenticated": False}

@app.post("/supplier/login")
async def supplier_login(request: Request):
    """API входа поставщика"""
    try:
        data = await request.json()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        print(f"🔐 LOGIN: email={email}")
        
        if not email or not password:
            return {"success": False, "error": "Email и пароль обязательны"}
        
        # Подключаемся к БД
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Ищем пользователя
        cur.execute("""
            SELECT u.id, u.email, u.password, u.role, u.is_active,
                   s.id as supplier_id, s.business_name, s.is_active as supplier_active
            FROM users u
            LEFT JOIN suppliers s ON s.user_id = u.id
            WHERE u.email = %s
        """, (email,))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user:
            print("❌ Пользователь не найден")
            return {"success": False, "error": "Неверный email или пароль"}
        
        if not user.get('is_active'):
            print("❌ Пользователь неактивен")
            return {"success": False, "error": "Аккаунт деактивирован"}
        
        if user.get('role') != 'supplier':
            print(f"❌ Неправильная роль: {user.get('role')}")
            return {"success": False, "error": "Доступ запрещен"}
        
        # Проверяем пароль
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if user.get('password') != password_hash:
            print("❌ Неверный пароль")
            return {"success": False, "error": "Неверный email или пароль"}
        
        # Создаем токен
        from jose import jwt
        import datetime
        
        token_data = {
            "sub": str(user['id']),
            "role": "supplier",
            "supplier_id": user['supplier_id'],
            "email": user['email'],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        print(f"✅ Логин успешен: {user.get('business_name')}")
        
        return {
            "success": True,
            "token": token,
            "supplier_id": user['supplier_id'],
            "business_name": user.get('business_name'),
            "message": "Вход выполнен успешно"
        }
        
    except Exception as e:
        print(f"❌ Ошибка логина: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

# backend/main.py - добавьте этот эндпоинт

@app.post("/api/auth/activate-user")
async def activate_user(request: Request, db: Session = Depends(get_db)):
    """Активировать пользователя (если он деактивирован)"""
    try:
        data = await request.json()
        phone = data.get("phone", "").strip()
        password = data.get("password", "")
        
        if not phone or not password:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Телефон и пароль обязательны"}
            )
        
        # Находим пользователя
        user = db.query(User).filter(User.phone == phone).first()
        
        if not user:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Пользователь не найден"}
            )
        
        # Проверяем пароль
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if user.password != password_hash:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Неверный пароль"}
            )
        
        # Активируем пользователя
        user.is_active = True
        db.commit()
        
        print(f"✅ Пользователь {phone} активирован")
        
        # Создаем токен
        from jose import jwt
        import datetime
        
        token_data = {
            "sub": str(user.id),
            "role": user.role or "customer",
            "phone": user.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }
        
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "success": True,
            "message": "Пользователь активирован",
            "token": token,
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "role": user.role or "customer"
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

# backend/main.py - добавьте этот эндпоинт для отладки

@app.post("/api/debug/activate-all-users")
async def debug_activate_all_users(db: Session = Depends(get_db)):
    """Активировать ВСЕХ пользователей (только для отладки)"""
    try:
        users = db.query(User).all()
        activated_count = 0
        
        for user in users:
            if not user.is_active:
                user.is_active = True
                activated_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Активировано {activated_count} пользователей",
            "total_users": len(users),
            "activated_count": activated_count
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    
@app.get("/api/supplier/check-auth")
async def supplier_check_auth(request: Request, db: Session = Depends(get_db)):
    """Проверка валидности токена поставщика"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"authenticated": False})
    
    token = auth_header.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("role") != "supplier":
            return JSONResponse(status_code=403, content={"authenticated": False})
        
        supplier_id = payload.get("supplier_id")
        if not supplier_id:
            return JSONResponse(status_code=404, content={"authenticated": False})
        
        return {"authenticated": True, "supplier_id": supplier_id}
        
    except:
        return JSONResponse(status_code=401, content={"authenticated": False})
    


# backend/main.py - ДОБАВЛЯЕМ ПЕРЕДАЧУ ПРОДУКТОВ И ШАБЛОНОВ

# backend/main.py - ДОБАВЛЯЕМ ПЕРЕДАЧУ ПРОДУКТОВ И ШАБЛОНОВ
@app.get("/supplier/dashboard")
async def supplier_dashboard(
    request: Request, 
    db: Session = Depends(get_db)
):
    """Страница дашборда поставщика"""
    
    supplier_id = None
    auth_token = None
    
    # ======== ПОЛУЧАЕМ ТОКЕН ========
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        auth_token = auth_header.split(" ")[1]
    
    if not auth_token:
        auth_token = request.query_params.get("token")
    
    # ======== ПРОВЕРЯЕМ ТОКЕН ========
    if auth_token:
        try:
            from jose import jwt
            payload = jwt.decode(auth_token, SECRET_KEY, algorithms=[ALGORITHM])
            role = payload.get("role")
            
            if role == "supplier":
                supplier_id = payload.get("supplier_id")
                if not supplier_id:
                    user_id = int(payload.get("sub"))
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM suppliers WHERE user_id = %s", (user_id,))
                    result = cur.fetchone()
                    cur.close()
                    conn.close()
                    if result:
                        supplier_id = result[0]
        except Exception as e:
            print(f"❌ JWT error: {e}")
            auth_token = None
    
    if not supplier_id:
        print("❌ No supplier_id, redirect to login")
        return RedirectResponse(url="/supplier/login?error=no_token", status_code=303)
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Получаем данные поставщика
        cur.execute("""
            SELECT id, business_name, business_type, city, address, phone, email, rating, is_active
            FROM suppliers 
            WHERE id = %s
        """, (supplier_id,))
        
        supplier = cur.fetchone()
        
        if not supplier:
            cur.close()
            conn.close()
            return RedirectResponse(url="/supplier/login", status_code=303)
        
        # Получаем заказы
        cur.execute("""
            SELECT 
                o.id,
                o.order_number,
                o.customer_address,
                o.amount_paid,
                o.status,
                o.created_at,
                o.delivery_deadline,
                o.assigned_courier_id,
                sb.name as surprise_bag_name
            FROM orders o
            LEFT JOIN surprise_bags sb ON sb.id = o.surprise_bag_id
            WHERE o.supplier_id = %s
            ORDER BY o.created_at DESC
        """, (supplier_id,))
        
        all_orders = cur.fetchall()
        
        # Статистика
        cur.execute("""
            SELECT 
                COUNT(*) as total_orders,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
                COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) as today_orders,
                COALESCE(SUM(CASE WHEN status = 'delivered' THEN amount_paid ELSE 0 END), 0) as total_revenue
            FROM orders
            WHERE supplier_id = %s
        """, (supplier_id,))
        
        stats_data = cur.fetchone()
        
        # Получаем сюрпризы
        cur.execute("""
            SELECT 
                id, name, description, original_price, discounted_price,
                discount_percentage, image_url, available_quantity, total_quantity,
                is_active, created_at, hide_contents
            FROM surprise_bags
            WHERE supplier_id = %s
            ORDER BY created_at DESC
        """, (supplier_id,))
        
        surprise_bags = cur.fetchall()
        
        # ======== ИСПРАВЛЕНО: ТОЛЬКО name_ru, name_kz, price (БЕЗ icon и name_en) ========
        cur.execute("""
            SELECT id, name_ru, name_kz, price
            FROM foods
            ORDER BY id
        """)
        products = cur.fetchall()
        
        # Если нет продуктов в базе - создаем тестовые (БЕЗ icon)
        if not products:
            products = [
                {'id': 1, 'name_ru': 'Маргарита Пицца', 'name_kz': 'Маргарита Пицца', 'price': 2500},
                {'id': 2, 'name_ru': 'Пепперони Пицца', 'name_kz': 'Пепперони Пицца', 'price': 3200},
                {'id': 6, 'name_ru': 'Гамбургер', 'name_kz': 'Гамбургер', 'price': 1800},
                {'id': 14, 'name_ru': 'Кока-Кола', 'name_kz': 'Кока-Кола', 'price': 500},
                {'id': 16, 'name_ru': 'Чизкейк', 'name_kz': 'Чизкейк', 'price': 1200},
                {'id': 18, 'name_ru': 'Картошка Фри', 'name_kz': 'Картоп Фри', 'price': 800}
            ]
        
        # Получаем шаблоны по типу заведения
        business_type = supplier.get('business_type') or 'restaurant'
        templates_data = get_templates_by_type(business_type)
        
        # Подготовка списка заказов для шаблона
        recent_orders_list = []
        for order in all_orders[:10]:
            courier_name = None
            if order.get('assigned_courier_id'):
                cur2 = conn.cursor()
                cur2.execute("SELECT first_name, last_name FROM courier_profiles WHERE user_id = %s", (order['assigned_courier_id'],))
                courier = cur2.fetchone()
                cur2.close()
                if courier:
                    courier_name = f"{courier[0]} {courier[1]}"
            
            recent_orders_list.append({
                "id": order['id'],
                "order_number": order['order_number'] or f"ORD-{order['id']}",
                "customer_address": order['customer_address'] or "Мекенжай көрсетілмеген",
                "surprise_bag_name": order['surprise_bag_name'] or "Тосын сый",
                "amount_paid": float(order['amount_paid']) if order['amount_paid'] else 0,
                "status": order['status'] or "pending",
                "created_at": order['created_at'],
                "delivery_deadline": order['delivery_deadline'],
                "assigned_courier_name": courier_name
            })
        
        stats = {
            "total_orders": stats_data['total_orders'] if stats_data else 0,
            "pending_orders": stats_data['pending_orders'] if stats_data else 0,
            "today_orders": stats_data['today_orders'] if stats_data else 0,
            "total_revenue": float(stats_data['total_revenue']) if stats_data else 0
        }
        
        lang = request.query_params.get("lang", "ru")
        
        cur.close()
        conn.close()
        
        return templates.TemplateResponse("supplier_dashboard.html", {
            "request": request,
            "supplier": supplier,
            "stats": stats,
            "recent_orders": recent_orders_list,
            "all_orders": recent_orders_list,
            "surprise_bags": surprise_bags,
            "products": products,
            "templates_data": templates_data,
            "monthly_revenue": stats["total_revenue"],
            "lang": lang,
            "token": auth_token
        })
        
    except Exception as e:
        cur.close()
        conn.close()
        print(f"❌ Ошибка supplier_dashboard: {e}")
        return RedirectResponse(url="/supplier/login", status_code=303)

# ✅ Функция получения шаблонов по типу
def get_templates_by_type(business_type: str) -> dict:
    """Возвращает шаблоны сюрпризов в зависимости от типа заведения"""
    
    templates = {
        'restaurant': {
            'icon': '🍽️',
            'name': {'en': 'Restaurant', 'ru': 'Ресторан', 'kz': 'Ресторан'},
            'templates': {
                'dinner_set': {
                    'name': {'en': 'Dinner Set', 'ru': 'Ужин на двоих', 'kz': 'Кешкі ас'},
                    'items': [{'id': 1, 'qty': 2}, {'id': 12, 'qty': 1}, {'id': 14, 'qty': 2}],
                    'price': 5500,
                    'description': {'en': 'Romantic dinner for two', 'ru': 'Романтический ужин на двоих', 'kz': 'Екеуге арналған романтикалық кешкі ас'}
                },
                'family_set': {
                    'name': {'en': 'Family Set', 'ru': 'Семейный обед', 'kz': 'Отбасылық түскі ас'},
                    'items': [{'id': 2, 'qty': 2}, {'id': 13, 'qty': 1}, {'id': 18, 'qty': 2}],
                    'price': 7200,
                    'description': {'en': 'Family lunch', 'ru': 'Семейный обед', 'kz': 'Отбасылық түскі ас'}
                }
            }
        },
        'cafe': {
            'icon': '☕',
            'name': {'en': 'Cafe', 'ru': 'Кафе', 'kz': 'Кафе'},
            'templates': {
                'coffee_set': {
                    'name': {'en': 'Coffee Set', 'ru': 'Кофе с десертом', 'kz': 'Кофе десертпен'},
                    'items': [{'id': 14, 'qty': 2}, {'id': 16, 'qty': 1}],
                    'price': 2300,
                    'description': {'en': 'Coffee and dessert', 'ru': 'Кофе и десерт', 'kz': 'Кофе және десерт'}
                },
                'breakfast_set': {
                    'name': {'en': 'Breakfast Set', 'ru': 'Завтрак', 'kz': 'Таңғы ас'},
                    'items': [{'id': 6, 'qty': 1}, {'id': 14, 'qty': 1}],
                    'price': 2800,
                    'description': {'en': 'Healthy breakfast', 'ru': 'Полезный завтрак', 'kz': 'Пайдалы таңғы ас'}
                }
            }
        },
        'fastfood': {
            'icon': '🍔',
            'name': {'en': 'Fast Food', 'ru': 'Фастфуд', 'kz': 'Фастфуд'},
            'templates': {
                'burger_set': {
                    'name': {'en': 'Burger Set', 'ru': 'Бургер с картошкой', 'kz': 'Бургер картоппен'},
                    'items': [{'id': 6, 'qty': 2}, {'id': 18, 'qty': 1}],
                    'price': 3400,
                    'description': {'en': 'Burger and fries', 'ru': 'Бургер и картошка фри', 'kz': 'Бургер және картоп фри'}
                },
                'pizza_set': {
                    'name': {'en': 'Pizza Set', 'ru': 'Пицца с напитками', 'kz': 'Пицца сусындармен'},
                    'items': [{'id': 1, 'qty': 1}, {'id': 14, 'qty': 2}],
                    'price': 3900,
                    'description': {'en': 'Pizza and drinks', 'ru': 'Пицца и напитки', 'kz': 'Пицца және сусындар'}
                }
            }
        },
        'bakery': {
            'icon': '🥖',
            'name': {'en': 'Bakery', 'ru': 'Пекарня', 'kz': 'Наубайхана'},
            'templates': {
                'sweet_set': {
                    'name': {'en': 'Sweet Set', 'ru': 'Сладкий набор', 'kz': 'Тәтті жинақ'},
                    'items': [{'id': 16, 'qty': 2}, {'id': 17, 'qty': 1}],
                    'price': 2800,
                    'description': {'en': 'Sweet pastries', 'ru': 'Сладкая выпечка', 'kz': 'Тәтті тоқаштар'}
                },
                'bread_set': {
                    'name': {'en': 'Bread Set', 'ru': 'Хлебный набор', 'kz': 'Нан жинағы'},
                    'items': [{'id': 1, 'qty': 1}, {'id': 2, 'qty': 1}],
                    'price': 3200,
                    'description': {'en': 'Fresh bread', 'ru': 'Свежий хлеб', 'kz': 'Жаңа нан'}
                }
            }
        },
        'supermarket': {
            'icon': '🛒',
            'name': {'en': 'Supermarket', 'ru': 'Супермаркет', 'kz': 'Супермаркет'},
            'templates': {
                'snack_set': {
                    'name': {'en': 'Snack Set', 'ru': 'Снэк-набор', 'kz': 'Снэк жинағы'},
                    'items': [{'id': 18, 'qty': 2}, {'id': 19, 'qty': 1}],
                    'price': 2600,
                    'description': {'en': 'Snacks for party', 'ru': 'Снэки для вечеринки', 'kz': 'Кешке арналған снэктер'}
                },
                'drink_set': {
                    'name': {'en': 'Drink Set', 'ru': 'Напитки', 'kz': 'Сусындар'},
                    'items': [{'id': 14, 'qty': 3}, {'id': 15, 'qty': 2}],
                    'price': 1900,
                    'description': {'en': 'Assorted drinks', 'ru': 'Ассорти напитков', 'kz': 'Сусындар ассорти'}
                }
            }
        },
        'shop': {
            'icon': '🛍️',
            'name': {'en': 'Shop', 'ru': 'Магазин', 'kz': 'Дүкен'},
            'templates': {
                'lunch_set': {
                    'name': {'en': 'Lunch Set', 'ru': 'Обед на вынос', 'kz': 'Алып кететін түскі ас'},
                    'items': [{'id': 12, 'qty': 1}, {'id': 6, 'qty': 1}],
                    'price': 3300,
                    'description': {'en': 'Quick lunch', 'ru': 'Быстрый обед', 'kz': 'Жылдам түскі ас'}
                },
                'salad_set': {
                    'name': {'en': 'Salad Set', 'ru': 'Салаты', 'kz': 'Салаттар'},
                    'items': [{'id': 12, 'qty': 1}, {'id': 13, 'qty': 1}],
                    'price': 3700,
                    'description': {'en': 'Fresh salads', 'ru': 'Свежие салаты', 'kz': 'Жаңа салаттар'}
                }
            }
        }
    }
    
    return templates.get(business_type, templates['restaurant'])


@app.post("/supplier/logout")
async def supplier_logout(request: Request):
    """Выход поставщика - чистим session и редирект"""
    # Просто редирект на логин, куки не используем
    return RedirectResponse(url="/supplier/login?logout=success", status_code=303)

@app.get("/api/foods")
async def get_foods(db: Session = Depends(get_db)):
    """Get all foods for dropdown list"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # ======== ИСПРАВЛЕНО: БЕЗ name_en ========
        cur.execute("""
            SELECT id, name_ru, name_kz, icon, price
            FROM foods
            ORDER BY id
        """)
        foods = cur.fetchall()
        cur.close()
        conn.close()
        
        print(f"📦 Returned {len(foods)} foods")
        return foods
    except Exception as e:
        print(f"❌ Error getting foods: {e}")
        return []
@app.get("/api/suppliers/{supplier_id}")
async def get_supplier_by_id(supplier_id: int):
    """Получить информацию о магазине по ID - ЧИСТЫЙ SQL"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                id, business_name, description, address, city, 
                phone, email, rating, cover_image, lat, lon, is_active
            FROM suppliers 
            WHERE id = %s
        """, (supplier_id,))
        
        supplier = cur.fetchone()
        cur.close()
        conn.close()
        
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        return supplier
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/suppliers/{supplier_id}/surprise-bags")
async def get_supplier_surprise_bags(supplier_id: int):
    """Получить все активные сюрпризы магазина - ЧИСТЫЙ SQL"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Проверяем существует ли поставщик
        cur.execute("SELECT id FROM suppliers WHERE id = %s", (supplier_id,))
        supplier = cur.fetchone()
        if not supplier:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        # Получаем активные сюрпризы
        cur.execute("""
            SELECT 
                id, name, description, original_price, discounted_price,
                discount_percentage, image_url, available_quantity,
                pickup_start_time, pickup_end_time, is_active
            FROM surprise_bags
            WHERE supplier_id = %s 
                AND is_active = true 
                AND available_quantity > 0
            ORDER BY created_at DESC
        """, (supplier_id,))
        
        bags = cur.fetchall()
        cur.close()
        conn.close()
        
        return bags
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/supplier/verify-token")
async def verify_supplier_token(request: Request):
    """Проверка токена поставщика - ЧИСТЫЙ SQL"""
    try:
        # Получаем токен из заголовка
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {"valid": False, "error": "No token provided"}
        
        token = auth_header.split(" ")[1]
        
        # Проверяем токен
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("role") != "supplier":
            return {"valid": False, "error": "Not a supplier"}
        
        supplier_id = payload.get("supplier_id")
        if not supplier_id:
            user_id = int(payload.get("sub"))
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id FROM suppliers WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            if result:
                supplier_id = result[0]
        
        # Проверяем что поставщик существует
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, business_name FROM suppliers WHERE id = %s", (supplier_id,))
        supplier = cur.fetchone()
        cur.close()
        conn.close()
        
        if not supplier:
            return {"valid": False, "error": "Supplier not found"}
        
        return {
            "valid": True,
            "supplier_id": supplier_id,
            "business_name": supplier[1]
        }
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token expired"}
    except jwt.JWTError:
        return {"valid": False, "error": "Invalid token"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"valid": False, "error": str(e)}
# backend/main.py - добавь этот эндпоинт

# backend/main.py - ЗАМЕНИТЕ ваш существующий эндпоинт
# backend/main.py - ЗАМЕНИТЕ эндпоинт на этот:
@app.delete("/api/admin/cleanup-cancelled-orders")
async def cleanup_cancelled_orders(request: Request):
    """Очистка отмененных заказов - чистый SQL с освобождением курьеров"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Сначала находим все отмененные заказы
        cur.execute("""
            SELECT id, order_number, assigned_courier_id
            FROM orders 
            WHERE status = 'cancelled'
        """)
        cancelled = cur.fetchall()
        
        if not cancelled:
            cur.close()
            conn.close()
            return {
                "success": True,
                "deleted_count": 0,
                "message": "Нет отмененных заказов для удаления"
            }
        
        # 2. ОСВОБОЖДАЕМ КУРЬЕРОВ (снимаем привязку к заказу)
        for order in cancelled:
            order_id = order[0]
            courier_id = order[2] if len(order) > 2 else None
            
            if courier_id:
                # Освобождаем курьера
                cur.execute("""
                    UPDATE courier_profiles 
                    SET current_order_id = NULL,
                        current_order_status = NULL,
                        is_available = true
                    WHERE current_order_id = %s
                """, (order_id,))
                print(f"✅ Освобожден курьер от заказа #{order_id}")
        
        # 3. Удаляем записи из order_tracking (если есть)
        order_ids = [str(o[0]) for o in cancelled]
        if order_ids:
            cur.execute(f"""
                DELETE FROM order_tracking 
                WHERE order_id IN ({','.join(order_ids)})
            """)
            
            # 4. Удаляем из assigned_orders (если есть)
            cur.execute(f"""
                DELETE FROM assigned_orders 
                WHERE order_id IN ({','.join(order_ids)})
            """)
        
        # 5. Теперь удаляем сами заказы
        cur.execute("""
            DELETE FROM orders 
            WHERE status = 'cancelled'
        """)
        deleted_count = cur.rowcount
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cancelled_orders": [
                {"id": o[0], "order_number": o[1]} for o in cancelled
            ],
            "message": f"Удалено {deleted_count} отмененных заказов"
        }
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/supplier/debug-bags")
async def debug_bags(request: Request):
    """Диагностика - проверка полей сюрпризов - ЧИСТЫЙ SQL"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"success": False})
    
    token = auth_header.split(" ")[1]
    
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id FROM suppliers WHERE user_id = %s
        """, (int(user_id),))
        supplier = cur.fetchone()
        
        if not supplier:
            cur.close()
            conn.close()
            return JSONResponse(status_code=404, content={"success": False})
        
        cur.execute("""
            SELECT 
                id, name, is_active, available_quantity,
                created_at, hide_contents, city
            FROM surprise_bags 
            WHERE supplier_id = %s
        """, (supplier['id'],))
        
        bags = cur.fetchall()
        cur.close()
        conn.close()
        
        return {"bags": bags}
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.delete("/api/supplier/clear-all-bags")
async def clear_all_surprise_bags(
    request: Request,
    db: Session = Depends(get_db)
):
    """Удаление ВСЕХ сюрприз-пакетов поставщика с очисткой связей"""
    
    # ✅ Проверяем токен поставщика
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Invalid token"}
            )
        
        # Проверяем что это поставщик
        if payload.get("role") != "supplier":
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Not a supplier"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": f"Authentication error: {str(e)}"}
        )
    
    try:
        from backend.models import Supplier, SurpriseBag, CartItem, Order, TemporaryReservation, SurpriseBagItem
        
        # Находим поставщика
        supplier = db.query(Supplier).filter(Supplier.user_id == int(user_id)).first()
        if not supplier:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Supplier not found"}
            )
        
        # Находим ВСЕ сюрпризы поставщика
        all_bags = db.query(SurpriseBag).filter(SurpriseBag.supplier_id == supplier.id).all()
        
        if not all_bags:
            return {
                "success": True,
                "message": "Нет сюрпризов для удаления",
                "deleted_count": 0
            }
        
        # Получаем ID всех сюрпризов
        bag_ids = [bag.id for bag in all_bags]
        
        print(f"🗑️ Найдено {len(bag_ids)} сюрпризов для удаления")
        
        # 1. Удаляем элементы сюрпризов (surprise_bag_items)
        deleted_items = db.query(SurpriseBagItem).filter(SurpriseBagItem.surprise_bag_id.in_(bag_ids)).delete(synchronize_session=False)
        print(f"🗑️ Удалено {deleted_items} элементов сюрпризов")
        
        # 2. Удаляем временные резервации (temporary_reservations)
        deleted_temp_res = db.query(TemporaryReservation).filter(TemporaryReservation.bag_id.in_(bag_ids)).delete(synchronize_session=False)
        print(f"🗑️ Удалено {deleted_temp_res} временных резерваций")
        
        # 3. Удаляем записи из корзины (cart_items)
        deleted_cart_items = db.query(CartItem).filter(CartItem.surprise_bag_id.in_(bag_ids)).delete(synchronize_session=False)
        print(f"🗑️ Удалено {deleted_cart_items} записей из корзины")
        
        # 4. Обновляем заказы (устанавливаем NULL)
        db.query(Order).filter(Order.surprise_bag_id.in_(bag_ids)).update(
            {Order.surprise_bag_id: None},
            synchronize_session=False
        )
        
        # 5. Теперь удаляем сами сюрпризы
        deleted_count = 0
        for bag in all_bags:
            db.delete(bag)
            deleted_count += 1
        
        db.commit()
        
        print(f"✅ Удалено {deleted_count} сюрпризов поставщика {supplier.business_name}")
        
        return {
            "success": True,
            "message": f"Удалено {deleted_count} сюрприз-пакетов, {deleted_cart_items} из корзины, {deleted_temp_res} резерваций, {deleted_items} элементов",
            "deleted_count": deleted_count,
            "deleted_cart_items": deleted_cart_items,
            "deleted_temp_res": deleted_temp_res,
            "deleted_items": deleted_items
        }
        
    except Exception as e:
        print(f"❌ Ошибка удаления: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error: {str(e)}"}
        )

        
# backend/main.py - ИСПРАВЛЕННАЯ ФУНКЦИЯ

async def auto_cleanup_cancelled_orders():
    """Автоматическая очистка отмененных заказов каждые 30 минут"""
    while True:
        try:
            await asyncio.sleep(1800)  # 30 минут
            
            db = SessionLocal()
            from datetime import datetime, timedelta
            
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            # ✅ ИСПРАВЛЕНО: статус как строка (БЕЗ ENUM)
            cancelled_orders = db.query(Order).filter(
                Order.status == "cancelled",
                Order.cancelled_at < one_hour_ago
            ).all()
            
            deleted_count = 0
            for order in cancelled_orders:
                try:
                    # Освобождаем курьера
                    if order.assigned_courier_id:
                        courier = db.query(CourierProfile).filter(
                            CourierProfile.user_id == order.assigned_courier_id,
                            CourierProfile.current_order_id == order.id
                        ).first()
                        if courier:
                            courier.current_order_id = None
                            courier.current_order_status = None
                            courier.is_available = True
                            courier.is_online = True
                            print(f"✅ Курьер освобожден от заказа #{order.id}")
                    
                    # ✅ ВОЗВРАЩАЕМ ТОВАР (если еще не возвращен)
                    if order.surprise_bag_id:
                        bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
                        if bag and not bag.is_active:
                            bag.available_quantity += 1
                            if bag.available_quantity > 0:
                                bag.is_active = True
                            print(f"📦 Восстановлен товар '{bag.name}' при очистке")
                    
                    db.delete(order)
                    deleted_count += 1
                    
                except Exception as e:
                    print(f"❌ Ошибка при удалении заказа #{order.id}: {e}")
                    db.rollback()
            
            db.commit()
            db.close()
            
            if deleted_count > 0:
                print(f"🧹 Автоочистка: удалено {deleted_count} отмененных заказов")
                
        except Exception as e:
            print(f"❌ Ошибка автоочистки: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(60)  # Пауза перед повторной попыткой

@app.get("/api/suppliers/{supplier_id}/orders")
async def get_supplier_orders(supplier_id: int, db: Session = Depends(get_db)):
    """Get orders for specific supplier"""
    orders = db.query(Order).filter(Order.supplier_id == supplier_id).all()
    
    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "order_number": order.order_number,
            "customer_address": order.customer_address,
            "amount_paid": order.amount_paid,
            "status": order.status.value if order.status else None,
            "created_at": order.created_at.isoformat() if order.created_at else None
        })
    
    return result


# backend/main.py - ИСПРАВЛЕННЫЕ ЭНДПОИНТЫ С jsonable_encoder

from fastapi.encoders import jsonable_encoder



@app.get("/api/surprise-bags")
async def get_all_surprise_bags(
    request: Request,
    db: Session = Depends(get_db)
):
    """ВРЕМЕННО - убираем все фильтры для теста"""
    
    bags = db.query(SurpriseBag).filter(
        SurpriseBag.is_active == True,
        SurpriseBag.available_quantity > 0
    ).all()
    
    result = []
    for bag in bags:
        supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
        if supplier and supplier.is_active:
            items = db.query(SurpriseBagItem).filter(
                SurpriseBagItem.surprise_bag_id == bag.id
            ).all()
            
            items_list = []
            for item in items:
                items_list.append({
                    "product_id": item.product_id or 0,
                    "name": item.product_name or "",
                    "price": float(item.product_price) if item.product_price else 0,
                    "quantity": int(item.quantity) if item.quantity else 1
                })
            
            result.append({
                "id": bag.id,
                "supplier_id": bag.supplier_id,
                "supplier_name": supplier.business_name or "",
                "name": bag.name or "",
                "description": bag.description or "",
                "original_price": float(bag.original_price) if bag.original_price else 0,
                "discounted_price": float(bag.discounted_price) if bag.discounted_price else 0,
                "discount_percentage": int(bag.discount_percentage) if bag.discount_percentage else 0,
                "image_url": bag.image_url or "",
                "available_quantity": int(bag.available_quantity) if bag.available_quantity else 0,
                "hide_contents": bool(bag.hide_contents) if bag.hide_contents is not None else False,
                "city": bag.city or "",
                "items": items_list
            })
    
    return JSONResponse(content=result)
# @app.get("/api/supplier/surprise-bags")
# async def get_supplier_surprise_bags(
#     request: Request,
#     db: Session = Depends(get_db)
# ):
#     """API для получения сюрпризов поставщика (для JS)"""
    
#     auth_header = request.headers.get("Authorization")
#     if not auth_header or not auth_header.startswith("Bearer "):
#         return JSONResponse(status_code=401, content={"success": False, "message": "Unauthorized"})
    
#     token = auth_header.split(" ")[1]
    
#     try:
#         from jose import jwt
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
#         if payload.get("role") != "supplier":
#             return JSONResponse(status_code=403, content={"success": False, "message": "Forbidden"})
        
#         supplier_id = payload.get("supplier_id")
#         if not supplier_id:
#             user_id = int(payload.get("sub"))
#             supplier = db.query(Supplier).filter(Supplier.user_id == user_id).first()
#             if supplier:
#                 supplier_id = supplier.id
        
#         if not supplier_id:
#             return JSONResponse(status_code=404, content={"success": False, "message": "Supplier not found"})
        
#         bags = db.query(SurpriseBag).filter(
#             SurpriseBag.supplier_id == supplier_id
#         ).order_by(SurpriseBag.created_at.desc()).all()
        
#         bags_list = []
#         for bag in bags:
#             bags_list.append({
#                 "id": bag.id,
#                 "name": bag.name or "",
#                 "description": bag.description or "",
#                 "original_price": float(bag.original_price) if bag.original_price else 0,
#                 "discounted_price": float(bag.discounted_price) if bag.discounted_price else 0,
#                 "discount_percentage": int(bag.discount_percentage) if bag.discount_percentage else 0,
#                 "image_url": bag.image_url or "",
#                 "available_quantity": int(bag.available_quantity) if bag.available_quantity else 0,
#                 "total_quantity": int(bag.total_quantity) if bag.total_quantity else 0,
#                 "is_active": bool(bag.is_active) if bag.is_active is not None else False,
#                 "hide_contents": bool(bag.hide_contents) if bag.hide_contents is not None else False,
#                 "city": bag.city or "",
#                 "pickup_start_time": bag.pickup_start_time or "",
#                 "pickup_end_time": bag.pickup_end_time or "",
#                 "created_at": bag.created_at.isoformat() if bag.created_at else None
#             })
        
#         print(f"📦 Найдено сюрпризов: {len(bags_list)}")
#         return JSONResponse(content={"success": True, "bags": jsonable_encoder(bags_list)})
        
#     except Exception as e:
#         print(f"❌ Error getting supplier bags: {e}")
#         import traceback
#         traceback.print_exc()
#         return JSONResponse(status_code=500, content={"success": False, "message": str(e)})
# # backend/main.py - ИСПРАВЛЕННЫЕ ЭНДПОИНТЫ



@app.delete("/users/{user_id}/avatar")
async def delete_avatar(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Удалить аватар пользователя"""
    
    # Проверяем авторизацию
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_user_id = payload.get("sub")
        
        if int(token_user_id) != user_id:
            raise HTTPException(status_code=403, detail="Cannot delete another user's avatar")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    # Удаляем аватар
    avatar_files = list(AVATAR_DIR.glob(f"avatar_{user_id}_*.webp"))
    
    deleted = 0
    for file_path in avatar_files:
        try:
            file_path.unlink()
            deleted += 1
        except:
            pass
    
    if deleted == 0:
        raise HTTPException(status_code=404, detail="No avatar found")
    
    return {"success": True, "deleted": deleted}


@app.post("/users/{user_id}/avatar")
async def upload_avatar(
    user_id: int,
    request: Request,
    avatar: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Загрузка аватара пользователя"""
    
    print(f"📥 Загрузка аватара для пользователя {user_id}")
    
    # Проверяем токен
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_user_id = payload.get("sub")
        if int(token_user_id) != user_id:
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Cannot change another user's avatar"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    
    # Проверяем пользователя
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return JSONResponse(
            status_code=404,
            content={"success": False, "detail": "User not found"}
        )
    
    # Проверяем файл
    if not avatar.content_type or not avatar.content_type.startswith('image/'):
        return JSONResponse(
            status_code=400,
            content={"success": False, "detail": "File must be an image"}
        )
    
    try:
        # Читаем файл
        content = await avatar.read()
        
        # Проверяем размер (макс 5MB)
        if len(content) > 5 * 1024 * 1024:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "File too large (max 5MB)"}
            )
        
        # Удаляем старые аватары
        for old_file in AVATAR_DIR.glob(f"avatar_{user_id}_*"):
            try:
                old_file.unlink()
                print(f"🗑️ Удален старый: {old_file.name}")
            except:
                pass
        
        # Сохраняем новый
        ext = avatar.filename.split('.')[-1] if avatar.filename else 'png'
        filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
        file_path = AVATAR_DIR / filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        print(f"✅ Аватар сохранен: {filename} ({len(content)} bytes)")
        
        return JSONResponse(content={
            "success": True,
            "message": "Avatar uploaded successfully",
            "filename": filename,
            "url": f"/uploads/avatars/{filename}"
        })
        
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": f"Error: {str(e)}"}
        )


@app.get("/users/avatar-file/{user_id}")
async def get_avatar_file(user_id: int):
    """Получить файл аватара"""
    
    print(f"🔍 Запрос аватара для {user_id}")
    
    avatar_files = list(AVATAR_DIR.glob(f"avatar_{user_id}_*"))
    
    if avatar_files:
        file_path = avatar_files[0]
        print(f"✅ Найден: {file_path.name}")
        return FileResponse(
            file_path,
            media_type="image/webp" if file_path.suffix == '.webp' else "image/png",
            headers={
                "Cache-Control": "public, max-age=86400"
            }
        )
    
    print(f"❌ Аватар не найден для {user_id}")
    return JSONResponse(
        status_code=404,
        content={"success": False, "detail": "Avatar not found"}
    )

@app.delete("/api/admin/force-delete-all")
async def admin_force_delete_all(db: Session = Depends(get_db)):
    """Админ принудительно удаляет все сюрпризы (сначала связи)"""
    try:
        # 1. Удаляем из temporary_reservations
        db.query(TemporaryReservation).delete()
        
        # 2. Удаляем из cart_items
        db.query(CartItem).delete()
        
        # 3. Обновляем заказы (убираем ссылки)
        db.query(Order).update({Order.surprise_bag_id: None})
        
        # 4. Удаляем из surprise_bag_items
        db.query(SurpriseBagItem).delete()
        
        # 5. Удаляем сами сюрпризы
        deleted = db.query(SurpriseBag).delete()
        
        db.commit()
        return {"success": True, "deleted": deleted}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@app.delete("/api/debug/nuke-all-bags")
async def nuke_all_bags(db: Session = Depends(get_db)):
    """Полностью очистить все сюрпризы и связи"""
    try:
        # 1. Удаляем временные резервации
        db.query(TemporaryReservation).delete()
        
        # 2. Удаляем из корзины
        db.query(CartItem).delete()
        
        # 3. Обновляем заказы (убираем ссылки)
        db.query(Order).update({Order.surprise_bag_id: None})
        
        # 4. Удаляем связи сюрпризов с продуктами
        db.query(SurpriseBagItem).delete()
        
        # 5. Удаляем сами сюрпризы
        deleted = db.query(SurpriseBag).delete()
        
        db.commit()
        return {"success": True, "deleted": deleted, "message": f"Удалено {deleted} сюрпризов"}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

@app.delete("/api/debug/force-delete-all-bags")
async def force_delete_all_bags(db: Session = Depends(get_db)):
    """Принудительное удаление всех сюрпризов"""
    try:
        # Сначала удаляем связи
        db.query(SurpriseBagItem).delete()
        # Потом сами сюрпризы
        deleted = db.query(SurpriseBag).delete()
        db.commit()
        return {"success": True, "deleted": deleted}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    




# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.get("/api/supplier/stats")
async def get_supplier_stats(request: Request, db: Session = Depends(get_db)):
    """Get statistics for the authenticated supplier"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        supplier_id = payload.get("supplier_id")
        if not supplier_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
        
        # Проверяем роль
        if payload.get("role") != "supplier":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Not a supplier"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        from datetime import datetime
        
        # Get all orders
        orders = db.query(Order).filter(Order.supplier_id == int(supplier_id)).all()
        
        total_orders = len(orders)
        
        # ✅ ИСПРАВЛЕНО: проверка статусов как строки (БЕЗ ENUM)
        pending_orders = len([o for o in orders if o.status == "pending"])
        confirmed_orders = len([o for o in orders if o.status == "confirmed"])
        completed_orders = len([o for o in orders if o.status == "delivered"])
        cancelled_orders = len([o for o in orders if o.status == "cancelled"])
        
        total_revenue = sum([o.amount_paid or 0 for o in orders if o.status == "delivered"])
        
        # Today's orders
        today = datetime.utcnow().date()
        today_orders = len([o for o in orders if o.created_at and o.created_at.date() == today])
        
        # Active bags count
        active_bags = db.query(SurpriseBag).filter(
            SurpriseBag.supplier_id == int(supplier_id),
            SurpriseBag.is_active == True,
            SurpriseBag.available_quantity > 0
        ).count()
        
        return {
            "success": True,
            "stats": {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "confirmed_orders": confirmed_orders,
                "completed_orders": completed_orders,
                "cancelled_orders": cancelled_orders,
                "today_orders": today_orders,
                "total_revenue": total_revenue,
                "active_bags": active_bags
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )


# backend/routers/ratings.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.database import get_db
from backend.models import Rating, SurpriseBag, User
from backend.schemas import (
    RatingCreate, 
    RatingResponse, 
    RatingUpdate, 
    RatingStats,
    MyRatingResponse
)


router = APIRouter(prefix="/api/surprise-bags", tags=["ratings"])

# ============================================
# 1. ПОЛУЧИТЬ РЕЙТИНГ ДЛЯ СЮРПРИЗА
# ============================================
@router.get("/{bag_id}/rating", response_model=RatingStats)
def get_bag_rating(
    bag_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить рейтинг и статистику для сюрприза
    """
    # Проверяем существует ли сюрприз
    bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
    if not bag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сюрприз не найден"
        )
    
    # Получаем все рейтинги
    ratings = db.query(Rating).filter(Rating.bag_id == bag_id).all()
    
    if not ratings:
        return RatingStats(
            average_rating=0.0,
            total_ratings=0,
            rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            recent_ratings=[]
        )
    
    # Вычисляем статистику
    avg_rating = sum(r.rating for r in ratings) / len(ratings)
    
    # Распределение оценок
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in ratings:
        rounded = int(round(r.rating))
        if rounded in distribution:
            distribution[rounded] += 1
    
    # Последние 5 оценок
    recent = sorted(ratings, key=lambda x: x.created_at, reverse=True)[:5]
    
    return RatingStats(
        average_rating=round(avg_rating, 2),
        total_ratings=len(ratings),
        rating_distribution=distribution,
        recent_ratings=[
            {
                "id": r.id,
                "rating": r.rating,
                "comment": r.comment,
                "user_id": r.user_id,
                "created_at": r.created_at.isoformat()
            }
            for r in recent
        ]
    )

# ============================================
# 2. ДОБАВИТЬ РЕЙТИНГ
# ============================================
@router.post("/{bag_id}/rating", response_model=RatingResponse)
def add_rating(
    bag_id: int,
    rating_data: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Добавить оценку для сюрприза
    """
    # Проверяем существует ли сюрприз
    bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
    if not bag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сюрприз не найден"
        )
    
    # Проверяем валидность оценки
    if not 1.0 <= rating_data.rating <= 5.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Оценка должна быть от 1.0 до 5.0"
        )
    
    # Проверяем не оставлял ли пользователь уже оценку
    existing = db.query(Rating).filter(
        Rating.bag_id == bag_id,
        Rating.user_id == current_user.id
    ).first()
    
    if existing:
        # Обновляем существующую оценку
        existing.rating = rating_data.rating
        existing.comment = rating_data.comment
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    
    # Создаем новую оценку
    new_rating = Rating(
        bag_id=bag_id,
        user_id=current_user.id,
        rating=rating_data.rating,
        comment=rating_data.comment
    )
    
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    
    return new_rating

# ============================================
# 3. ОБНОВИТЬ РЕЙТИНГ
# ============================================
@router.put("/{bag_id}/rating", response_model=RatingResponse)
def update_rating(
    bag_id: int,
    rating_data: RatingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обновить свою оценку для сюрприза
    """
    # Находим оценку
    rating = db.query(Rating).filter(
        Rating.bag_id == bag_id,
        Rating.user_id == current_user.id
    ).first()
    
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Оценка не найдена"
        )
    
    # Обновляем
    rating.rating = rating_data.rating
    rating.comment = rating_data.comment
    rating.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(rating)
    
    return rating

# ============================================
# 4. УДАЛИТЬ РЕЙТИНГ
# ============================================
@router.delete("/{bag_id}/rating", status_code=status.HTTP_204_NO_CONTENT)
def delete_rating(
    bag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Удалить свою оценку для сюрприза
    """
    rating = db.query(Rating).filter(
        Rating.bag_id == bag_id,
        Rating.user_id == current_user.id
    ).first()
    
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Оценка не найдена"
        )
    
    db.delete(rating)
    db.commit()

# ============================================
# 5. ПОЛУЧИТЬ ВСЕ ОЦЕНКИ ПОЛЬЗОВАТЕЛЯ
# ============================================
@router.get("/my/ratings", response_model=List[RatingResponse])
def get_my_ratings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить все оценки текущего пользователя
    """
    ratings = db.query(Rating).filter(
        Rating.user_id == current_user.id
    ).all()
    
    return ratings

# ============================================
# 6. ПОЛУЧИТЬ ОЦЕНКУ ПОЛЬЗОВАТЕЛЯ ДЛЯ СЮРПРИЗА
# ============================================
@router.get("/{bag_id}/my-rating", response_model=Optional[MyRatingResponse])
def get_my_rating_for_bag(
    bag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить оценку текущего пользователя для конкретного сюрприза
    """
    rating = db.query(Rating).filter(
        Rating.bag_id == bag_id,
        Rating.user_id == current_user.id
    ).first()
    
    if not rating:
        return None
    
    return rating
# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.put("/api/supplier/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update order status (for supplier dashboard)"""
    
    # ✅ Проверяем авторизацию
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Проверяем что это поставщик
        if payload.get("role") != "supplier":
            return JSONResponse(
                status_code=403,
                content={"success": False, "error": "Not a supplier"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": f"Authentication error: {str(e)}"}
        )
    
    try:
        # Get JSON data
        data = await request.json()
        new_status = data.get("status")
        
        print(f"📝 Received status update: order_id={order_id}, new_status={new_status}")
        
        if not new_status:
            return {"success": False, "error": "Status is required"}
        
        # ✅ Валидные статусы
        valid_statuses = [
            "pending", "confirmed", "preparing", "ready_for_pickup",
            "picked_up", "out_for_delivery", "nearby", "delivered", "cancelled"
        ]
        
        if new_status not in valid_statuses:
            return {"success": False, "error": f"Invalid status: {new_status}"}
        
        # Find the order
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"success": False, "error": f"Order {order_id} not found"}
        
        print(f"📦 Found order: {order.order_number}, current status: {order.status}")
        
        # ✅ ИСПРАВЛЕНО: старый статус - строка (без .value)
        old_status = order.status if order.status else "unknown"
        
        # ✅ ИСПРАВЛЕНО: новый статус - строка (БЕЗ ENUM)
        order.status = new_status
        
        from datetime import datetime
        
        # Update delivery status based on order status
        if new_status == "out_for_delivery":
            order.delivery_started_at = datetime.utcnow()
            order.delivery_deadline = datetime.utcnow() + timedelta(minutes=30)
        elif new_status == "nearby":
            order.driver_lat = data.get("lat")
            order.driver_lon = data.get("lon")
            order.last_location_update = datetime.utcnow()
        elif new_status == "delivered":
            order.delivered_at = datetime.utcnow()
            # ✅ Освобождаем курьера
            if order.assigned_courier_id:
                db.query(CourierProfile).filter(
                    CourierProfile.user_id == order.assigned_courier_id
                ).update({
                    "current_order_id": None,
                    "current_order_status": None,
                    "is_available": True,
                    "is_online": True
                })
        elif new_status == "confirmed":
            order.confirmed_at = datetime.utcnow()
        elif new_status == "ready_for_pickup":
            order.ready_at = datetime.utcnow()
        elif new_status == "cancelled":
            order.cancelled_at = datetime.utcnow()
            # ✅ Возвращаем товар
            if order.surprise_bag_id:
                bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
                if bag:
                    bag.available_quantity += 1
                    if bag.available_quantity > 0:
                        bag.is_active = True
        
        # Add tracking record
        tracking = OrderTracking(
            order_id=order.id,
            status=order.status,
            message=f"Status changed from {old_status} to {new_status}",
            created_at=datetime.utcnow()
        )
        db.add(tracking)
        db.commit()
        
        print(f"✅ Order {order.order_number} status updated to {new_status}")
        
        return {
            "success": True,
            "message": f"Status updated to {new_status}",
            "order_id": order.id,
            "order_number": order.order_number,
            "old_status": old_status,
            "new_status": new_status
        }
        
    except Exception as e:
        print(f"❌ Error updating status: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}

@app.delete("/api/supplier/surprise-bags/{bag_id}")
async def delete_surprise_bag(bag_id: int, request: Request, db: Session = Depends(get_db)):
    """Delete a surprise bag (hard delete)"""
    supplier_id = request.cookies.get("supplier_id")
    
    if not supplier_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    bag = db.query(SurpriseBag).filter(
        SurpriseBag.id == bag_id,
        SurpriseBag.supplier_id == int(supplier_id)
    ).first()
    
    if not bag:
        raise HTTPException(status_code=404, detail="Bag not found")
    
    db.delete(bag)
    db.commit()
    
    # Notify clients
    await notify_bag_deleted(bag_id)
    
    return {"success": True, "message": "Bag deleted"}
# Если у тебя есть эндпоинт для обновления сюрприза, добавь туда уведомление:
# Например:
@app.put("/api/supplier/surprise-bags/{bag_id}/toggle")
async def toggle_bag_status(
    bag_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Включить/выключить сюрприз-пакет"""
    
    try:
        # Получаем токен
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Bearer token required"}
            )
        
        token = auth_header.split(" ")[1]
        
        # Декодируем токен
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        # Находим поставщика
        supplier = db.query(Supplier).filter(Supplier.user_id == int(user_id)).first()
        if not supplier:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Supplier not found"}
            )
        
        # Находим сюрприз
        bag = db.query(SurpriseBag).filter(
            SurpriseBag.id == bag_id,
            SurpriseBag.supplier_id == supplier.id  # ✅ supplier.id РАБОТАЕТ
        ).first()
        
        if not bag:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Bag not found"}
            )
        
        # Переключаем статус
        bag.is_active = not bag.is_active
        db.commit()
        
        return JSONResponse(content={
            "success": True,
            "is_active": bag.is_active,
            "message": "Статус изменен"
        })
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/test-websocket")
async def test_websocket():
    """Test endpoint to broadcast a test message"""
    await manager.broadcast({
        "type": "test",
        "message": "This is a test broadcast!",
        "timestamp": datetime.utcnow().isoformat()
    })
    return {"success": True, "message": "Test message broadcasted"}

@app.get("/api/order-statuses")
async def get_order_statuses():
    """Get all possible order statuses"""
    return {
        "statuses": [
            {"value": "pending", "label_ru": "Ожидает", "label_kz": "Күтілуде"},
            {"value": "confirmed", "label_ru": "Подтвержден", "label_kz": "Расталды"},
            {"value": "preparing", "label_ru": "Готовится", "label_kz": "Дайындалуда"},
            {"value": "ready_for_pickup", "label_ru": "Готов к выдаче", "label_kz": "Дайын"},
            {"value": "out_for_delivery", "label_ru": "В пути", "label_kz": "Жолда"},
            {"value": "nearby", "label_ru": "Рядом", "label_kz": "Жақын жерде"},
            {"value": "delivered", "label_ru": "Доставлен", "label_kz": "Жеткізілді"},
            {"value": "cancelled", "label_ru": "Отменен", "label_kz": "Бас тартылды"}
        ]
    }

# backend/main.py - ЗАМЕНИТЕ ваш существующий check-auth
# backend/main.py - ИСПРАВЛЕННЫЙ check-auth

@app.get("/api/check-auth")
async def check_auth(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"authenticated": False, "error": "No token provided"}
    
    token = auth_header.split(" ")[1]
    
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            return {"authenticated": False}
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            return {"authenticated": False}
        
        # ✅ role УЖЕ СТРОКА (VARCHAR)
        return {
            "authenticated": True,
            "user_id": user.id,
            "user": {
                "id": user.id,
                "phone": user.phone,
                "full_name": user.full_name,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role or "customer"
            }
        }
    except jwt.ExpiredSignatureError:
        return {"authenticated": False, "error": "Token expired"}
    except jwt.JWTError:
        return {"authenticated": False, "error": "Invalid token"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"authenticated": False, "error": str(e)}

@app.get("/api/debug-cookies")
async def debug_cookies(request: Request):
    cookies = request.cookies
    return {
        "user_id": cookies.get("user_id"),
        "user_phone": cookies.get("user_phone"),
        "all_cookies": dict(cookies)
    }
# backend/main.py - добавьте этот эндпоинт


uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/supplier/couriers")
async def supplier_couriers_page(request: Request, db: Session = Depends(get_db)):
    """Страница управления курьерами для поставщика"""
    
    # Получаем токен из query param
    token = request.query_params.get("token")
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        return RedirectResponse(url="/supplier/login?error=no_token", status_code=303)
    
    # Декодируем токен
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("role") != "supplier":
            return RedirectResponse(url="/supplier/login?error=invalid_role", status_code=303)
        
        supplier_id = payload.get("supplier_id")
        if not supplier_id:
            user_id = int(payload.get("sub"))
            supplier = db.query(Supplier).filter(Supplier.user_id == user_id).first()
            if not supplier:
                return RedirectResponse(url="/supplier/login?error=supplier_not_found", status_code=303)
            supplier_id = supplier.id
        
    except Exception as e:
        print(f"❌ Token error: {e}")
        return RedirectResponse(url="/supplier/login?error=invalid_token", status_code=303)
    
    # Получаем поставщика
    supplier = db.query(Supplier).filter(Supplier.id == int(supplier_id)).first()
    if not supplier:
        return RedirectResponse(url="/supplier/login?error=supplier_not_found", status_code=303)
    
    # ✅ ИСПРАВЛЕНО: убираем фильтр по supplier_id
    couriers = db.query(CourierProfile).all()
    
    couriers_list = []
    for c in couriers:
        user = db.query(User).filter(User.id == c.user_id).first()
        couriers_list.append({
            "id": c.id,
            "user_id": c.user_id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "phone": c.phone,
            "car_model": c.car_model,
            "car_number": c.car_number,
            "is_online": c.is_online,
            "is_verified": c.is_verified,
            "rating": c.rating,
            "total_deliveries": c.total_deliveries,
            "created_at": c.created_at
        })
    
    return templates.TemplateResponse("supplier_couriers.html", {
        "request": request,
        "supplier": supplier,
        "couriers": couriers_list,
        "lang": request.query_params.get("lang", "ru"),
        "token": token
    })
# В main.py
# backend/main.py - добавьте

@app.delete("/api/supplier/couriers/{courier_id}")
async def remove_courier(courier_id: int, request: Request, db: Session = Depends(get_db)):
    """Удалить курьера"""
    supplier_id = request.cookies.get("supplier_id")
    
    if not supplier_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    courier = db.query(CourierProfile).filter(
        CourierProfile.id == courier_id,
        CourierProfile.supplier_id == int(supplier_id)
    ).first()
    
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    user = db.query(User).filter(User.id == courier.user_id).first()
    
    if user:
        db.delete(user)
    db.delete(courier)
    db.commit()
    
    return {"success": True, "message": "Курьер удален"}

# backend/main.py - ИСПРАВЛЕННАЯ ФУНКЦИЯ

@app.post("/supplier/couriers/add")
async def add_courier(request: Request, db: Session = Depends(get_db)):
    """Добавление курьера поставщиком"""
    
    # Получаем supplier_id из токена
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        supplier_id = payload.get("supplier_id")
        if not supplier_id:
            return JSONResponse(status_code=401, content={"error": "Invalid token"})
    except:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})
    
    try:
        data = await request.json()
        phone = data.get("phone", "").strip()
        full_name = data.get("full_name", "").strip()
        password = data.get("password", "")
        car_model = data.get("car_model", "").strip()
        car_number = data.get("car_number", "").strip()
        
        # ======== ВАЛИДАЦИЯ ========
        if not phone:
            return JSONResponse(status_code=400, content={"error": "Телефон обязателен"})
        if not full_name:
            return JSONResponse(status_code=400, content={"error": "ФИО обязательно"})
        if not password or len(password) < 6:
            return JSONResponse(status_code=400, content={"error": "Пароль минимум 6 символов"})
        
        # ======== ПРОВЕРКА СУЩЕСТВОВАНИЯ ========
        existing_user = db.query(User).filter(User.phone == phone).first()
        
        if existing_user:
            # Если пользователь уже есть
            courier_profile = db.query(CourierProfile).filter(CourierProfile.user_id == existing_user.id).first()
            if courier_profile:
                courier_profile.car_model = car_model
                courier_profile.car_number = car_number
                courier_profile.is_active = True
            else:
                # ✅ ИСПРАВЛЕНО: role = 'courier' (строка, БЕЗ ENUM)
                if existing_user.role != "courier":
                    existing_user.role = "courier"
                
                courier_profile = CourierProfile(
                    user_id=existing_user.id,
                    first_name=full_name.split()[0] if full_name.split() else full_name,
                    last_name=full_name.split()[1] if len(full_name.split()) > 1 else "",
                    phone=phone,
                    car_model=car_model,
                    car_number=car_number,
                    courier_type="driver" if car_model else "pedestrian",
                    is_available=True,
                    is_active=True
                )
                db.add(courier_profile)
        else:
            # Создаем нового пользователя
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            name_parts = full_name.split()
            first_name = name_parts[0] if name_parts else full_name
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            # ✅ ИСПРАВЛЕНО: role = 'courier' (строка, БЕЗ ENUM)
            new_user = User(
                phone=phone,
                full_name=full_name,
                first_name=first_name,
                last_name=last_name,
                password=password_hash,
                role="courier",  # ✅ СТРОКА, БЕЗ ENUM
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(new_user)
            db.flush()
            
            courier_profile = CourierProfile(
                user_id=new_user.id,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                car_model=car_model,
                car_number=car_number,
                courier_type="driver" if car_model else "pedestrian",
                is_available=True,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(courier_profile)
        
        db.commit()
        return {"success": True, "message": "Курьер добавлен"}
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/courier/orders")
async def get_courier_orders(request: Request, db: Session = Depends(get_db)):
    """Получить заказы, назначенные курьеру"""
    token = request.cookies.get("courier_token")
    if not token or token not in courier_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = courier_sessions[token]
    courier_id = session["courier_id"]
    
    # Находим заказы, назначенные этому курьеру
    assignments = db.query(AssignedOrder).filter(
        AssignedOrder.courier_id == courier_id,
        AssignedOrder.status == "assigned"
    ).all()
    
    order_ids = [a.order_id for a in assignments]
    
    orders = db.query(Order).filter(Order.id.in_(order_ids)).order_by(Order.created_at.desc()).all()
    
    result = []
    for order in orders:
        supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        result.append({
            "id": order.id,
            "order_number": order.order_number,
            "customer_address": order.customer_address,
            "customer_lat": order.customer_lat,
            "customer_lon": order.customer_lon,
            "supplier_name": supplier.business_name if supplier else "",
            "supplier_address": supplier.address if supplier else "",
            "supplier_lat": supplier.lat if supplier else 0,
            "supplier_lon": supplier.lon if supplier else 0,
            "status": order.status.value if order.status else "pending",
            "amount": order.amount_paid or 0,
            "delivery_deadline": order.delivery_deadline.isoformat() if order.delivery_deadline else None
        })
    
    return {"orders": result}



# backend/main.py - ИСПРАВЛЕННЫЙ ЭНДПОИНТ

@app.post("/api/courier/orders/{order_id}/status")
async def update_courier_order_status(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Курьер обновляет статус заказа"""
    
    # ✅ ИСПРАВЛЕНО: проверка через Bearer токен (не cookies)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Bearer token required"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "detail": "Invalid token"}
            )
        
        # Проверяем что это курьер
        if payload.get("role") != "courier":
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Not a courier"}
            )
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": "Token expired"}
        )
    except jwt.JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Invalid token: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"success": False, "detail": f"Authentication error: {str(e)}"}
        )
    
    try:
        data = await request.json()
        new_status = data.get("status")
        
        if not new_status:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Status is required"}
            )
        
        # ✅ Проверяем что статус валидный
        valid_statuses = [
            "pending", "confirmed", "preparing", "ready_for_pickup",
            "picked_up", "out_for_delivery", "nearby", "delivered", "cancelled"
        ]
        
        if new_status not in valid_statuses:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": f"Invalid status: {new_status}"}
            )
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Order not found"}
            )
        
        # Проверяем что заказ назначен этому курьеру
        if order.assigned_courier_id != int(user_id):
            return JSONResponse(
                status_code=403,
                content={"success": False, "detail": "Order not assigned to you"}
            )
        
        from datetime import datetime
        
        # ✅ ИСПРАВЛЕНО: обновление статуса как строка (БЕЗ ENUM)
        if new_status == "picked_up":
            order.status = "picked_up"
        elif new_status == "out_for_delivery":
            order.status = "out_for_delivery"
        elif new_status == "nearby":
            order.status = "nearby"
        elif new_status == "delivered":
            order.status = "delivered"
            order.delivered_at = datetime.utcnow()
        elif new_status == "ready_for_pickup":
            order.status = "ready_for_pickup"
        elif new_status == "confirmed":
            order.status = "confirmed"
        elif new_status == "preparing":
            order.status = "preparing"
        else:
            order.status = new_status
        
        # Обновляем статус курьера
        courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
        if courier:
            courier.current_order_status = order.status
            
            # Если заказ доставлен - освобождаем курьера
            if order.status == "delivered":
                courier.current_order_id = None
                courier.current_order_status = None
                courier.is_available = True
                courier.is_online = True
        
        db.commit()
        
        print(f"✅ Курьер обновил статус заказа #{order.order_number}: {new_status}")
        
        return {
            "success": True,
            "message": f"Status updated to {new_status}",
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )





@app.post("/api/courier/location")
async def update_courier_location(request: Request, db: Session = Depends(get_db)):
    """Обновление GPS-координат курьера"""
    token = request.cookies.get("courier_token")
    if not token or token not in courier_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    order_id = data.get("order_id")
    lat = data.get("lat")
    lon = data.get("lon")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.driver_lat = lat
        order.driver_lon = lon
        order.last_location_update = datetime.utcnow()
        db.commit()
    
    return {"success": True}


@app.post("/api/courier/logout")
async def courier_logout(request: Request):
    """Выход курьера"""
    token = request.cookies.get("courier_token")
    if token in courier_sessions:
        del courier_sessions[token]
    
    response = JSONResponse({"success": True})
    response.delete_cookie("courier_token")
    return response

@app.get("/supplier/couriers")
async def get_supplier_couriers(request: Request, db: Session = Depends(get_db)):
    supplier_id = request.cookies.get("supplier_id")
    if not supplier_id:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    
    couriers = db.query(CourierProfile).filter(
        CourierProfile.supplier_id == int(supplier_id)
    ).all()
    
    result = []
    for c in couriers:
        user = db.query(User).filter(User.id == c.user_id).first()
        if user:
            result.append({
                "id": user.id,
                "full_name": user.full_name,
                "phone": user.phone,
                "car_model": c.car_model,
                "car_number": c.car_number,
                "is_active": user.is_active,
                "created_at": c.created_at
            })
    
    return {"couriers": result}

@app.get("/supplier/couriers")
async def supplier_couriers_page(request: Request, db: Session = Depends(get_db)):
    # Проверка авторизации поставщика
    supplier_id = request.cookies.get("supplier_id")
    
    if not supplier_id:
        return RedirectResponse(url="/supplier/login", status_code=303)
    
    supplier = db.query(Supplier).filter(Supplier.id == int(supplier_id)).first()
    if not supplier:
        response = RedirectResponse(url="/supplier/login", status_code=303)
        response.delete_cookie("supplier_id")
        return response
    
    # Получаем курьеров этого поставщика
    courier_profiles = db.query(CourierProfile).filter(
        CourierProfile.supplier_id == int(supplier_id)
    ).all()
    
    couriers = []
    for cp in courier_profiles:
        user = db.query(User).filter(User.id == cp.user_id).first()
        if user:
            couriers.append({
                "id": user.id,
                "full_name": user.full_name,
                "phone": user.phone,
                "car_model": cp.car_model,
                "car_number": cp.car_number,
                "is_active": user.is_active,
                "created_at": cp.created_at
            })
    
    return templates.TemplateResponse("supplier_couriers.html", {
        "request": request,
        "supplier": supplier,
        "couriers": couriers,
        "lang": request.query_params.get("lang", "ru")
    })

@app.get("/supplier/orders")
async def supplier_orders_page(request: Request, db: Session = Depends(get_db)):
    """Страница всех заказов поставщика"""
    
    # ✅ ПОЛУЧАЕМ ТОКЕН ИЗ QUERY PARAM ИЛИ HEADER
    token = request.query_params.get("token")
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        return RedirectResponse(url="/supplier/login?error=no_token", status_code=303)
    
    # ✅ ДЕКОДИРУЕМ ТОКЕН
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("role") != "supplier":
            return RedirectResponse(url="/supplier/login?error=invalid_role", status_code=303)
        
        supplier_id = payload.get("supplier_id")
        if not supplier_id:
            user_id = int(payload.get("sub"))
            supplier = db.query(Supplier).filter(Supplier.user_id == user_id).first()
            if not supplier:
                return RedirectResponse(url="/supplier/login?error=supplier_not_found", status_code=303)
            supplier_id = supplier.id
        
    except jwt.ExpiredSignatureError:
        return RedirectResponse(url="/supplier/login?error=token_expired", status_code=303)
    except jwt.JWTError as e:
        print(f"❌ JWT Error: {e}")
        return RedirectResponse(url="/supplier/login?error=invalid_token", status_code=303)
    except Exception as e:
        print(f"❌ Error: {e}")
        return RedirectResponse(url="/supplier/login?error=unknown", status_code=303)
    
    # ✅ ПОЛУЧАЕМ ПОСТАВЩИКА
    supplier = db.query(Supplier).filter(Supplier.id == int(supplier_id)).first()
    if not supplier:
        return RedirectResponse(url="/supplier/login?error=supplier_not_found", status_code=303)
    
    return templates.TemplateResponse("supplier_orders.html", {
        "request": request,
        "supplier": supplier,
        "token": token  # ← ПЕРЕДАЕМ ТОКЕН В ШАБЛОН
    })

@app.get("/supplier/surprise-bags")
async def supplier_bags_page(request: Request, db: Session = Depends(get_db)):
    """Страница управления сюрпризами поставщика"""
    supplier_id = request.cookies.get("supplier_id")
    if not supplier_id:
        return RedirectResponse(url="/supplier/login", status_code=303)
    
    supplier = db.query(Supplier).filter(Supplier.id == int(supplier_id)).first()
    if not supplier:
        return RedirectResponse(url="/supplier/login", status_code=303)
    
    return templates.TemplateResponse("supplier_bags.html", {
        "request": request,
        "supplier": supplier
    })

# backend/main.py - ДОБАВИТЬ В КОНЕЦ ФАЙЛА

from backend.websocket_manager import manager
from fastapi import WebSocket, WebSocketDisconnect
from jose import jwt, JWTError

@app.websocket("/ws/supplier/{supplier_id}")
async def websocket_supplier(
    websocket: WebSocket,
    supplier_id: int
):
    """WebSocket для поставщика"""
    
    # Проверяем токен из query параметра
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Token required")
        return
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        if role != "supplier":
            await websocket.close(code=1008, reason="Not a supplier")
            return
        
        # Проверяем что supplier_id совпадает
        token_supplier_id = payload.get("supplier_id")
        if not token_supplier_id or int(token_supplier_id) != supplier_id:
            await websocket.close(code=1008, reason="Invalid supplier")
            return
        
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        return
    except Exception as e:
        print(f"❌ WS Error: {e}")
        await websocket.close(code=1011, reason="Internal error")
        return
    
    # Принимаем соединение
    await websocket.accept()
    
    # Регистрируем в менеджере
    await manager.connect(websocket, "supplier", supplier_id)
    print(f"✅ WebSocket connected for supplier {supplier_id}")
    
    try:
        while True:
            # Ждем сообщения
            data = await websocket.receive_text()
            print(f"📨 WS message from supplier {supplier_id}: {data}")
            
            try:
                # Пытаемся распарсить JSON
                import json
                message = json.loads(data)
                
                # Обработка разных типов сообщений
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "broadcast":
                    # Пересылаем всем поставщикам
                    await manager.broadcast(message, f"supplier_{supplier_id}")
                    
            except json.JSONDecodeError:
                # Если не JSON - игнорируем
                pass
                
    except WebSocketDisconnect:
        print(f"❌ WebSocket disconnected for supplier {supplier_id}")
    finally:
        # Отключаем
        await manager.disconnect(websocket, "supplier", supplier_id)


# ============ RUN APP ============
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)