# backend/models.py - ИСПРАВЛЕННАЯ ВЕРСИЯ (без дубликатов)

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base
import enum

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    COURIER = "courier"  
    ADMIN = "admin"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"
    OUT_FOR_DELIVERY = "out_for_delivery"
    NEARBY = "nearby"  # ← ДОБАВЬТЕ
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class DeliveryStatus(str, enum.Enum):
    AT_SUPPLIER = "at_supplier"
    EN_ROUTE = "en_route"
    NEARBY = "nearby"
    ARRIVED = "arrived"

class CourierType(str, enum.Enum):
    PEDESTRIAN = "pedestrian"
    DRIVER = "driver"

# Food model
class Food(Base):
    __tablename__ = "foods"
    id = Column(Integer, primary_key=True, index=True)
    name_ru = Column(String(255))
    name_kz = Column(String(255))
    price = Column(Float)
    image = Column(String(500))
    discount = Column(Integer, default=0)

# CartItem model
class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    surprise_bag_id = Column(Integer, ForeignKey("surprise_bags.id"), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="cart_items")
    surprise_bag = relationship("SurpriseBag", back_populates="cart_items")

# User model - ТОЛЬКО ОДИН РАЗ!
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(50), unique=True, nullable=False)
    phone_verified = Column(Boolean, default=False)
    password = Column(String(255), nullable=False)
    
    # Личные данные
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    
    role = Column(SQLEnum(UserRole), default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    supplier_profile = relationship("Supplier", back_populates="user", uselist=False)
    cart_items = relationship("CartItem", back_populates="user")
    courier_profile = relationship("CourierProfile", back_populates="user", uselist=False)

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    business_name = Column(String(255), nullable=False)
    business_type = Column(String(100))
    description = Column(Text)
    logo = Column(String(500))
    cover_image = Column(String(500))
    address = Column(String(500))
    city = Column(String(100))
    lat = Column(Float)
    lon = Column(Float)
    phone = Column(String(50))
    email = Column(String(255))
    rating = Column(Float, default=0)
    total_reviews = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    pickup_start_time = Column(String(50))
    pickup_end_time = Column(String(50))
    
    user = relationship("User", back_populates="supplier_profile")
    surprise_bags = relationship("SurpriseBag", back_populates="supplier")
    orders = relationship("Order", back_populates="supplier", foreign_keys="Order.supplier_id")

class SurpriseBag(Base):
    __tablename__ = "surprise_bags"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    original_price = Column(Float, nullable=False)
    discounted_price = Column(Float, nullable=False)
    discount_percentage = Column(Integer)
    image_url = Column(String(500))
    available_quantity = Column(Integer, default=1)
    total_quantity = Column(Integer, default=1)
    pickup_start_time = Column(String(50))
    pickup_end_time = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    possible_items = Column(Text)
    
    supplier = relationship("Supplier", back_populates="surprise_bags")
    orders = relationship("Order", back_populates="surprise_bag")
    cart_items = relationship("CartItem", back_populates="surprise_bag")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    surprise_bag_id = Column(Integer, ForeignKey("surprise_bags.id"), nullable=True)
    items = Column(Text, nullable=True)
    total_amount = Column(Float, nullable=True)
    order_number = Column(String(50), unique=True, nullable=True)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    delivery_status = Column(SQLEnum(DeliveryStatus), default=DeliveryStatus.AT_SUPPLIER)
    
    payment_id = Column(String(100), nullable=True)
    payment_status = Column(String(50), default="pending")
    payment_method = Column(String(50), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    payment_amount = Column(Float, nullable=True)
    transaction_id = Column(String(100), nullable=True)
    
    customer_lat = Column(Float, nullable=True)
    customer_lon = Column(Float, nullable=True)
    customer_address = Column(String(500), nullable=True)
    
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    address = Column(String(500), nullable=True)
    
    driver_lat = Column(Float, nullable=True)
    driver_lon = Column(Float, nullable=True)
    last_location_update = Column(DateTime, nullable=True)
    
    delivery_started_at = Column(DateTime, nullable=True)
    delivery_deadline = Column(DateTime, nullable=True)
    auto_refund_processed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    ready_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)  # ✅ ДОБАВИТЬ ЭТУ СТРОКУ
    pickup_time = Column(String(50))
    amount_paid = Column(Float, nullable=True)
    
    assigned_courier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    delivery_type = Column(String(50), default="delivery")  # ✅ ДОБАВИТЬ ЭТУ СТРОКУ (для самовывоза)
    
    user = relationship("User", back_populates="orders", foreign_keys=[user_id])
    supplier = relationship("Supplier", back_populates="orders", foreign_keys=[supplier_id])
    surprise_bag = relationship("SurpriseBag", back_populates="orders")
    assigned_courier = relationship("User", foreign_keys=[assigned_courier_id])
    tracking_updates = relationship("OrderTracking", back_populates="order")
class OrderTracking(Base):
    __tablename__ = "order_tracking"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    status = Column(SQLEnum(OrderStatus), nullable=True)
    delivery_status = Column(SQLEnum(DeliveryStatus), nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    message = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    order = relationship("Order", back_populates="tracking_updates")

class CourierProfile(Base):
    __tablename__ = "courier_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False, unique=True)
    courier_type = Column(String(20), default="pedestrian")
    car_model = Column(String(100), nullable=True)
    car_number = Column(String(50), nullable=True)
    speed_kmh = Column(Float, default=5.0)
    delivery_radius_km = Column(Float, default=3.0)
    
    is_online = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    rating = Column(Float, default=5.0)
    total_deliveries = Column(Integer, default=0)
    completed_orders_today = Column(Integer, default=0)
    
    current_lat = Column(Float, nullable=True)
    current_lon = Column(Float, nullable=True)
    last_location_update = Column(DateTime, nullable=True)
    
    current_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    current_order_status = Column(String(50), default=None)
    
    proposed_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    proposed_order_expires_at = Column(DateTime, nullable=True)
    
    last_online_at = Column(DateTime, nullable=True)
    last_offline_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="courier_profile")
    current_order = relationship("Order", foreign_keys=[current_order_id])
    proposed_order = relationship("Order", foreign_keys=[proposed_order_id])

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class SupplierCourier(Base):
    __tablename__ = "supplier_couriers"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    courier_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AssignedOrder(Base):
    __tablename__ = "assigned_orders"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    courier_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(50), default="assigned")
    assigned_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    order = relationship("Order", backref="assignments")
    courier = relationship("User", backref="assignments")

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TemporaryReservation(Base):
    __tablename__ = "temporary_reservations"
    
    id = Column(Integer, primary_key=True)
    bag_id = Column(Integer, ForeignKey("surprise_bags.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quantity = Column(Integer, default=1)
    reserved_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # reserved_at + 15 минут
    is_paid = Column(Boolean, default=False)
    
    # Relationships
    bag = relationship("SurpriseBag", backref="reservations")
    user = relationship("User", backref="reservations")