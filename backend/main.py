from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from backend.database import SessionLocal, engine, get_db
from backend import models
from backend.models import Food, User, UserRole, Supplier, SurpriseBag, Order, OrderStatus, DeliveryStatus, OrderTracking, Review
from datetime import datetime, timedelta
import secrets
import os
import math
import hashlib
from fastapi.staticfiles import StaticFiles
from typing import Optional
from pydantic import BaseModel
from backend.schemas import (
    OrderCreate, PhoneVerificationRequest, PhoneRegisterRequest
)
from backend.models import (
    CartItem,Food, User, UserRole, Supplier, SurpriseBag, 
    Order, OrderStatus, DeliveryStatus, OrderTracking, Review
)
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
    allow_origins=["http://localhost:3000", "https://toogood-2ncf.onrender.com", "https://sarqyn-mobile.onrender.com"],
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




# WEBSOCKET

# Добавь это в начало файла (рядом с другими импортами)
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import json




# ============ CART API ENDPOINTS ============

# backend/main.py - добавь эти эндпоинты

# ============ CART API ENDPOINTS ============

@app.get("/api/cart")
async def get_cart(request: Request, db: Session = Depends(get_db)):
    """Get current user's cart"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        return {"success": False, "error": "Not authenticated", "items": [], "total": 0, "count": 0}
    
    cart_items = db.query(CartItem).filter(
        CartItem.user_id == int(user_id)
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


@app.post("/api/cart/add")
async def add_to_cart(request: Request, db: Session = Depends(get_db)):
    """Add item to cart"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    bag_id = data.get("bag_id")
    quantity = data.get("quantity", 1)
    
    # Check if bag exists and is available
    bag = db.query(SurpriseBag).filter(
        SurpriseBag.id == bag_id,
        SurpriseBag.is_active == True,
        SurpriseBag.available_quantity >= quantity
    ).first()
    
    if not bag:
        raise HTTPException(status_code=404, detail="Item not available")
    
    # Check if item already in cart
    existing = db.query(CartItem).filter(
        CartItem.user_id == int(user_id),
        CartItem.surprise_bag_id == bag_id
    ).first()
    
    if existing:
        existing.quantity += quantity
        existing.updated_at = datetime.utcnow()
    else:
        cart_item = CartItem(
            user_id=int(user_id),
            surprise_bag_id=bag_id,
            quantity=quantity
        )
        db.add(cart_item)
    
    db.commit()
    
    # Get updated cart count
    cart_count = db.query(CartItem).filter(
        CartItem.user_id == int(user_id)
    ).with_entities(func.sum(CartItem.quantity)).scalar() or 0
    
    return {
        "success": True, 
        "message": "Added to cart",
        "cart_count": cart_count
    }


@app.delete("/api/cart/remove/{bag_id}")
async def remove_from_cart(bag_id: int, request: Request, db: Session = Depends(get_db)):
    """Remove item from cart"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == int(user_id),
        CartItem.surprise_bag_id == bag_id
    ).first()
    
    if cart_item:
        db.delete(cart_item)
        db.commit()
    
    return {"success": True, "message": "Removed from cart"}


@app.put("/api/cart/update/{bag_id}")
async def update_cart_quantity(bag_id: int, request: Request, db: Session = Depends(get_db)):
    """Update item quantity in cart"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    quantity = data.get("quantity", 1)
    
    if quantity <= 0:
        return await remove_from_cart(bag_id, request, db)
    
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == int(user_id),
        CartItem.surprise_bag_id == bag_id
    ).first()
    
    if cart_item:
        cart_item.quantity = quantity
        cart_item.updated_at = datetime.utcnow()
        db.commit()
    
    return {"success": True, "message": "Cart updated"}

# backend/main.py - добавь этот эндпоинт для проверки

@app.get("/api/debug/users")
async def debug_users(request: Request, db: Session = Depends(get_db)):
    """Проверка пользователей в БД (только для отладки)"""
    
    # Получаем всех пользователей
    users = db.query(User).all()
    
    result = {
        "total_users": len(users),
        "users": []
    }
    
    for user in users:
        result["users"].append({
            "id": user.id,
            "phone": user.phone,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "phone_verified": user.phone_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None
        })
    
    # Также проверь таблицу suppliers
    suppliers = db.query(Supplier).all()
    result["total_suppliers"] = len(suppliers)
    
    return result




@app.delete("/api/cart/clear")
async def clear_cart(request: Request, db: Session = Depends(get_db)):
    """Clear all items from cart"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db.query(CartItem).filter(CartItem.user_id == int(user_id)).delete()
    db.commit()
    
    return {"success": True, "message": "Cart cleared"}
@app.post("/api/orders/create-from-cart")
async def create_orders_from_cart(request: Request, db: Session = Depends(get_db)):
    """Create orders from all items in cart"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    customer_lat = data.get("lat")
    customer_lon = data.get("lon")
    customer_address = data.get("address")
    
    # Get cart items
    cart_items = db.query(CartItem).filter(
        CartItem.user_id == int(user_id)
    ).all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
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
        
        # Create order for each item (or group by supplier)
        order_number = f"ORD-{secrets.token_hex(4).upper()}"
        amount = bag.discounted_price * cart_item.quantity
        
        order = Order(
            user_id=int(user_id),
            supplier_id=bag.supplier_id,
            surprise_bag_id=bag.id,
            order_number=order_number,
            status=OrderStatus.PENDING,
            customer_lat=customer_lat,
            customer_lon=customer_lon,
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
        
        # Decrease quantity
        bag.available_quantity -= cart_item.quantity
        total_amount += amount
        orders_created.append(order)
    
    # Clear cart
    for cart_item in cart_items:
        db.delete(cart_item)
    
    db.commit()
    
    # Send WebSocket notification
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
                "amount": order.amount_paid
            } for order in orders_created
        ],
        "total_amount": total_amount,
        "message": f"Created {len(orders_created)} order(s)"
    }


@app.get("/api/orders/my")
async def get_my_orders(request: Request, db: Session = Depends(get_db)):
    """Get all orders for current user"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    orders = db.query(Order).filter(
        Order.user_id == int(user_id)
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
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"🔌 WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

manager = ConnectionManager()

# ============ WEBSOCKET ENDPOINT ============
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connected",
            "message": "Connected to Sarqyn Food WebSocket"
        }, websocket)
        
        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            print(f"📨 Received from client: {data}")
            
            # Handle client messages if needed
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)
            except:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)







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
    computed_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    print(f"DEBUG: Computed hash: {computed_hash}")
    print(f"DEBUG: Stored hash: {hashed_password}")
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
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

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


# Add this endpoint to your main.py

@app.post("/api/verify-and-register")
async def verify_and_register(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        
        # Flexible field name handling
        phone = data.get('phone') or data.get('phone_number')
        full_name = data.get('full_name') or data.get('fullName') or data.get('name')
        if full_name:
            full_name = full_name.encode('utf-8').decode('utf-8')  
        password = data.get('password')
        verification_code = data.get('verification_code') or data.get('code') or data.get('verificationCode')
        
        # Debug print
        print(f"📝 Received data: phone={phone}, name={full_name}, has_password={bool(password)}, code={verification_code}")
        
        # Validate all fields
        if not phone:
            raise HTTPException(status_code=400, detail="Phone number is required")
        if not full_name:
            raise HTTPException(status_code=400, detail="Full name is required")
        if not password:
            raise HTTPException(status_code=400, detail="Password is required")
        
        # Format phone number
        import re
        digits = re.sub(r'\D', '', phone)
        
        formatted_phone = None
        
        if digits.startswith('77') and len(digits) == 11:
            formatted_phone = '+' + digits
        elif digits.startswith('7') and len(digits) == 11:
            formatted_phone = '+' + digits
        elif digits.startswith('8') and len(digits) == 11:
            formatted_phone = '+7' + digits[1:]
        elif len(digits) == 10:
            formatted_phone = '+77' + digits
        elif digits.startswith('996') and len(digits) == 12:
            formatted_phone = '+' + digits
        elif digits.startswith('998') and len(digits) == 12:
            formatted_phone = '+' + digits
        else:
            if digits.startswith('+'):
                formatted_phone = digits
            else:
                formatted_phone = '+' + digits
        
        print(f"📞 Original phone: {phone} -> Formatted: {formatted_phone}")
        
        # Check if phone already exists
        existing_user = db.query(User).filter(User.phone == formatted_phone).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Phone number already registered")
        
        # Verify code (demo mode)
        is_verified = False
        if verification_code and len(verification_code) == 6 and verification_code.isdigit():
            is_verified = True
            print(f"✅ Code verified: {verification_code}")
        
        if not is_verified:
            print(f"⚠️ Invalid code: {verification_code}")
            raise HTTPException(status_code=400, detail="Invalid verification code. Demo code is 123456")
        
        # Create user
        hashed_password = hash_password(password)
        
        new_user = User(
            phone=formatted_phone,
            full_name=full_name,
            password=hashed_password,
            role=UserRole.CUSTOMER,
            phone_verified=True,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✅ User registered: {new_user.id} - {formatted_phone}")
        
        # 🔥 СОЗДАЕМ ОТВЕТ С КУКОЙ ДЛЯ АВТОВХОДА
        from fastapi.responses import JSONResponse
        
        response = JSONResponse({
            "success": True,
            "message": "Registration successful",
            "user_id": new_user.id
        })
        
        # Устанавливаем куку для автоматической авторизации (30 дней)
        response.set_cookie(
            key="user_id",
            value=str(new_user.id),
            httponly=True,
            samesite="lax",
            max_age=60*60*24*30  # 30 дней
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")





@app.get("/api/me")
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
@app.get("/login")
async def phone_login_page(request: Request, lang: str = "kz"):
    return templates.TemplateResponse("phone_login.html", {
        "request": request,
        "lang": lang
    })
from fastapi.responses import JSONResponse

from fastapi.responses import JSONResponse

@app.post("/api/login")
async def api_login(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        phone = data.get("phone")
        password = data.get("password")
        
        # Format phone
        formatted_phone = format_phone_number(phone)
        
        # Find user
        user = db.query(User).filter(User.phone == formatted_phone).first()
        
        if not user or not verify_password(password, user.password):
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Invalid credentials"}
            )
        
        # ✅ ОТВЕТ С ДАННЫМИ ПОЛЬЗОВАТЕЛЯ В JSON (БЕЗ КИРИЛЛИЦЫ В COOKIES)
        response = JSONResponse(
            status_code=200,
            content={
                "success": True,
                "redirect": "/",
                "user": {
                    "id": user.id,
                    "phone": user.phone,
                    "full_name": user.full_name,  # ← Кириллица здесь (в JSON)
                    "role": user.role.value if user.role else "customer"
                }
            }
        )
        
        # ✅ ТОЛЬКО БЕЗОПАСНЫЕ КУКИ (без кириллицы)
        response.set_cookie(
            key="user_id", 
            value=str(user.id),
            httponly=True,      # Нельзя прочитать через JavaScript
            samesite="lax",     # Защита от CSRF
            max_age=60*60*24*30 # 30 дней
        )
        
        response.set_cookie(
            key="phone", 
            value=user.phone,   # Телефон содержит только цифры и +
            httponly=True,
            samesite="lax",
            max_age=60*60*24*30
        )
        
        print(f"✅ Login successful for user: {user.phone}")
        return response
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
        
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    response.delete_cookie("user_phone")
    response.delete_cookie("user_name")
    return response

# ============ DELIVERY TRACKING ROUTES ============
@app.post("/api/delivery/{order_id}/start")
async def start_real_delivery(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    if not order.customer_lat or not order.customer_lon:
        raise HTTPException(status_code=400, detail="Customer location not available")
    
    distance = calculate_distance(supplier.lat, supplier.lon, order.customer_lat, order.customer_lon)
    eta_minutes = calculate_eta(distance, 40)
    
    waypoints = generate_waypoints(supplier.lat, supplier.lon, order.customer_lat, order.customer_lon, 100)
    
    delivery_cache[str(order_id)] = {
        "waypoints": waypoints,
        "current_index": 0,
        "total_distance": distance,
        "eta_minutes": eta_minutes,
        "is_active": True,
        "started_at": datetime.utcnow().isoformat()
    }
    
    order.status = OrderStatus.OUT_FOR_DELIVERY
    order.delivery_status = DeliveryStatus.EN_ROUTE
    order.driver_lat = supplier.lat
    order.driver_lon = supplier.lon
    db.commit()
    
    return {
        "success": True,
        "order_id": order_id,
        "distance_km": round(distance, 2),
        "eta_minutes": eta_minutes
    }

@app.get("/api/delivery/{order_id}/position")
async def get_delivery_position(order_id: int, db: Session = Depends(get_db)):
    cache_key = str(order_id)
    
    if cache_key in delivery_cache and delivery_cache[cache_key]["is_active"]:
        waypoints = delivery_cache[cache_key]["waypoints"]
        current_index = delivery_cache[cache_key]["current_index"]
        
        if current_index < len(waypoints):
            current_pos = waypoints[current_index]
            delivery_cache[cache_key]["current_index"] = current_index + 1
            
            # Update database
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                order.driver_lat = current_pos["lat"]
                order.driver_lon = current_pos["lon"]
                db.commit()
            
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
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                order.status = OrderStatus.DELIVERED
                order.delivery_status = DeliveryStatus.ARRIVED
                db.commit()
            return {"success": True, "is_complete": True}
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if order and order.status == OrderStatus.DELIVERED:
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
        
    

# ============ ADD MOCK DATA ============
def add_mock_data(db: Session):
    try:
        if db.query(Food).count() == 0:
            mock_foods = [
                Food(name_ru="Пицца Маргарита", name_kz="Пицца Маргарита", price=1800, image="https://images.unsplash.com/photo-1604382355076-af4b0eb60143?w=400&h=300&fit=crop", discount=40),
                Food(name_ru="Бургер", name_kz="Бургер", price=1500, image="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop", discount=40),
                Food(name_ru="Суши сет", name_kz="Суши сет", price=2250, image="https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400&h=300&fit=crop", discount=25),
                Food(name_ru="Грек салаты", name_kz="Грек салаты", price=975, image="https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400&h=300&fit=crop", discount=35),
                Food(name_ru="Цезарь", name_kz="Цезарь", price=1200, image="https://images.unsplash.com/photo-1550304943-4f24f54dd3b9?w=400&h=300&fit=crop", discount=33),
                Food(name_ru="Чизкейк", name_kz="Чизкейк", price=1200, image="https://picsum.photos/id/132/400/300", discount=20),
                Food(name_ru="Тирамису", name_kz="Тирамису", price=1300, image="https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400&h=300&fit=crop", discount=23),
                Food(name_ru="Кола", name_kz="Кола", price=400, image="https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400&h=300&fit=crop", discount=33),
                Food(name_ru="Лимонад", name_kz="Лимонад", price=500, image="https://images.unsplash.com/photo-1527960471264-932f39eb36a6?w=400&h=300&fit=crop", discount=28),
            ]
            for food in mock_foods:
                db.add(food)
            db.commit()
            print("✅ Mock foods added")
    except Exception as e:
        print(f"Error adding mock foods: {e}")
    
    try:
        if db.query(Supplier).count() == 0:
            mock_suppliers = [
                Supplier(
                    business_name="Sarqyn Restoran",
                    business_type="Restaurant",
                    description="Дәмді тағамдар",
                    city="Алматы",
                    address="Алматы, Достык 123",
                    lat=43.238, lon=76.945,
                    phone="+7 777 123 4567",
                    email="info@sarqyn.kz",
                    rating=4.8,
                    total_reviews=55,
                    is_verified=True,
                    is_active=True,
                    pickup_start_time="19:30",
                    pickup_end_time="20:00"
                )
            ]
            for supplier in mock_suppliers:
                db.add(supplier)
            db.commit()
            print("✅ Mock suppliers added")
    except Exception as e:
        print(f"Error adding mock suppliers: {e}")

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

@app.get("/api/surprise-bags")
async def get_all_surprise_bags(db: Session = Depends(get_db)):
    bags = db.query(SurpriseBag).filter(SurpriseBag.is_active == True).all()
    result = []
    for bag in bags:
        supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
        result.append({
            "id": bag.id,
            "supplier_id": bag.supplier_id,
            "supplier_name": supplier.business_name if supplier else "Unknown",
            "name": bag.name,
            "description": bag.description,
            "original_price": bag.original_price,
            "discounted_price": bag.discounted_price,
            "discount_percentage": bag.discount_percentage,
            "available_quantity": bag.available_quantity,
            "is_active": bag.is_active
        })
    return result

@app.get("/api/surprise-bags/{bag_id}")
async def get_surprise_bag(bag_id: int, db: Session = Depends(get_db)):
    bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
    if not bag:
        raise HTTPException(status_code=404, detail="Surprise bag not found")
    supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
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
        "available_quantity": bag.available_quantity
    }

@app.get("/api/suppliers/nearby")
async def get_nearby_suppliers(lat: float, lon: float, radius: float = 50, db: Session = Depends(get_db)):
    all_suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    nearby = []
    for supplier in all_suppliers:
        if supplier.lat and supplier.lon:
            distance = haversine_distance(lat, lon, supplier.lat, supplier.lon)
            if distance <= radius:
                active_bags = db.query(SurpriseBag).filter(
                    SurpriseBag.supplier_id == supplier.id,
                    SurpriseBag.is_active == True,
                    SurpriseBag.available_quantity > 0
                ).all()
                nearby.append({
                    "id": supplier.id,
                    "business_name": supplier.business_name,
                    "distance_km": round(distance, 2),
                    "rating": supplier.rating,
                    "surprise_bags": [
                        {
                            "id": bag.id,
                            "name": bag.name,
                            "discounted_price": bag.discounted_price,
                            "discount_percentage": bag.discount_percentage
                        } for bag in active_bags
                    ]
                })
    nearby.sort(key=lambda x: x["distance_km"])
    return {"count": len(nearby), "suppliers": nearby}

# ============ HOME PAGE ============
@app.get("/")
async def home(request: Request, lang: str = "kz", category: str = "all", db: Session = Depends(get_db)):
    add_mock_data(db)
    
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
@app.get("/api/suppliers/nearby")
async def get_nearby_suppliers(
    lat: float, 
    lon: float, 
    radius: float = 50, 
    db: Session = Depends(get_db)
):
    from math import radians, sin, cos, sqrt, atan2
    
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    
    all_suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    
    nearby = []
    for supplier in all_suppliers:
        if supplier.lat and supplier.lon:
            distance = haversine(lat, lon, supplier.lat, supplier.lon)
            if distance <= radius:
                active_bags = db.query(SurpriseBag).filter(
                    SurpriseBag.supplier_id == supplier.id,
                    SurpriseBag.is_active == True,
                    SurpriseBag.available_quantity > 0
                ).all()
                nearby.append({
                    "id": supplier.id,
                    "business_name": supplier.business_name,
                    "distance_km": round(distance, 2),
                    "rating": supplier.rating,
                    "surprise_bags": [
                        {
                            "id": bag.id,
                            "name": bag.name,
                            "discounted_price": bag.discounted_price,
                            "discount_percentage": bag.discount_percentage
                        } for bag in active_bags
                    ]
                })
    
    nearby.sort(key=lambda x: x["distance_km"])
    return {"count": len(nearby), "suppliers": nearby}

class OrderCreate(BaseModel):
    bag_id: int
    lat: float
    lon: float
    address: str

@app.post("/api/orders")
async def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    # Check if bag exists
    bag = db.query(SurpriseBag).filter(
        SurpriseBag.id == order_data.bag_id,
        SurpriseBag.is_active == True,
        SurpriseBag.available_quantity > 0
    ).first()
    
    if not bag:
        raise HTTPException(status_code=404, detail="Bag not available")
    
    # Get or create user with simple method
    user = db.query(User).filter(User.phone == "temp_user").first()
    if not user:
        # Create user without complex hashing for now
        user = User(
            phone="temp_user",
            password="temp_password",  # Change this later
            full_name="Temporary User",
            role="customer",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Check supplier
    supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Create order
    order_number = f"ORD-{secrets.token_hex(4).upper()}"
    
    order = Order(
        user_id=user.id,
        supplier_id=bag.supplier_id,
        surprise_bag_id=bag.id,
        order_number=order_number,
        status=OrderStatus.PENDING,
        customer_lat=order_data.lat,
        customer_lon=order_data.lon,
        customer_address=order_data.address,
        lat=order_data.lat,
        lon=order_data.lon,
        address=order_data.address,
        amount_paid=bag.discounted_price,
        pickup_time=f"{bag.pickup_start_time} - {bag.pickup_end_time}" if bag.pickup_start_time else None,
        created_at=datetime.utcnow()
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Decrease quantity
    bag.available_quantity -= 1
    db.commit()
    
    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status.value,
        "message": "Order created successfully"
    }

class OrderCreate(BaseModel):
    bag_id: int
    lat: float
    lon: float
    address: str

class OrderResponse(BaseModel):
    order_id: int
    status: str
    message: str

@app.post("/api/orders")
async def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    # Check if bag exists and is available
    bag = db.query(SurpriseBag).filter(
        SurpriseBag.id == order_data.bag_id,
        SurpriseBag.is_active == True,
        SurpriseBag.available_quantity > 0
    ).first()
    
    if not bag:
        raise HTTPException(status_code=404, detail="Bag not available")
    
    # Get supplier
    supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get or create a default user (for now, create one if not exists)
    # In production, you'd get the authenticated user
    user = db.query(User).filter(User.phone == "temp_user").first()
    if not user:
        # Create temporary user if none exists
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user = User(
            phone="temp_user",
            password=pwd_context.hash("temp_password"),
            full_name="Temporary User",
            role="customer",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate unique order number
    order_number = f"ORD-{secrets.token_hex(4).upper()}"
    
    # Create order - using fields that exist in your Order model
    order = Order(
        user_id=user.id,
        supplier_id=bag.supplier_id,
        surprise_bag_id=bag.id,
        order_number=order_number,
        status=OrderStatus.PENDING,
        delivery_status="at_supplier",  # Will use DeliveryStatus enum value
        customer_lat=order_data.lat,
        customer_lon=order_data.lon,
        customer_address=order_data.address,
        lat=order_data.lat,  # Also set old fields for compatibility
        lon=order_data.lon,
        address=order_data.address,
        amount_paid=bag.discounted_price,
        pickup_time=f"{bag.pickup_start_time} - {bag.pickup_end_time}" if bag.pickup_start_time else None,
        created_at=datetime.utcnow()
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Decrease available quantity
    bag.available_quantity -= 1
    db.commit()
    
    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status.value,
        "message": "Order created successfully"
    }



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


@app.get("/api/orders/{order_id}")
async def get_order_by_id(order_id: int, db: Session = Depends(get_db)):
    """Get single order by ID"""
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        # Get bag and supplier info
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
        supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        
        return {
            "order_id": order.id,
            "order_number": order.order_number or f"ORD-{order.id}",
            "status": order.status.value if order.status else "pending",
            "delivery_status": order.delivery_status.value if order.delivery_status else "at_supplier",
            "bag_name": bag.name if bag else "Surprise Bag",
            "supplier_name": supplier.business_name if supplier else "Restaurant",
            "supplier_address": supplier.address if supplier else "",
            "customer_address": order.customer_address or "Address not specified",
            "amount_paid": order.amount_paid or 0,
            "pickup_time": order.pickup_time or "",
            "created_at": order.created_at.isoformat() if order.created_at else datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Error fetching order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
@app.get("/admin")
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    foods = db.query(Food).all()
    orders = db.query(Order).all()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "foods": foods,
        "orders": orders
    })

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

# ============ SUPPLIER ROUTES ============
@app.get("/supplier/register")
async def supplier_register_page(request: Request, lang: str = "kz"):
    return templates.TemplateResponse("supplier_register.html", {"request": request, "lang": lang})

@app.post("/supplier/register")
async def supplier_register(
    business_name: str = Form(...),
    business_type: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    city: str = Form(...),
    address: str = Form(...),
    lat: float = Form(...),
    lon: float = Form(...),
    pickup_start: str = Form(...),
    pickup_end: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=email, phone=phone, password=hash_password(password),
        full_name=business_name, role=UserRole.SUPPLIER, is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.flush()
    
    supplier = Supplier(
        user_id=user.id, business_name=business_name, business_type=business_type,
        description=description, city=city, address=address, lat=lat, lon=lon,
        phone=phone, email=email, pickup_start_time=pickup_start,
        pickup_end_time=pickup_end, created_at=datetime.utcnow()
    )
    db.add(supplier)
    db.commit()
    
    response = RedirectResponse(url="/supplier/dashboard", status_code=303)
    response.set_cookie(key="supplier_id", value=str(supplier.id))
    return response

@app.get("/supplier/login")
async def supplier_login_page(request: Request, lang: str = "kz"):
    return templates.TemplateResponse("supplier_login.html", {"request": request, "lang": lang})

@app.post("/supplier/login")
async def supplier_login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email, User.role == UserRole.SUPPLIER).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    supplier = db.query(Supplier).filter(Supplier.user_id == user.id).first()
    response = RedirectResponse(url="/supplier/dashboard", status_code=303)
    response.set_cookie(key="supplier_id", value=str(supplier.id))
    return response
@app.get("/supplier/dashboard")
async def supplier_dashboard(request: Request, db: Session = Depends(get_db)):
    try:
        supplier_id = request.cookies.get("supplier_id")
        
        if not supplier_id:
            return RedirectResponse(url="/supplier/login", status_code=303)
        
        supplier = db.query(Supplier).filter(Supplier.id == int(supplier_id)).first()
        
        if not supplier:
            response = RedirectResponse(url="/supplier/login", status_code=303)
            response.delete_cookie("supplier_id")
            return response
        
        # Get all orders for this supplier
        all_orders = db.query(Order).filter(Order.supplier_id == supplier.id).order_by(Order.created_at.desc()).all()
        
        print(f"📦 Supplier {supplier.business_name} has {len(all_orders)} orders")
        
        # Prepare orders list
        recent_orders_list = []
        for order in all_orders:
            bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
            recent_orders_list.append({
                "id": order.id,
                "order_number": order.order_number or f"ORD-{order.id}",
                "customer_address": order.customer_address or "Мекенжай көрсетілмеген",
                "surprise_bag_name": bag.name if bag else "Тосын сый",
                "amount_paid": order.amount_paid or 0,
                "status": order.status.value if order.status else "pending",
                "created_at": order.created_at
            })
        
        # Statistics
        total_orders = len(all_orders)
        pending_orders = len([o for o in all_orders if o.status == OrderStatus.PENDING])
        today_orders = len([o for o in all_orders if o.created_at and o.created_at.date() == datetime.utcnow().date()])
        total_revenue = sum([o.amount_paid or 0 for o in all_orders])
        
        stats = {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "today_orders": today_orders,
            "total_revenue": total_revenue
        }
        
        # Surprise bags
        surprise_bags = db.query(SurpriseBag).filter(SurpriseBag.supplier_id == supplier.id).all()
        
        lang = request.query_params.get("lang", "ru")
        
        return templates.TemplateResponse("supplier_dashboard.html", {
            "request": request,
            "supplier": supplier,
            "stats": stats,
            "recent_orders": recent_orders_list,
            "all_orders": recent_orders_list,
            "surprise_bags": surprise_bags,
            "monthly_revenue": total_revenue,
            "lang": lang
        })
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return templates.TemplateResponse("supplier_dashboard.html", {
            "request": request,
            "supplier": None,
            "stats": {},
            "recent_orders": [],
            "all_orders": [],
            "surprise_bags": [],
            "monthly_revenue": 0,
            "lang": "ru"
        })
    


@app.get("/api/foods")
async def get_foods(db: Session = Depends(get_db)):
    """Get all foods for dropdown list"""
    try:
        foods = db.query(Food).all()
        result = []
        for food in foods:
            result.append({
                "id": food.id,
                "name_ru": food.name_ru,
                "name_kz": food.name_kz,
                "price": food.price,
                "image": food.image,
                "discount": food.discount
            })
        print(f"📦 Returned {len(result)} foods")
        return result
    except Exception as e:
        print(f"❌ Error getting foods: {e}")
        return []
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
# Найди существующий эндпоинт @app.post("/api/supplier/surprise-bags")
# И измени его, добавив уведомление:

@app.post("/api/supplier/surprise-bags")
async def create_surprise_bag(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    supplier_id = request.cookies.get("supplier_id")
    if not supplier_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get supplier info
    supplier = db.query(Supplier).filter(Supplier.id == int(supplier_id)).first()
    
    bag = SurpriseBag(
        supplier_id=int(supplier_id),
        name=data.get("name"),
        description=data.get("description"),
        original_price=float(data.get("original_price")),
        discounted_price=float(data.get("discounted_price")),
        discount_percentage=int(((float(data.get("original_price")) - float(data.get("discounted_price"))) / float(data.get("original_price"))) * 100),
        image_url=data.get("image_url"),
        available_quantity=int(data.get("available_quantity", 1)),
        pickup_start_time=data.get("pickup_start_time"),
        pickup_end_time=data.get("pickup_end_time"),
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(bag)
    db.commit()
    db.refresh(bag)
    
    # 👇 ОТПРАВЛЯЕМ WEBSOCKET УВЕДОМЛЕНИЕ
    await notify_new_surprise({
        "id": bag.id,
        "name": bag.name,
        "supplier_name": supplier.business_name if supplier else "Sarqyn",
        "discounted_price": bag.discounted_price,
        "original_price": bag.original_price,
        "discount_percentage": bag.discount_percentage,
        "image_url": bag.image_url
    })
    
    return {"success": True, "bag_id": bag.id}






@app.put("/api/supplier/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update order status (for supplier dashboard)"""
    try:
        # Get JSON data
        data = await request.json()
        new_status = data.get("status")
        
        print(f"📝 Received status update: order_id={order_id}, new_status={new_status}")
        
        if not new_status:
            return {"success": False, "error": "Status is required"}
        
        # Find the order
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"success": False, "error": f"Order {order_id} not found"}
        
        print(f"📦 Found order: {order.order_number}, current status: {order.status}")
        
        # Update status
        old_status = order.status.value if order.status else "unknown"
        order.status = OrderStatus(new_status)
        
        # Update delivery status based on order status
        if new_status == "out_for_delivery":
            order.delivery_status = "en_route"
        elif new_status == "nearby":
            order.delivery_status = "nearby"
        elif new_status == "delivered":
            order.delivery_status = "arrived"
            order.delivered_at = datetime.utcnow()
        elif new_status == "confirmed":
            order.confirmed_at = datetime.utcnow()
        elif new_status == "ready_for_pickup":
            order.ready_at = datetime.utcnow()
        
        # Add tracking record
        tracking = OrderTracking(
            order_id=order.id,
            status=order.status,
            delivery_status=order.delivery_status,
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
            "new_status": new_status
        }
        
    except Exception as e:
        print(f"❌ Error updating status: {e}")
        return {"success": False, "error": str(e)}



# Если у тебя есть эндпоинт для обновления сюрприза, добавь туда уведомление:
# Например:

@app.put("/api/supplier/surprise-bags/{bag_id}/toggle")
async def toggle_bag_status(bag_id: int, db: Session = Depends(get_db)):
    bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
    if not bag:
        raise HTTPException(status_code=404, detail="Bag not found")
    
    bag.is_active = not bag.is_active
    db.commit()
    
    # 👇 Если сюрприз скрыли (деактивировали), уведомляем клиентов
    if not bag.is_active:
        await notify_bag_deleted(bag_id)
    else:
        # Если снова активировали, уведомляем о новом (или обновлении)
        supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
        await notify_new_surprise({
            "id": bag.id,
            "name": bag.name,
            "supplier_name": supplier.business_name if supplier else "Sarqyn",
            "discounted_price": bag.discounted_price,
            "original_price": bag.original_price,
            "discount_percentage": bag.discount_percentage,
            "image_url": bag.image_url,
            "is_active": bag.is_active
        })
    
    return {"success": True, "is_active": bag.is_active}


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

@app.get("/api/check-auth")
async def check_auth(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    
    if user_id:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user:
            return {
                "authenticated": True,
                "user_id": user.id,
                "user_name": user.full_name,
                "user_phone": user.phone   # ← ДОЛЖНО БЫТЬ
            }
    return {"authenticated": False}

# ============ RUN APP ============
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)