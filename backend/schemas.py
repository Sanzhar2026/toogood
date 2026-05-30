from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    ADMIN = "admin"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class DeliveryStatus(str, Enum):
    AT_SUPPLIER = "at_supplier"
    EN_ROUTE = "en_route"
    NEARBY = "nearby"
    ARRIVED = "arrived"

# ============ USER SCHEMAS ============
class UserCreate(BaseModel):
    """For creating a new user"""
    email: Optional[str] = None  # Made optional - phone is primary
    phone: str  # REQUIRED - phone number
    password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER

class UserResponse(BaseModel):
    id: int
    email: Optional[str]
    phone: str
    full_name: Optional[str]
    phone_verified: bool
    role: UserRole
    is_active: bool
    created_at: datetime

# ============ PHONE VERIFICATION SCHEMAS ============
class PhoneVerificationRequest(BaseModel):
    """Request to send SMS verification code"""
    phone_number: str

class PhoneVerificationResponse(BaseModel):
    success: bool
    message: str
    demo: bool = False

class PhoneRegisterRequest(BaseModel):
    """Complete registration with phone verification"""
    phone_number: str
    full_name: str
    password: str
    verification_code: str

class PhoneLoginRequest(BaseModel):
    """Login with phone number"""
    phone_number: str
    password: str

# ============ SUPPLIER SCHEMAS ============
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

# ============ SURPRISE BAG SCHEMAS ============
class SurpriseBagCreate(BaseModel):
    name: str
    description: Optional[str] = None
    original_price: float
    discounted_price: float
    image_url: Optional[str] = None
    available_quantity: int = 1
    pickup_start_time: Optional[str] = None
    pickup_end_time: Optional[str] = None
    possible_items: Optional[str] = None

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

# ============ ORDER SCHEMAS ============
class OrderCreate(BaseModel):
    surprise_bag_id: int
    customer_lat: float
    customer_lon: float
    customer_address: str
    pickup_time: Optional[str] = None
    user_id: Optional[int] = 1  # Temporary, will be from auth

class OrderResponse(BaseModel):
    id: int
    order_number: str
    status: OrderStatus
    delivery_status: Optional[str]
    customer_address: str
    amount_paid: float
    created_at: datetime
    supplier: Optional[SupplierResponse]
    surprise_bag: Optional[SurpriseBagResponse]

class OrderTrackingUpdate(BaseModel):
    order_id: int
    status: OrderStatus
    delivery_status: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    message: str

# ============ DELIVERY SCHEMAS ============
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

# ============ API RESPONSE SCHEMAS ============
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None

    # backend/schemas.py - Add these schemas

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

# ... existing code ...

# ============ PAYMENT SCHEMAS ============

class PaymentMethod(str, Enum):
    KASPI = "kaspi"
    HALYK = "halyk"
    MASTERCARD = "mastercard"
    VISA = "visa"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentRequest(BaseModel):
    """Payment initiation request"""
    order_id: int
    payment_method: PaymentMethod
    amount: float
    card_number: Optional[str] = None
    card_expiry: Optional[str] = None
    card_cvv: Optional[str] = None
    card_holder: Optional[str] = None

class PaymentResponse(BaseModel):
    """Payment response"""
    success: bool
    payment_id: str
    transaction_id: str
    amount: float
    status: str
    message: str
    payment_method: str
    timestamp: str

class PaymentStatusResponse(BaseModel):
    """Payment status check response"""
    payment_id: str
    order_id: int
    order_number: str
    amount: float
    status: str
    payment_method: str
    card_last4: Optional[str] = None
    timestamp: str

class PaymentHistoryItem(BaseModel):
    """Single payment history item"""
    order_id: int
    order_number: str
    amount: float
    payment_method: str
    payment_id: Optional[str]
    paid_at: Optional[datetime]
    status: str

class PaymentHistoryResponse(BaseModel):
    """Payment history response"""
    history: List[PaymentHistoryItem]

# Update OrderResponse to include payment info
class OrderResponse(BaseModel):
    id: int
    order_number: str
    status: OrderStatus
    delivery_status: Optional[str]
    customer_address: str
    amount_paid: float
    created_at: datetime
    supplier: Optional[SupplierResponse]
    surprise_bag: Optional[SurpriseBagResponse]
    # Payment fields
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None
    paid_at: Optional[datetime] = None

# ============ ADMIN SCHEMAS ============
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

# backend/schemas.py - добавьте в самый конец файла

# ============ COURIER SCHEMAS ============

class CourierType(str, Enum):
    PEDESTRIAN = "pedestrian"
    DRIVER = "driver"

class CourierRegisterRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str
    password: str
    courier_type: CourierType = CourierType.PEDESTRIAN
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