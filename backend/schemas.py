# backend/schemas.py - ПОЛНАЯ ВЕРСИЯ С РЕЙТИНГАМИ

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

# ============================================================
# ВНИМАНИЕ: ЭТИ ENUM ОСТАВЛЕНЫ ТОЛЬКО ДЛЯ PYDANTIC ВАЛИДАЦИИ
# НО В БАЗЕ ДАННЫХ ИХ НЕТ - ТАМ ТОЛЬКО VARCHAR!
# ============================================================

class UserRole(str, Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    COURIER = "courier"
    ADMIN = "admin"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"
    OUT_FOR_DELIVERY = "out_for_delivery"
    NEARBY = "nearby"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    KASPI = "kaspi"
    HALYK = "halyk"
    MASTERCARD = "mastercard"
    VISA = "visa"
    CASH = "cash"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class CourierType(str, Enum):
    PEDESTRIAN = "pedestrian"
    DRIVER = "driver"


# ============================================================
# USER SCHEMAS
# ============================================================

class UserCreate(BaseModel):
    email: Optional[str] = None
    phone: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER

class UserResponse(BaseModel):
    id: int
    email: Optional[str]
    phone: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    phone_verified: bool
    role: str
    is_active: bool
    created_at: datetime
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# PHONE VERIFICATION SCHEMAS
# ============================================================

class PhoneVerificationRequest(BaseModel):
    phone_number: str

class PhoneVerificationResponse(BaseModel):
    success: bool
    message: str
    demo: bool = False

class PhoneRegisterRequest(BaseModel):
    phone_number: str
    full_name: str
    password: str
    verification_code: str

class PhoneLoginRequest(BaseModel):
    phone_number: str
    password: str


# ============================================================
# SUPPLIER SCHEMAS
# ============================================================

class SupplierCreate(BaseModel):
    business_name: str
    business_type: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = "Алматы"
    address: str
    lat: float
    lon: float
    phone: str
    email: str
    pickup_start_time: Optional[str] = None
    pickup_end_time: Optional[str] = None

class SupplierResponse(BaseModel):
    id: int
    business_name: str
    business_type: Optional[str]
    description: Optional[str]
    logo: Optional[str]
    cover_image: Optional[str]
    city: Optional[str]
    address: str
    lat: float
    lon: float
    rating: float
    total_reviews: int
    is_verified: bool
    is_active: bool
    pickup_start_time: Optional[str]
    pickup_end_time: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================
# SURPRISE BAG SCHEMAS
# ============================================================

class SurpriseBagCreate(BaseModel):
    name: str
    description: Optional[str] = None
    original_price: float
    discounted_price: float
    image_url: Optional[str] = None
    available_quantity: int = 1
    total_quantity: Optional[int] = 1
    pickup_start_time: Optional[str] = None
    pickup_end_time: Optional[str] = None
    possible_items: Optional[str] = None
    hide_contents: bool = False
    city: Optional[str] = None

class SurpriseBagResponse(BaseModel):
    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    name: str
    description: Optional[str]
    original_price: float
    discounted_price: float
    discount_percentage: Optional[int]
    image_url: Optional[str]
    available_quantity: int
    total_quantity: Optional[int]
    pickup_start_time: Optional[str]
    pickup_end_time: Optional[str]
    is_active: bool
    created_at: Optional[datetime]
    hide_contents: bool = False
    city: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# ORDER SCHEMAS
# ============================================================

class OrderCreate(BaseModel):
    bag_id: int
    lat: float = 0
    lon: float = 0
    address: str
    pickup_time: Optional[str] = None
    user_id: Optional[int] = 1
    delivery_type: str = "delivery"

class OrderResponse(BaseModel):
    id: int
    order_number: str
    status: str
    delivery_type: Optional[str] = None
    customer_address: Optional[str]
    amount_paid: float
    created_at: datetime
    supplier_name: Optional[str] = None
    supplier_id: Optional[int] = None
    surprise_bag_name: Optional[str] = None
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None
    paid_at: Optional[datetime] = None
    delivery_deadline: Optional[datetime] = None
    assigned_courier_id: Optional[int] = None
    assigned_courier_name: Optional[str] = None

    class Config:
        from_attributes = True


class OrderTrackingUpdate(BaseModel):
    order_id: int
    status: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    message: str


# ============================================================
# DELIVERY SCHEMAS
# ============================================================

class DeliveryPosition(BaseModel):
    lat: float
    lon: float
    progress: float
    remaining_steps: int
    is_complete: bool = False

class DeliveryInfo(BaseModel):
    order_id: int
    order_number: str
    supplier_name: str
    supplier_location: dict
    customer_location: dict
    customer_address: str
    bag_name: str
    distance_km: float
    eta_minutes: int
    status: str
    progress: Optional[float] = 0


# ============================================================
# API RESPONSE SCHEMAS
# ============================================================

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None


# ============================================================
# PAYMENT SCHEMAS
# ============================================================

class PaymentRequest(BaseModel):
    order_id: int
    payment_method: str
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
    status: str
    message: str
    payment_method: str
    timestamp: str

class PaymentStatusResponse(BaseModel):
    payment_id: str
    order_id: int
    order_number: str
    amount: float
    status: str
    payment_method: str
    card_last4: Optional[str] = None
    timestamp: str

class PaymentHistoryItem(BaseModel):
    order_id: int
    order_number: str
    amount: float
    payment_method: str
    payment_id: Optional[str]
    paid_at: Optional[datetime]
    status: str

class PaymentHistoryResponse(BaseModel):
    history: List[PaymentHistoryItem]


# ============================================================
# ADMIN SCHEMAS
# ============================================================

class AdminCreate(BaseModel):
    username: str
    password: str

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

class AdminUpdatePassword(BaseModel):
    old_password: str
    new_password: str


# ============================================================
# COURIER SCHEMAS
# ============================================================

class CourierRegisterRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str
    password: str
    courier_type: str = "pedestrian"
    car_model: Optional[str] = None
    car_number: Optional[str] = None

class CourierStatusResponse(BaseModel):
    success: bool
    is_online: bool
    is_available: bool
    is_verified: bool
    current_order_id: Optional[int]
    current_order_status: Optional[str]
    courier_type: str
    rating: float
    total_deliveries: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    car_model: Optional[str] = None
    car_number: Optional[str] = None

class CourierLocationUpdate(BaseModel):
    lat: float
    lon: float

class CourierResponse(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    phone: str
    courier_type: str
    car_model: Optional[str]
    car_number: Optional[str]
    is_online: bool
    is_verified: bool
    rating: float
    total_deliveries: int
    current_lat: Optional[float]
    current_lon: Optional[float]
    current_order_status: Optional[str]

    class Config:
        from_attributes = True


# ============================================================
# CART SCHEMAS
# ============================================================

class CartItemResponse(BaseModel):
    id: int
    surprise_bag_id: int
    name: str
    price: float
    original_price: float
    image_url: Optional[str]
    quantity: int
    supplier_name: str
    supplier_id: int

    class Config:
        from_attributes = True


# ============================================================
# BOOKING SCHEMAS
# ============================================================

class BookingRequest(BaseModel):
    bag_id: int

class BookingResponse(BaseModel):
    success: bool
    message: str
    expires_at: Optional[str] = None
    remaining_seconds: Optional[int] = None
    order_id: Optional[int] = None


# ============================================================
# REVIEW SCHEMAS
# ============================================================

class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# ✅ RATING SCHEMAS (НОВЫЕ)
# ============================================================

class RatingBase(BaseModel):
    """Базовая схема для рейтинга"""
    rating: float = Field(ge=1.0, le=5.0, description="Оценка от 1.0 до 5.0")
    comment: Optional[str] = Field(None, max_length=500, description="Комментарий к оценке")

class RatingCreate(RatingBase):
    """Схема для создания рейтинга"""
    bag_id: int = Field(..., description="ID сюрприза")

class RatingUpdate(RatingBase):
    """Схема для обновления рейтинга"""
    pass

class RatingResponse(RatingBase):
    """Схема для ответа с рейтингом"""
    id: int
    bag_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RatingStats(BaseModel):
    """Статистика рейтингов для сюрприза"""
    average_rating: float = Field(..., description="Средняя оценка")
    total_ratings: int = Field(..., description="Количество оценок")
    rating_distribution: dict = Field(..., description="Распределение оценок {1: 0, 2: 0, ...}")
    recent_ratings: List[dict] = Field(default=[], description="Последние 5 оценок")

class MyRatingResponse(BaseModel):
    """Ответ с рейтингом пользователя для конкретного сюрприза"""
    id: int
    bag_id: int
    rating: float
    comment: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True