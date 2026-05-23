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
    Order, OrderStatus, DeliveryStatus, OrderTracking, Review, CourierProfile, AssignedOrder ,TemporaryReservation
)


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








courier_sessions = {}

















# backend/main.py - добавьте WebSocket для курьеров

# backend/main.py - исправленный WebSocket без Depends

@app.websocket("/ws/courier-tracking")
async def courier_tracking_websocket(websocket: WebSocket):
    """WebSocket для отслеживания курьеров в реальном времени"""
    
    # Принимаем соединение
    await websocket.accept()
    
    # Получаем ID пользователя из cookies (не через Depends)
    cookies = websocket.cookies
    user_id = cookies.get("user_id")
    
    print(f"🔌 WebSocket connection attempt, user_id from cookie: {user_id}")
    
    if not user_id:
        print("❌ WebSocket: нет user_id в cookies")
        await websocket.close(code=1008, reason="Not authenticated")
        return
    
    # Создаем сессию БД вручную
    db = SessionLocal()
    
    try:
        # Проверяем, что пользователь - курьер
        user = db.query(User).filter(User.id == int(user_id)).first()
        
        if not user:
            print(f"❌ WebSocket: пользователь {user_id} не найден")
            await websocket.close(code=1008, reason="User not found")
            return
        
        courier = db.query(CourierProfile).filter(CourierProfile.user_id == user.id).first()
        
        if not courier:
            print(f"❌ WebSocket: курьер для user_id {user_id} не найден")
            await websocket.close(code=1008, reason="Courier not found")
            return
        
        courier_id = courier.id
        print(f"✅ WebSocket подключен для курьера {courier_id} ({user.first_name} {user.last_name})")
        
        # Добавляем в список активных соединений
        if courier_id not in courier_connections:
            courier_connections[courier_id] = []
        courier_connections[courier_id].append(websocket)
        
        # Отправляем приветственное сообщение
        await websocket.send_json({
            "type": "connected",
            "message": f"Connected to courier tracking as {courier.first_name}",
            "courier_id": courier_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Держим соединение открытым
        while True:
            try:
                data = await websocket.receive_text()
                print(f"📨 Получено от курьера {courier_id}: {data}")
                
                try:
                    message = json.loads(data)
                    msg_type = message.get("type")
                    
                    if msg_type == "ping":
                        await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                        print("💓 Heartbeat pong sent")
                        
                    elif msg_type == "update_location":
                        # Обновляем позицию курьера в БД
                        lat = message.get("lat")
                        lon = message.get("lon")
                        if lat and lon:
                            courier.current_lat = lat
                            courier.current_lon = lon
                            courier.last_location_update = datetime.utcnow()
                            db.commit()
                            print(f"📍 Позиция курьера {courier_id} обновлена: {lat}, {lon}")
                            
                            # Транслируем всем клиентам
                            await manager.broadcast({
                                "type": "courier_location",
                                "courier_id": courier_id,
                                "first_name": courier.first_name,
                                "last_name": courier.last_name,
                                "lat": lat,
                                "lon": lon,
                                "status": courier.current_order_status or "online",
                                "timestamp": datetime.utcnow().isoformat()
                            }, channel="surprise_bags")
                            
                except json.JSONDecodeError:
                    print(f"❌ Неверный JSON: {data}")
                    
            except WebSocketDisconnect:
                print(f"🔌 WebSocket отключен для курьера {courier_id}")
                break
            except Exception as e:
                print(f"❌ Ошибка обработки сообщения: {e}")
                break
                
    except Exception as e:
        print(f"❌ WebSocket ошибка: {e}")
    finally:
        # Удаляем соединение
        if courier_id in courier_connections:
            if websocket in courier_connections[courier_id]:
                courier_connections[courier_id].remove(websocket)
            if not courier_connections[courier_id]:
                del courier_connections[courier_id]
        
        db.close()
        print(f"🔌 WebSocket закрыт для курьера {courier_id if 'courier_id' in locals() else 'unknown'}")

# Глобальный словарь для WebSocket соединений курьеров
courier_connections = {}


# ============ ДОБАВЬТЕ ЭТОТ ЭНДПОИНТ ============

@app.get("/api/courier/available-orders")
async def get_available_orders_for_courier(request: Request, db: Session = Depends(get_db)):
    """Получить список доступных заказов для курьера"""
    
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Проверяем, что пользователь - курьер
    courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
    
    if not courier:
        raise HTTPException(status_code=403, detail="Not a courier")
    
    # Получаем текущую позицию курьера
    courier_lat = courier.current_lat
    courier_lon = courier.current_lon
    
    if not courier_lat or not courier_lon:
        # Если нет позиции, возвращаем пустой список
        return {"success": True, "orders": [], "message": "Позиция не определена"}
    
    # Ищем заказы со статусом PENDING и CONFIRMED
    available_orders = db.query(Order).filter(
        Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED]),
        Order.assigned_courier_id == None
    ).all()
    
    available_orders_list = []
    
    for order in available_orders:
        supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        
        if supplier and supplier.lat and supplier.lon:
            # Рассчитываем расстояние до ресторана
            distance = haversine_distance(
                courier_lat, courier_lon,
                supplier.lat, supplier.lon
            )
            
            # Показываем заказы в радиусе 10 км
            if distance <= 10.0:
                bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
                
                available_orders_list.append({
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "supplier_name": supplier.business_name,
                    "supplier_address": supplier.address,
                    "distance_km": round(distance, 2),
                    "estimated_time_minutes": int((distance / courier.speed_kmh) * 60),
                    "amount": order.amount_paid or 0,
                    "bag_name": bag.name if bag else "Surprise Bag",
                    "customer_address": order.customer_address
                })
    
    # Сортируем по расстоянию
    available_orders_list.sort(key=lambda x: x["distance_km"])
    
    return {
        "success": True,
        "orders": available_orders_list[:10],  # Максимум 10 заказов
        "count": len(available_orders_list)
    }


# backend/main.py - обновите эндпоинт

# backend/main.py - обновите эндпоинт

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

@app.post("/api/courier/respond-to-proposal")
async def respond_to_proposal(request: Request, db: Session = Depends(get_db)):
    """Курьер отвечает на предложение заказа"""
    
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    response = data.get("response")  # "accept" или "decline"
    
    courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
    
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    if not courier.proposed_order_id:
        return {"success": False, "message": "Нет предложенных заказов"}
    
    # Проверяем, не истекло ли предложение
    if courier.proposed_order_expires_at and courier.proposed_order_expires_at < datetime.utcnow():
        courier.proposed_order_id = None
        db.commit()
        return {"success": False, "message": "Предложение истекло"}
    
    if response == "accept":
        order = db.query(Order).filter(Order.id == courier.proposed_order_id).first()
        if order and order.status == OrderStatus.PENDING:
            order.assigned_courier_id = courier.user_id
            order.status = OrderStatus.CONFIRMED
            
            if courier.current_order_id:
                # Ставим в очередь
                message = "Заказ добавлен в очередь"
            else:
                courier.current_order_id = courier.proposed_order_id
                courier.current_order_status = "assigned"
                courier.is_available = False
                message = "Заказ назначен!"
            
            courier.proposed_order_id = None
            db.commit()
            
            # Уведомляем через WebSocket
            await manager.broadcast({
                "type": "order_assigned",
                "order_id": order.id,
                "courier_id": courier.id
            }, channel="orders")
            
            return {"success": True, "message": message, "order_id": order.id}
    
    else:  # decline
        courier.proposed_order_id = None
        db.commit()
        return {"success": True, "message": "Предложение отклонено"}
    
    return {"success": False, "message": "Ошибка"}


@app.post("/api/courier/accept-order/{order_id}")
async def courier_accept_order(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Курьер принимает заказ из списка"""
    
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
    
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
        raise HTTPException(status_code=400, detail="Заказ уже назначен")
    
    if courier.current_order_id:
        raise HTTPException(status_code=400, detail="У вас уже есть активный заказ")
    
    # Назначаем заказ
    order.assigned_courier_id = courier.user_id
    order.status = OrderStatus.CONFIRMED
    courier.current_order_id = order_id
    courier.current_order_status = "assigned"
    courier.is_available = False
    
    db.commit()
    
    return {"success": True, "message": "Заказ принят", "order_id": order_id}












# backend/main.py - добавьте

@app.get("/api/cart/reservation")
async def get_active_reservation(request: Request, db: Session = Depends(get_db)):
    """Получить активную резервацию для текущего пользователя"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        return {"reservation": None}
    
    reservation = db.query(TemporaryReservation).filter(
        TemporaryReservation.user_id == int(user_id),
        TemporaryReservation.is_paid == False,
        TemporaryReservation.expires_at > datetime.utcnow()
    ).first()
    
    if reservation:
        return {
            "reservation": {
                "id": reservation.id,
                "expires_at": reservation.expires_at.isoformat(),
                "bag_id": reservation.bag_id
            }
        }
    
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








# backend/main.py - добавьте в конец файла

# ============ COURIER ENDPOINTS ============

# backend/main.py - убедитесь что эндпоинт выглядит так:

# backend/main.py - исправленный эндпоинт

@app.post("/courier/register")
async def courier_register(request: Request, db: Session = Depends(get_db)):
    """Регистрация курьера"""
    data = await request.json()
    
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    phone = format_phone_number(data.get("phone"))
    password = data.get("password")
    courier_type = data.get("courier_type", "pedestrian")
    car_model = data.get("car_model", "")
    car_number = data.get("car_number", "")
    
    if not first_name or not last_name or not phone or not password:
        raise HTTPException(status_code=400, detail="Все поля обязательны")
    
    existing = db.query(User).filter(User.phone == phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким номером уже существует")
    
    speed = 5.0 if courier_type == "pedestrian" else 40.0
    radius = 3.0 if courier_type == "pedestrian" else 15.0
    
    hashed_password = hash_password(password)
    full_name = f"{first_name} {last_name}"
    
    # ✅ ИСПРАВЛЕНО: используем правильные имена полей
    new_user = User(
        phone=phone,
        first_name=first_name,   # ✅ теперь есть в модели
        last_name=last_name,      # ✅ теперь есть в модели
        full_name=full_name,
        password=hashed_password,
        role=UserRole.COURIER,
        is_active=False,
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.flush()
    
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
        created_at=datetime.utcnow()
    )
    db.add(courier_profile)
    db.commit()
    
    return {
        "success": True,
        "message": "Заявка отправлена на рассмотрение",
        "courier_id": new_user.id
    }
@app.post("/api/courier/go-online")
async def courier_go_online(request: Request, db: Session = Depends(get_db)):
    """Курьер выходит на линию"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    lat = data.get("lat")
    lon = data.get("lon")
    
    courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    if not courier.is_verified:
        raise HTTPException(status_code=403, detail="Курьер не верифицирован")
    
    courier.is_online = True
    courier.is_available = True
    courier.last_online_at = datetime.utcnow()
    
    if lat and lon:
        courier.current_lat = lat
        courier.current_lon = lon
        courier.last_location_update = datetime.utcnow()
    
    db.commit()
    
    return {"success": True, "message": "Вы на линии", "is_online": True}


@app.post("/api/courier/go-offline")
async def courier_go_offline(request: Request, db: Session = Depends(get_db)):
    """Курьер уходит с линии"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    if courier.current_order_id:
        raise HTTPException(status_code=400, detail="У вас есть активный заказ")
    
    courier.is_online = False
    courier.is_available = False
    courier.last_offline_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "Вы офлайн", "is_online": False}


@app.post("/api/courier/update-location")
async def update_courier_location(request: Request, db: Session = Depends(get_db)):
    """Обновление геолокации курьера (автоматически каждые 3 секунды)"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    lat = data.get("lat")
    lon = data.get("lon")
    
    courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    courier.current_lat = lat
    courier.current_lon = lon
    courier.last_location_update = datetime.utcnow()
    
    # Автоматическое определение "почти закончил" (менее 500м до клиента)
    if courier.current_order_id:
        order = db.query(Order).filter(Order.id == courier.current_order_id).first()
        if order and order.customer_lat:
            from math import radians, sin, cos, sqrt, atan2
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371
                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                return R * c
            
            distance_km = haversine(lat, lon, order.customer_lat, order.customer_lon)
            if distance_km <= 0.5 and courier.current_order_status != "almost_done":
                courier.current_order_status = "almost_done"
    
    db.commit()
    
    return {"success": True, "status": courier.current_order_status}


@app.get("/api/courier/status")
async def get_courier_status(request: Request, db: Session = Depends(get_db)):
    """Получить статус курьера"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
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
        "last_name": courier.last_name
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


@app.post("/api/courier/complete-order/{order_id}")
async def courier_complete_order(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Курьер завершил доставку"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    courier = db.query(CourierProfile).filter(CourierProfile.user_id == int(user_id)).first()
    if not courier:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = OrderStatus.DELIVERED
    order.delivered_at = datetime.utcnow()
    
    courier.current_order_id = None
    courier.current_order_status = None
    courier.is_available = True
    courier.total_deliveries += 1
    courier.completed_orders_today += 1
    courier.last_order_completed_at = datetime.utcnow()
    
    db.commit()
    
    return {"success": True, "message": "Заказ доставлен"}






# backend/main.py - добавьте логин для курьера
# backend/main.py - убедитесь что эндпоинт возвращает success
# backend/main.py - убедитесь что эндпоинт возвращает success
# backend/main.py - исправьте эндпоинт логина курьера

# backend/main.py - исправленный эндпоинт

@app.post("/api/courier/login")
async def courier_login(request: Request, db: Session = Depends(get_db)):
    """Логин для курьеров"""
    data = await request.json()
    phone = format_phone_number(data.get("phone"))
    password = data.get("password")
    
    print(f"🔐 Попытка входа курьера: {phone}")
    
    # Ищем пользователя
    user = db.query(User).filter(
        User.phone == phone,
        User.role == UserRole.COURIER
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Неверный телефон или пароль")
    
    if not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Неверный телефон или пароль")
    
    courier = db.query(CourierProfile).filter(CourierProfile.user_id == user.id).first()
    
    if not courier or not courier.is_verified:
        raise HTTPException(status_code=403, detail="Аккаунт не подтвержден")
    
    # ✅ СОЗДАЕМ ОТВЕТ С ПРАВИЛЬНЫМИ КУКАМИ
    response = JSONResponse({
        "success": True,
        "message": "Вход выполнен",
        "courier": {
            "id": courier.id,
            "first_name": courier.first_name,
            "last_name": courier.last_name,
            "phone": user.phone,
            "is_verified": courier.is_verified
        }
    })
    
    # ✅ Устанавливаем cookie с правильными параметрами
    response.set_cookie(
        key="user_id",
        value=str(user.id),
        httponly=True,
        samesite="none",  # ← ВАЖНО для cross-domain
        secure=True,       # ← ВАЖНО для HTTPS
        max_age=60*60*24*30,
        path="/"
    )
    
    response.set_cookie(
        key="courier_id",
        value=str(courier.id),
        httponly=True,
        samesite="none",
        secure=True,
        max_age=60*60*24*30,
        path="/"
    )
    
    return response
# main.py - регистрация с выбором типа


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
    

# main.py - обновление геолокации курьера


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


@app.post("/api/supplier/auto-assign-courier/{order_id}")
async def auto_assign_courier(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Автоматически назначает лучшего курьера на заказ"""
    supplier_id = request.cookies.get("supplier_id")
    if not supplier_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.supplier_id == int(supplier_id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != OrderStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Order not confirmed yet")
    
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
    
    # Обновляем статус заказа
    order.status = OrderStatus.OUT_FOR_DELIVERY
    order.delivery_started_at = datetime.utcnow()
    order.delivery_deadline = datetime.utcnow() + timedelta(minutes=30)
    order.assigned_courier_id = best_courier.user_id
    
    # Увеличиваем счетчик доставок курьера
    best_courier.total_deliveries = (best_courier.total_deliveries or 0) + 1
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Курьер {courier_user.full_name} автоматически назначен",
        "courier": {
            "id": best_courier.id,
            "name": courier_user.full_name,
            "phone": courier_user.phone,
            "car_model": best_courier.car_model,
            "car_number": best_courier.car_number,
            "rating": best_courier.rating
        }
    }


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


@app.post("/api/supplier/assign-courier")
async def assign_courier_to_order(request: Request, db: Session = Depends(get_db)):
    """Ручное назначение курьера на заказ"""
    supplier_id = request.cookies.get("supplier_id")
    if not supplier_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    order_id = data.get("order_id")
    courier_profile_id = data.get("courier_profile_id")
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.supplier_id == int(supplier_id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != OrderStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Order not confirmed yet")
    
    courier_profile = db.query(CourierProfile).filter(
        CourierProfile.id == courier_profile_id,
        CourierProfile.supplier_id == int(supplier_id)
    ).first()
    
    if not courier_profile:
        raise HTTPException(status_code=404, detail="Courier not found")
    
    user = db.query(User).filter(User.id == courier_profile.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Courier not active")
    
    # Создаем назначение
    assignment = AssignedOrder(
        order_id=order_id,
        courier_id=courier_profile.user_id,
        status="assigned",
        assigned_at=datetime.utcnow()
    )
    db.add(assignment)
    
    # Обновляем статус заказа
    order.status = OrderStatus.OUT_FOR_DELIVERY
    order.delivery_started_at = datetime.utcnow()
    order.delivery_deadline = datetime.utcnow() + timedelta(minutes=30)
    order.assigned_courier_id = courier_profile.user_id
    
    # Увеличиваем счетчик доставок курьера
    courier_profile.total_deliveries = (courier_profile.total_deliveries or 0) + 1
    
    db.commit()
    
    return {
        "success": True, 
        "message": f"Курьер {user.full_name} назначен на заказ {order.order_number}",
        "courier": {
            "name": user.full_name,
            "phone": user.phone
        }
    }


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
@app.post("/admin/api/order/{order_id}/confirm-payment")
async def admin_confirm_payment(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ подтверждает оплату и запускает доставку"""
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.payment_status != "paid":
        raise HTTPException(status_code=400, detail="Order not paid yet")
    
    # Подтверждаем и запускаем доставку
    now = datetime.utcnow()
    order.status = OrderStatus.CONFIRMED
    order.delivery_started_at = now
    order.delivery_deadline = now + timedelta(minutes=30)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Payment confirmed, delivery started",
        "delivery_deadline": order.delivery_deadline.isoformat()
    }


# ============ КЛИЕНТ: ПОЛУЧИЛ ЗАКАЗ ============
@app.post("/api/order/{order_id}/receive")
async def customer_receive_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Клиент подтверждает, что получил заказ → статус меняется на DELIVERED"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == int(user_id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Проверяем, что заказ в доставке
    if order.status != OrderStatus.OUT_FOR_DELIVERY:
        raise HTTPException(status_code=400, detail="Order is not in delivery")
    
    # Проверяем, не истек ли дедлайн
    if order.delivery_deadline and datetime.utcnow() > order.delivery_deadline:
        raise HTTPException(status_code=400, detail="Delivery deadline expired. Auto-refund initiated.")
    
    # Автоматически завершаем заказ
    order.status = OrderStatus.DELIVERED
    order.delivery_status = DeliveryStatus.ARRIVED
    order.delivered_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": "Order received successfully"}


# ============ КЛИЕНТ: ОТКАЗ ОТ ЗАКАЗА ============
@app.post("/api/order/{order_id}/reject")
async def customer_reject_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Клиент отказывается от заказа → отправляет запрос админу на возврат"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    reason = data.get("reason", "Не указана")
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == int(user_id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Проверяем, что заказ в доставке
    if order.status != OrderStatus.OUT_FOR_DELIVERY:
        raise HTTPException(status_code=400, detail="Cannot reject order at this stage")
    
    # Создаем запрос на возврат
    order.refund_requested_by_customer = True
    order.refund_requested_at = datetime.utcnow()
    order.refund_reason = reason
    order.refund_status = "requested"
    
    db.commit()
    
    return {
        "success": True,
        "message": "Refund requested. Admin will process.",
        "refund_request_id": order.id
    }


# ============ АДМИН: ПОДТВЕРДИТЬ ВОЗВРАТ ============
@app.post("/admin/api/order/{order_id}/approve-refund")
async def admin_approve_refund(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ подтверждает возврат денег (деньги отправлены клиенту)"""
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.refund_status != "requested":
        raise HTTPException(status_code=400, detail="No refund request found")
    
    # Выполняем возврат (имитация)
    order.refund_status = "completed"
    order.refund_processed_at = datetime.utcnow()
    order.refund_amount = order.amount_paid
    order.payment_status = "refunded"
    order.status = OrderStatus.CANCELLED
    order.refund_transaction_id = f"REF-{secrets.token_hex(8).upper()}"
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Refund approved for order {order.order_number}",
        "refund_amount": order.refund_amount
    }


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
async def auto_refund_on_deadline():
    """Каждую минуту проверяем: если 30 минут истекли и клиент не подтвердил получение → авто-возврат"""
    while True:
        try:
            await asyncio.sleep(60)  # Каждую минуту
            
            db = SessionLocal()
            now = datetime.utcnow()
            
            # Заказы в доставке, у которых дедлайн истек
            expired_orders = db.query(Order).filter(
                Order.status == OrderStatus.OUT_FOR_DELIVERY,
                Order.delivery_deadline <= now,
                Order.auto_refund_processed == False
            ).all()
            
            for order in expired_orders:
                print(f"⏰ АВТО-ВОЗВРАТ: Заказ {order.order_number} не получен за 30 минут")
                
                order.auto_refund_processed = True
                order.refund_status = "completed"
                order.refund_processed_at = now
                order.refund_amount = order.amount_paid
                order.payment_status = "refunded"
                order.status = OrderStatus.CANCELLED
                order.refund_transaction_id = f"AUTO-REF-{secrets.token_hex(8).upper()}"
                order.refund_reason = "Автоматический возврат: заказ не получен в течение 30 минут"
                
                db.commit()
                
                # Уведомление через WebSocket
                await manager.broadcast({
                    "type": "auto_refund",
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "amount": order.amount_paid,
                    "message": "Заказ не получен вовремя. Деньги возвращены."
                })
            
            db.close()
            
        except Exception as e:
            print(f"❌ Ошибка auto_refund: {e}")

# backend/main.py - добавьте фоновую задачу

import asyncio
from datetime import datetime, timedelta

async def cleanup_expired_reservations():
    """Фоновая задача: каждую минуту проверяет истекшие резервации"""
    while True:
        await asyncio.sleep(60)  # Каждую минуту
        
        db = SessionLocal()
        try:
            # Находим истекшие резервации (не оплачены и срок истек)
            expired = db.query(TemporaryReservation).filter(
                TemporaryReservation.is_paid == False,
                TemporaryReservation.expires_at < datetime.utcnow()
            ).all()
            
            for reservation in expired:
                # Возвращаем количество обратно в сюрприз
                bag = db.query(SurpriseBag).filter(SurpriseBag.id == reservation.bag_id).first()
                if bag:
                    bag.available_quantity += reservation.quantity
                    if bag.available_quantity > 0:
                        bag.is_active = True
                    
                    print(f"🔄 Возврат: сюрприз {bag.name}, +{reservation.quantity}, теперь {bag.available_quantity}")
                    
                    # Отправляем WebSocket уведомление
                    await manager.broadcast({
                        "type": "bag_quantity_updated",
                        "data": {
                            "bag_id": bag.id,
                            "available_quantity": bag.available_quantity,
                            "is_active": bag.is_active
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    }, channel="surprise_bags")
                
                # Удаляем резервацию из корзины пользователя
                cart_item = db.query(CartItem).filter(
                    CartItem.user_id == reservation.user_id,
                    CartItem.surprise_bag_id == reservation.bag_id
                ).first()
                if cart_item:
                    if cart_item.quantity > reservation.quantity:
                        cart_item.quantity -= reservation.quantity
                    else:
                        db.delete(cart_item)
                
                db.delete(reservation)
            
            if expired:
                db.commit()
                print(f"🧹 Очищено {len(expired)} истекших резерваций")
                
        except Exception as e:
            print(f"Ошибка очистки резерваций: {e}")
        finally:
            db.close()
# backend/main.py - при успешной оплате

@app.post("/api/payment/confirm-reservation")
async def confirm_reservation(request: Request, db: Session = Depends(get_db)):
    """Подтверждение резервации после успешной оплаты"""
    data = await request.json()
    reservation_id = data.get("reservation_id")
    
    reservation = db.query(TemporaryReservation).filter(
        TemporaryReservation.id == reservation_id
    ).first()
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Резервация не найдена")
    
    # Помечаем как оплаченную
    reservation.is_paid = True
    
    # Создаем заказ
    bag = db.query(SurpriseBag).filter(SurpriseBag.id == reservation.bag_id).first()
    
    order = Order(
        user_id=reservation.user_id,
        supplier_id=bag.supplier_id,
        surprise_bag_id=bag.id,
        order_number=f"ORD-{secrets.token_hex(4).upper()}",
        status=OrderStatus.CONFIRMED,
        amount_paid=bag.discounted_price * reservation.quantity,
        created_at=datetime.utcnow()
    )
    db.add(order)
    db.commit()
    
    # Удаляем из корзины
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == reservation.user_id,
        CartItem.surprise_bag_id == reservation.bag_id
    ).first()
    if cart_item:
        db.delete(cart_item)
    
    db.commit()
    
    return {"success": True, "message": "Оплата подтверждена", "order_id": order.id}
# Запускаем фоновую задачу при старте приложения
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_expired_reservations())
    print("✅ Фоновая задача очистки резерваций запущена")
# Клиент запрашивает возврат
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
@app.post("/admin/api/refund/approve/{order_id}")
async def admin_approve_refund(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.refund_status not in ["requested", "processing"]:
        raise HTTPException(status_code=400, detail="Refund not requested or already processed")
    
    # ========== ИМИТАЦИЯ ВОЗВРАТА ДЕНЕГ ==========
    # В реальном проекте здесь будет вызов API банка
    # await bank_api.refund(order.payment_id, order.amount_paid)
    
    # Обновляем статус заказа
    order.refund_status = "completed"
    order.refund_processed_at = datetime.utcnow()
    order.refund_amount = order.amount_paid
    order.payment_status = "refunded"
    order.status = OrderStatus.CANCELLED
    
    # Генерируем ID транзакции возврата
    order.refund_transaction_id = f"REF-{secrets.token_hex(8).upper()}"
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Refund approved for order {order.order_number}",
        "refund_amount": order.refund_amount,
        "refund_transaction_id": order.refund_transaction_id
    }

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

def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed

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
@app.get("/admin/login")
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    admin = db.query(Admin).filter(Admin.username == username).first()
    
    if not admin or not verify_password(password, admin.password_hash):
        return templates.TemplateResponse(
            "admin_login.html",
            {"request": request, "error": "Неверный логин или пароль"}
        )
    
    token = secrets.token_urlsafe(32)
    admin_sessions[token] = {
        "admin_id": admin.id,
        "username": admin.username,
        "expires_at": datetime.utcnow() + timedelta(hours=8)
    }
    
    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    response.set_cookie(key="admin_token", value=token, httponly=True, max_age=8*60*60)
    return response

@app.get("/admin/logout")
async def admin_logout(request: Request):
    token = request.cookies.get("admin_token")
    if token in admin_sessions:
        del admin_sessions[token]
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_token")
    return response

# ============ АДМИН-ДАШБОРД ============
@app.get("/admin/dashboard")
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    # Статистика
    total_orders = db.query(Order).count()
    paid_orders = db.query(Order).filter(Order.payment_status == "paid").count()
    pending_payment = db.query(Order).filter(Order.payment_status == "pending").count()
    total_revenue = db.query(func.sum(Order.amount_paid)).filter(Order.payment_status == "paid").scalar() or 0
    
    # Заказы
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    orders_data = []
    for order in orders:
        user = db.query(User).filter(User.id == order.user_id).first()
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
        orders_data.append({
            "id": order.id,
            "order_number": order.order_number or f"ORD-{order.id}",
            "user_name": user.full_name if user else "Неизвестно",
            "user_phone": user.phone if user else "—",
            "amount": order.amount_paid or 0,
            "payment_status": order.payment_status or "pending",
            "order_status": order.status.value if order.status else "pending",
            "bag_name": bag.name if bag else "Surprise Bag",
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else "—",
        })
    
    stats = {
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "pending_payment": pending_payment,
        "total_revenue": total_revenue
    }
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "stats": stats,
        "orders": orders_data,
        "admin": admin
    })

# ============ API ДЛЯ ОБНОВЛЕНИЯ ============
@app.post("/admin/api/order/{order_id}/payment-status")
async def admin_update_payment_status(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = await request.json()
    new_status = data.get("payment_status")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.payment_status = new_status
    if new_status == "paid" and not order.paid_at:
        order.paid_at = datetime.utcnow()
        order.status = OrderStatus.CONFIRMED
    
    db.commit()
    return {"success": True}

@app.post("/admin/api/order/{order_id}/status")
async def admin_update_order_status(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Админ меняет статус заказа (с проверками и триггерами)"""
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = await request.json()
    new_status = data.get("status")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    old_status = order.status.value if order.status else "unknown"
    
    # ============ ЛОГИКА ПРИ СМЕНЕ СТАТУСА ============
    
    if new_status == "confirmed":
        # Админ подтверждает оплату (но доставка еще не начата)
        order.confirmed_at = datetime.utcnow()
        
    elif new_status == "out_for_delivery":
        # Админ запускает доставку → устанавливаем дедлайн 30 минут
        if order.payment_status != "paid":
            raise HTTPException(status_code=400, detail="Cannot start delivery: order not paid")
        if order.status != OrderStatus.CONFIRMED:
            raise HTTPException(status_code=400, detail="Cannot start delivery: order not confirmed")
        
        now = datetime.utcnow()
        order.delivery_started_at = now
        order.delivery_deadline = now + timedelta(minutes=30)
        order.delivery_status = DeliveryStatus.EN_ROUTE
        
    elif new_status == "delivered":
        # Админ вручную отмечает доставку (если клиент не нажал кнопку)
        order.delivered_at = datetime.utcnow()
        order.delivery_status = DeliveryStatus.ARRIVED
        
    elif new_status == "cancelled":
        # Админ отменяет заказ (если есть основания)
        if order.payment_status == "paid":
            # Если оплачен, нужно вернуть деньги
            order.refund_status = "completed"
            order.refund_processed_at = datetime.utcnow()
            order.refund_amount = order.amount_paid
            order.payment_status = "refunded"
            order.refund_reason = f"Отменено администратором. Причина: {data.get('reason', 'Не указана')}"
            order.refund_transaction_id = f"ADMIN-REF-{secrets.token_hex(8).upper()}"
    
    # Обновляем статус
    order.status = OrderStatus(new_status)
    db.commit()
    
    return {
        "success": True,
        "message": f"Статус заказа {order.order_number} изменен с {old_status} на {new_status}",
        "delivery_deadline": order.delivery_deadline.isoformat() if order.delivery_deadline else None
    }

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

@app.post("/api/bookings/create")
async def create_booking(
    request: Request,
    booking_data: BookingRequest,
    db: Session = Depends(get_db)
):
    """Забронировать сюрприз-пакет на 15 минут"""
    
    # Get user from cookie
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if bag exists and is available
    bag = db.query(SurpriseBag).filter(
        SurpriseBag.id == booking_data.bag_id,
        SurpriseBag.is_active == True,
        SurpriseBag.available_quantity > 0
    ).first()
    
    if not bag:
        return {
            "success": False,
            "message": "Пакет недоступен"
        }
    
    # Check if there's an active booking (pending order less than 15 min old)
    existing_booking = db.query(Order).filter(
        Order.surprise_bag_id == booking_data.bag_id,
        Order.status == OrderStatus.PENDING,
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
    
    order = Order(
        user_id=int(user_id),
        supplier_id=bag.supplier_id,
        surprise_bag_id=bag.id,
        order_number=order_number,
        status=OrderStatus.PENDING,
        payment_status="pending",
        amount_paid=bag.discounted_price,
        created_at=datetime.utcnow()
    )
    
    db.add(order)
    
    # Decrease available quantity
    bag.available_quantity -= 1
    
    db.commit()
    db.refresh(order)
    
    return {
        "success": True,
        "expires_at": expires_at.isoformat(),
        "remaining_seconds": 15 * 60,
        "message": f"Пакет '{bag.name}' забронирован на 15 минут",
        "order_id": order.id
    }


@app.get("/api/bookings/check/{bag_id}")
async def check_booking(
    bag_id: int,
    db: Session = Depends(get_db)
):
    """Проверить статус бронирования"""
    
    booking = db.query(Order).filter(
        Order.surprise_bag_id == bag_id,
        Order.status == OrderStatus.PENDING,
        Order.payment_status == "pending",
        Order.created_at > datetime.utcnow() - timedelta(minutes=15)
    ).first()
    
    if not booking:
        return {
            "is_booked": False,
            "remaining_seconds": 0
        }
    
    expires_at = booking.created_at + timedelta(minutes=15)
    remaining = int((expires_at - datetime.utcnow()).total_seconds())
    
    return {
        "is_booked": True,
        "remaining_seconds": max(0, remaining),
        "expires_at": expires_at.isoformat(),
        "order_id": booking.id
    }


@app.delete("/api/bookings/release/{bag_id}")
async def release_booking(
    bag_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Освободить бронь (если пользователь отменил)"""
    
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find active booking
    booking = db.query(Order).filter(
        Order.surprise_bag_id == bag_id,
        Order.user_id == int(user_id),
        Order.status == OrderStatus.PENDING,
        Order.payment_status == "pending"
    ).first()
    
    if booking:
        # Return quantity to bag
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
        if bag:
            bag.available_quantity += 1
        
        booking.status = OrderStatus.CANCELLED
        db.commit()
        
        return {"success": True, "message": "Бронирование отменено"}
    
    return {"success": False, "message": "Бронь не найдена"}


# Обновите эндпоинт получения сюрприз-пакетов, чтобы исключить забронированные
# backend/main.py - обновите эндпоинт получения сюрпризов

@app.get("/api/surprise-bags")
async def get_all_surprise_bags(db: Session = Depends(get_db)):
    """Получить только доступные сюрпризы (is_active=True И available_quantity > 0)"""
    bags = db.query(SurpriseBag).filter(
        SurpriseBag.is_active == True,
        SurpriseBag.available_quantity > 0  # ← ТОЛЬКО ЕСЛИ ЕСТЬ В НАЛИЧИИ
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
                "is_active": bag.is_active
            })
    
    return result


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

@app.post("/api/payment/initiate")
async def initiate_payment(request: Request, payment_data: PaymentRequest, db: Session = Depends(get_db)):
    """
    Initiate payment - IMITATION MODE
    When real APIs are available, switch PAYMENT_CONFIG["mode"] to "production"
    """
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify order exists and belongs to user
    order = db.query(Order).filter(
        Order.id == payment_data.order_id,
        Order.user_id == int(user_id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if order is already paid
    if order.payment_status == "paid":
        return PaymentResponse(
            success=True,
            payment_id=order.payment_id or f"PAY-{uuid.uuid4().hex[:12].upper()}",
            transaction_id=order.transaction_id or f"TXN-{uuid.uuid4().hex[:16].upper()}",
            amount=payment_data.amount,
            status="completed",
            message="Order already paid",
            payment_method=payment_data.payment_method.value,
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    
    # Generate unique IDs
    payment_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
    transaction_id = f"TXN-{uuid.uuid4().hex[:16].upper()}"
    
    # Simulate payment processing delay
    await asyncio.sleep(1.5)
    
    # DEMO MODE: Simulate payment result
    if PAYMENT_CONFIG["mode"] == "demo":
        # 95% success rate for realistic testing
        is_successful = random.random() < PAYMENT_CONFIG["demo_success_rate"]
        
        if is_successful:
            # Update order with payment info
            order.payment_id = payment_id
            order.transaction_id = transaction_id
            order.payment_status = "paid"
            order.payment_method = payment_data.payment_method.value
            order.paid_at = datetime.utcnow()
            order.payment_amount = payment_data.amount
            order.status = OrderStatus.CONFIRMED  # Auto-confirm after payment
            order.confirmed_at = datetime.utcnow()
            db.commit()
            
            # Create tracking record
            tracking = OrderTracking(
                order_id=order.id,
                status=order.status,
                delivery_status=order.delivery_status,
                message=f"✅ Payment completed via {payment_data.payment_method.value} (Demo Mode)",
                created_at=datetime.utcnow()
            )
            db.add(tracking)
            db.commit()
            
            # Store transaction for reference
            payment_transactions[payment_id] = {
                "order_id": order.id,
                "order_number": order.order_number,
                "amount": payment_data.amount,
                "payment_method": payment_data.payment_method.value,
                "card_last4": payment_data.card_number[-4:] if payment_data.card_number else "0000",
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = PaymentResponse(
                success=True,
                payment_id=payment_id,
                transaction_id=transaction_id,
                amount=payment_data.amount,
                status="completed",
                message=f"✅ Payment successful via {payment_data.payment_method.value}",
                payment_method=payment_data.payment_method.value,
                timestamp=datetime.utcnow().isoformat()
            )
        else:
            # Simulate payment failure
            result = PaymentResponse(
                success=False,
                payment_id=payment_id,
                transaction_id=transaction_id,
                amount=payment_data.amount,
                status="failed",
                message="❌ Payment failed. Insufficient funds or card declined. Please try another card.",
                payment_method=payment_data.payment_method.value,
                timestamp=datetime.utcnow().isoformat()
            )
        
        return result.dict()
    
    # PRODUCTION MODE: Real API integration
    else:
        # This will be implemented when you get real API keys
        if payment_data.payment_method == PaymentMethod.KASPI and PAYMENT_CONFIG["kaspi"]["enabled"]:
            return await process_real_kaspi_payment(order, payment_data, payment_id, transaction_id, db)
        elif payment_data.payment_method == PaymentMethod.HALYK and PAYMENT_CONFIG["halyk"]["enabled"]:
            return await process_real_halyk_payment(order, payment_data, payment_id, transaction_id, db)
        else:
            # Fallback to demo if real API not configured
            return {
                "success": False,
                "message": f"Real {payment_data.payment_method.value} API not configured yet. Please enable in production."
            }

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

@app.post("/api/payment/initiate")
async def initiate_payment(request: Request, payment_data: PaymentRequest, db: Session = Depends(get_db)):
    """Initiate payment - IMITATION MODE (ready for real API)"""
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify order exists
    order = db.query(Order).filter(
        Order.id == payment_data.order_id,
        Order.user_id == int(user_id)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Generate unique IDs
    payment_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
    transaction_id = f"TXN-{uuid.uuid4().hex[:16].upper()}"
    
    # Simulate payment processing (2 seconds delay)
    await asyncio.sleep(1)  # Simulate network delay
    
    # IMITATION: Always succeed (with 95% success rate for realism)
    import random
    is_successful = random.random() < 0.95  # 95% success rate
    
    if is_successful:
        # Update order with payment info
        order.payment_id = payment_id
        order.payment_status = "paid"
        order.payment_method = payment_data.payment_method.value
        order.paid_at = datetime.utcnow()
        order.status = OrderStatus.CONFIRMED
        db.commit()
        
        # Create tracking record
        tracking = OrderTracking(
            order_id=order.id,
            status=order.status,
            delivery_status=order.delivery_status,
            message=f"✅ Payment completed via {payment_data.payment_method.value} (Imitation)",
            created_at=datetime.utcnow()
        )
        db.add(tracking)
        db.commit()
        
        # Store transaction for reference
        payment_transactions[payment_id] = {
            "order_id": order.id,
            "order_number": order.order_number,
            "amount": payment_data.amount,
            "payment_method": payment_data.payment_method.value,
            "card_last4": payment_data.card_number[-4:] if payment_data.card_number else "0000",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = PaymentResponse(
            success=True,
            payment_id=payment_id,
            transaction_id=transaction_id,
            amount=payment_data.amount,
            status="completed",
            message=f"✅ Payment successful via {payment_data.payment_method.value}",
            payment_method=payment_data.payment_method.value,
            timestamp=datetime.utcnow().isoformat()
        )
    else:
        # Simulate payment failure
        result = PaymentResponse(
            success=False,
            payment_id=payment_id,
            transaction_id=transaction_id,
            amount=payment_data.amount,
            status="failed",
            message="❌ Payment failed. Insufficient funds or card declined.",
            payment_method=payment_data.payment_method.value,
            timestamp=datetime.utcnow().isoformat()
        )
    
    return result.dict()

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


# backend/main.py - добавьте или обновите эндпоинт добавления в корзину

# backend/main.py - обновите эндпоинт добавления в корзину

# backend/main.py - исправленный эндпоинт

@app.post("/api/cart/add")
async def add_to_cart(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    bag_id = data.get("bag_id")
    quantity = data.get("quantity", 1)
    
    # Проверяем наличие сюрприза (НЕ учитываем временные резервы)
    bag = db.query(SurpriseBag).filter(
        SurpriseBag.id == bag_id,
        SurpriseBag.is_active == True,
        SurpriseBag.available_quantity >= quantity
    ).first()
    
    if not bag:
        raise HTTPException(status_code=404, detail="Товар недоступен")
    
    # Проверяем, есть ли активная временная резервация у этого пользователя
    existing_reservation = db.query(TemporaryReservation).filter(
        TemporaryReservation.bag_id == bag_id,
        TemporaryReservation.user_id == int(user_id),
        TemporaryReservation.is_paid == False,
        TemporaryReservation.expires_at > datetime.utcnow()
    ).first()
    
    if existing_reservation:
        # Обновляем существующую резервацию
        existing_reservation.quantity += quantity
        existing_reservation.expires_at = datetime.utcnow() + timedelta(minutes=15)
        db.commit()
        
        return {
            "success": True,
            "message": "Товар добавлен в корзину",
            "reservation_id": existing_reservation.id,
            "expires_at": existing_reservation.expires_at.isoformat()
        }
    
    # ✅ УМЕНЬШАЕМ ДОСТУПНОЕ КОЛИЧЕСТВО (бронируем)
    old_qty = bag.available_quantity
    bag.available_quantity -= quantity
    print(f"📦 Бронирование: {bag.name}, было {old_qty}, стало {bag.available_quantity}")
    
    # Если стало 0, деактивируем
    if bag.available_quantity <= 0:
        bag.is_active = False
        print(f"🔴 Сюрприз {bag.name} закончился")
    
    # ✅ СОЗДАЕМ ВРЕМЕННУЮ РЕЗЕРВАЦИЮ
    reservation = TemporaryReservation(
        bag_id=bag_id,
        user_id=int(user_id),
        quantity=quantity,
        reserved_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=15),
        is_paid=False
    )
    db.add(reservation)
    db.commit()
    
    # ✅ ОТПРАВЛЯЕМ WEBSOCKET УВЕДОМЛЕНИЕ ВСЕМ КЛИЕНТАМ
    await manager.broadcast({
        "type": "bag_quantity_updated",
        "data": {
            "bag_id": bag_id,
            "available_quantity": bag.available_quantity,
            "is_active": bag.is_active
        },
        "timestamp": datetime.utcnow().isoformat()
    }, channel="surprise_bags")
    
    # Добавляем в корзину пользователя
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == int(user_id),
        CartItem.surprise_bag_id == bag_id
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            user_id=int(user_id),
            surprise_bag_id=bag_id,
            quantity=quantity
        )
        db.add(cart_item)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Товар забронирован на 15 минут",
        "reservation_id": reservation.id,
        "expires_at": reservation.expires_at.isoformat(),
        "available_quantity": bag.available_quantity
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
# backend/main.py - убедитесь что менеджер правильно настроен

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, List[WebSocket]] = {
            "surprise_bags": [],
            "orders": [],
            "all": []
        }
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions["all"].append(websocket)
        print(f"✅ WebSocket connected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict, channel: str = "all"):
        """Отправить сообщение всем подписчикам канала"""
        # Получаем клиентов для канала
        if channel == "all":
            clients = self.active_connections.copy()
        else:
            clients = self.subscriptions.get(channel, []).copy()
        
        disconnected = []
        for connection in clients:
            try:
                await connection.send_json(message)
                print(f"📤 Sent to {channel}: {message.get('type')}")
            except:
                disconnected.append(connection)
        
        # Очищаем отключенных
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)
            for ch in self.subscriptions:
                if connection in self.subscriptions[ch]:
                    self.subscriptions[ch].remove(connection)

manager = ConnectionManager()

# ============ WEBSOCKET ENDPOINT ============
# backend/main.py - добавьте WebSocket обработку

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "subscribe":
                channel = message.get("channel")
                if channel == "surprise_bags":
                    # Отправляем текущие доступные сюрпризы
                    db = SessionLocal()
                    try:
                        active_bags = db.query(SurpriseBag).filter(
                            SurpriseBag.is_active == True,
                            SurpriseBag.available_quantity > 0
                        ).all()
                        
                        bags_data = []
                        for bag in active_bags:
                            supplier = db.query(Supplier).filter(Supplier.id == bag.supplier_id).first()
                            bags_data.append({
                                "id": bag.id,
                                "name": bag.name,
                                "supplier_name": supplier.business_name if supplier else "Unknown",
                                "discounted_price": bag.discounted_price,
                                "available_quantity": bag.available_quantity
                            })
                        
                        await websocket.send_json({
                            "type": "initial_bags",
                            "data": bags_data
                        })
                    finally:
                        db.close()
                        
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
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
        
        formatted_phone = format_phone_number(phone)
        user = db.query(User).filter(User.phone == formatted_phone).first()
        
        if not user or not verify_password(password, user.password):
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Invalid credentials"}
            )
        
        # ✅ СОЗДАЕМ ОТВЕТ С COOKIE
        response = JSONResponse({
            "success": True,
            "redirect": "/",
            "user": {
                "id": user.id,
                "phone": user.phone,
                "full_name": user.full_name,
                "role": user.role.value if user.role else "customer"
            }
        })
        
        # ✅ УСТАНАВЛИВАЕМ COOKIE ПРАВИЛЬНО
        response.set_cookie(
            key="user_id",
            value=str(user.id),
            httponly=True,
            samesite="lax",
            secure=True,  # ← ВАЖНО для HTTPS (Render.com)
            domain=None,   # Автоматически использует текущий домен
            max_age=60*60*24*30  # 30 дней
        )
        
        # Дополнительная cookie для отладки
        response.set_cookie(
            key="user_phone",
            value=user.phone,
            httponly=True,
            samesite="lax",
            secure=True,
            max_age=60*60*24*30
        )
        
        print(f"✅ Login successful for user: {user.phone}, cookie set")
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

# backend/main.py - обновите nearby suppliers

# backend/main.py - показываем только доступные сюрпризы
@app.get("/api/suppliers/nearby")
async def get_nearby_suppliers(lat: float, lon: float, radius: float = 50, db: Session = Depends(get_db)):
    """Получить поставщиков ТОЛЬКО с доступными сюрпризами"""
    all_suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    
    nearby = []
    for supplier in all_suppliers:
        if supplier.lat and supplier.lon:
            distance = haversine_distance(lat, lon, supplier.lat, supplier.lon)
            if distance <= radius:
                # ✅ ТОЛЬКО АКТИВНЫЕ И С available_quantity > 0
                active_bags = db.query(SurpriseBag).filter(
                    SurpriseBag.supplier_id == supplier.id,
                    SurpriseBag.is_active == True,
                    SurpriseBag.available_quantity > 0  # ← ГЛАВНОЕ УСЛОВИЕ!
                ).all()
                
                if active_bags:
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
                                "discount_percentage": bag.discount_percentage,
                                "original_price": bag.original_price,
                                "image_url": bag.image_url,
                                "available_quantity": bag.available_quantity  # ← ОТПРАВЛЯЕМ КОЛИЧЕСТВО
                            } for bag in active_bags
                        ]
                    })
    
    nearby.sort(key=lambda x: x["distance_km"])
    print(f"📍 Найдено поставщиков с доступными сюрпризами: {len(nearby)}")
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

# ============ WEBSOCKET FOR SUPPLIERS ============

# Хранилище для supplier WebSocket соединений
supplier_connections = {}  # {supplier_id: [websocket1, websocket2]}

@app.websocket("/ws/supplier")
async def supplier_websocket_endpoint(websocket: WebSocket):
    """WebSocket для поставщиков - получают уведомления о новых заказах"""
    
    # Получаем supplier_id из query параметра
    supplier_id = websocket.query_params.get("supplier_id")
    
    # Проверяем авторизацию
    cookies = websocket.cookies
    user_id = cookies.get("user_id")
    supplier_cookie = cookies.get("supplier_id")
    
    print(f"🔌 WebSocket connection attempt: supplier_id={supplier_id}")
    
    if not supplier_id:
        print("❌ WebSocket rejected: No supplier_id")
        await websocket.close(code=1008, reason="Supplier ID required")
        return
    
    # Принимаем соединение
    await websocket.accept()
    print(f"✅ WebSocket connected for supplier {supplier_id}")
    
    # Сохраняем соединение
    if supplier_id not in supplier_connections:
        supplier_connections[supplier_id] = []
    supplier_connections[supplier_id].append(websocket)
    
    try:
        # Отправляем приветственное сообщение
        await websocket.send_json({
            "type": "connected",
            "message": f"Connected as supplier {supplier_id}",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Держим соединение открытым
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except:
                pass
                
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for supplier {supplier_id}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        # Удаляем соединение
        if supplier_id in supplier_connections:
            if websocket in supplier_connections[supplier_id]:
                supplier_connections[supplier_id].remove(websocket)
            if not supplier_connections[supplier_id]:
                del supplier_connections[supplier_id]


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

@app.post("/api/orders")
async def create_order(
    request: Request,  # ← ДОБАВИТЬ ЭТОТ ПАРАМЕТР
    order_data: OrderCreate, 
    db: Session = Depends(get_db)
):
    # Check if bag exists
    bag = db.query(SurpriseBag).filter(
        SurpriseBag.id == order_data.bag_id,
        SurpriseBag.is_active == True,
        SurpriseBag.available_quantity > 0
    ).first()
    
    if not bag:
        raise HTTPException(status_code=404, detail="Bag not available")
    
    # Get user from cookie
    user_id = request.cookies.get("user_id")
    
    if user_id:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
    else:
        # Fallback for testing
        user = db.query(User).filter(User.phone == "temp_user").first()
        if not user:
            user = User(
                phone="temp_user",
                password="temp_password",
                full_name="Temporary User",
                role="customer",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    
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
        amount_paid=bag.discounted_price,
        created_at=datetime.utcnow()
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Decrease quantity
    bag.available_quantity -= 1
    db.commit()
    
    # Send WebSocket notification to supplier
    await notify_supplier_new_order(bag.supplier_id, {
        "order_id": order.id,
        "order_number": order.order_number,
        "bag_name": bag.name,
        "amount": bag.discounted_price
    })
    
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
    
@app.post("/supplier/logout")
async def supplier_logout(request: Request):
    response = RedirectResponse(url="/supplier/login", status_code=303)
    response.delete_cookie("supplier_id")
    return response

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


@app.get("/api/supplier/surprise-bags")
async def get_supplier_surprise_bags(request: Request, db: Session = Depends(get_db)):
    """Get all surprise bags for the authenticated supplier"""
    supplier_id = request.cookies.get("supplier_id")
    
    if not supplier_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    bags = db.query(SurpriseBag).filter(
        SurpriseBag.supplier_id == int(supplier_id)
    ).order_by(SurpriseBag.created_at.desc()).all()
    
    result = []
    for bag in bags:
        result.append({
            "id": bag.id,
            "name": bag.name,
            "description": bag.description,
            "original_price": bag.original_price,
            "discounted_price": bag.discounted_price,
            "discount_percentage": bag.discount_percentage,
            "image_url": bag.image_url,
            "available_quantity": bag.available_quantity,
            "is_active": bag.is_active,
            "pickup_start_time": bag.pickup_start_time,
            "pickup_end_time": bag.pickup_end_time,
            "created_at": bag.created_at.isoformat() if bag.created_at else None
        })
    
    return {"bags": result}






@app.post("/api/supplier/surprise-bags")
async def create_surprise_bag(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    supplier_id = request.cookies.get("supplier_id")
    
    if not supplier_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get supplier info
    supplier = db.query(Supplier).filter(Supplier.id == int(supplier_id)).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Calculate discount percentage
    original_price = float(data.get("original_price"))
    discounted_price = float(data.get("discounted_price"))
    
    if discounted_price > original_price:
        raise HTTPException(status_code=400, detail="Discounted price cannot be greater than original price")
    
    discount_percentage = int(((original_price - discounted_price) / original_price) * 100)
    
    # Create bag
    bag = SurpriseBag(
        supplier_id=int(supplier_id),
        name=data.get("name"),
        description=data.get("description"),
        original_price=original_price,
        discounted_price=discounted_price,
        discount_percentage=discount_percentage,
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
    
    # Send WebSocket notification to all clients
    await notify_new_surprise({
        "id": bag.id,
        "name": bag.name,
        "supplier_name": supplier.business_name,
        "discounted_price": bag.discounted_price,
        "original_price": bag.original_price,
        "discount_percentage": bag.discount_percentage,
        "image_url": bag.image_url
    })
    
    return {"success": True, "bag_id": bag.id, "bag": bag}

@app.get("/api/supplier/orders")
async def get_supplier_orders(request: Request, db: Session = Depends(get_db)):
    """Get all orders for the authenticated supplier"""
    supplier_id = request.cookies.get("supplier_id")
    
    if not supplier_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    orders = db.query(Order).filter(
        Order.supplier_id == int(supplier_id)
    ).order_by(Order.created_at.desc()).all()
    
    result = []
    for order in orders:
        bag = db.query(SurpriseBag).filter(SurpriseBag.id == order.surprise_bag_id).first()
        result.append({
            "id": order.id,
            "order_number": order.order_number or f"ORD-{order.id}",
            "bag_name": bag.name if bag else "Surprise Bag",
            "customer_address": order.customer_address or "Address not specified",
            "customer_phone": order.customer_phone,
            "amount_paid": float(order.amount_paid) if order.amount_paid else 0,
            "status": order.status.value if order.status else "pending",
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "pickup_time": order.pickup_time
        })
    
    return {"orders": result}


@app.get("/api/supplier/stats")
async def get_supplier_stats(request: Request, db: Session = Depends(get_db)):
    """Get statistics for the authenticated supplier"""
    supplier_id = request.cookies.get("supplier_id")
    
    if not supplier_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get all orders
    orders = db.query(Order).filter(Order.supplier_id == int(supplier_id)).all()
    
    total_orders = len(orders)
    pending_orders = len([o for o in orders if o.status == OrderStatus.PENDING])
    confirmed_orders = len([o for o in orders if o.status == OrderStatus.CONFIRMED])
    completed_orders = len([o for o in orders if o.status == OrderStatus.DELIVERED])
    
    total_revenue = sum([o.amount_paid or 0 for o in orders])
    
    # Today's orders
    today = datetime.utcnow().date()
    today_orders = len([o for o in orders if o.created_at and o.created_at.date() == today])
    
    # Get active bags count
    active_bags = db.query(SurpriseBag).filter(
        SurpriseBag.supplier_id == int(supplier_id),
        SurpriseBag.is_active == True,
        SurpriseBag.available_quantity > 0
    ).count()
    
    return {
        "stats": {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "confirmed_orders": confirmed_orders,
            "completed_orders": completed_orders,
            "today_orders": today_orders,
            "total_revenue": total_revenue,
            "active_bags": active_bags
        }
    }






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
async def toggle_bag_status(bag_id: int, request: Request, db: Session = Depends(get_db)):
    """Toggle surprise bag active status (activate/deactivate)"""
    supplier_id = request.cookies.get("supplier_id")
    
    if not supplier_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    bag = db.query(SurpriseBag).filter(
        SurpriseBag.id == bag_id,
        SurpriseBag.supplier_id == int(supplier_id)
    ).first()
    
    if not bag:
        raise HTTPException(status_code=404, detail="Bag not found")
    
    bag.is_active = not bag.is_active
    db.commit()
    
    # Notify clients
    if not bag.is_active:
        await notify_bag_deleted(bag_id)
    else:
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



# backend/main.py - добавьте этот эндпоинт

@app.get("/supplier/couriers")
async def supplier_couriers_page(request: Request, db: Session = Depends(get_db)):
    """Страница управления курьерами для поставщика"""
    
    supplier_id = request.cookies.get("supplier_id")
    
    if not supplier_id:
        return RedirectResponse(url="/supplier/login", status_code=303)
    
    supplier = db.query(Supplier).filter(Supplier.id == int(supplier_id)).first()
    if not supplier:
        response = RedirectResponse(url="/supplier/login", status_code=303)
        response.delete_cookie("supplier_id")
        return response
    
    # Получаем курьеров этого поставщика
    couriers = db.query(CourierProfile).filter(
        CourierProfile.supplier_id == int(supplier_id)
    ).all()
    
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
        "lang": request.query_params.get("lang", "ru")
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

@app.post("/supplier/couriers/add")
async def add_courier(request: Request, db: Session = Depends(get_db)):
    supplier_id = request.cookies.get("supplier_id")
    if not supplier_id:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    
    data = await request.json()
    phone = format_phone_number(data.get("phone"))
    full_name = data.get("full_name")
    password = data.get("password")
    car_model = data.get("car_model")
    car_number = data.get("car_number")
    
    # Проверяем, нет ли уже такого пользователя
    existing_user = db.query(User).filter(User.phone == phone).first()
    
    if existing_user:
        # Если пользователь уже есть, просто привязываем к поставщику
        courier_profile = db.query(CourierProfile).filter(CourierProfile.user_id == existing_user.id).first()
        if courier_profile:
            courier_profile.supplier_id = int(supplier_id)
        else:
            courier_profile = CourierProfile(
                user_id=existing_user.id,
                supplier_id=int(supplier_id),
                car_model=car_model,
                car_number=car_number
            )
            db.add(courier_profile)
    else:
        # Создаем нового пользователя
        new_user = User(
            phone=phone,
            full_name=full_name,
            password=hash_password(password),
            role=UserRole.COURIER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(new_user)
        db.flush()
        
        courier_profile = CourierProfile(
            user_id=new_user.id,
            supplier_id=int(supplier_id),
            car_model=car_model,
            car_number=car_number
        )
        db.add(courier_profile)
    
    db.commit()
    return {"success": True}


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



@app.post("/api/courier/orders/{order_id}/status")
async def update_courier_order_status(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Курьер обновляет статус заказа"""
    token = request.cookies.get("courier_token")
    if not token or token not in courier_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await request.json()
    new_status = data.get("status")
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if new_status == "picked_up":
        order.status = OrderStatus.OUT_FOR_DELIVERY
    elif new_status == "delivered":
        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.utcnow()
    
    db.commit()
    
    return {"success": True, "message": f"Status updated to {new_status}"}

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
    supplier_id = request.cookies.get("supplier_id")
    if not supplier_id:
        return RedirectResponse(url="/supplier/login", status_code=303)
    
    supplier = db.query(Supplier).filter(Supplier.id == int(supplier_id)).first()
    if not supplier:
        return RedirectResponse(url="/supplier/login", status_code=303)
    
    return templates.TemplateResponse("supplier_orders.html", {
        "request": request,
        "supplier": supplier
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
# ============ RUN APP ============
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)