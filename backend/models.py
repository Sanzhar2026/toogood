from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base
import enum

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    ADMIN = "admin"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class DeliveryStatus(str, enum.Enum):
    AT_SUPPLIER = "at_supplier"
    EN_ROUTE = "en_route"
    NEARBY = "nearby"
    ARRIVED = "arrived"

# Original Food model
class Food(Base):
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    name_ru = Column(String(255))
    name_kz = Column(String(255))
    price = Column(Float)
    image = Column(String(500))
    discount = Column(Integer, default=0)


# User model with phone verification
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(50), unique=True, nullable=False)
    phone_verified = Column(Boolean, default=False)
    password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(SQLEnum(UserRole), default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    supplier_profile = relationship("Supplier", back_populates="user", uselist=False)


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
    
    # Pickup hours
    pickup_start_time = Column(String(50))
    pickup_end_time = Column(String(50))
    
    # Relationships
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
    
    # Relationships
    supplier = relationship("Supplier", back_populates="surprise_bags")
    orders = relationship("Order", back_populates="surprise_bag")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    food_id = Column(Integer, ForeignKey("foods.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    surprise_bag_id = Column(Integer, ForeignKey("surprise_bags.id"), nullable=True)
    
    # Order details
    order_number = Column(String(50), unique=True, nullable=True)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    delivery_status = Column(SQLEnum(DeliveryStatus), default=DeliveryStatus.AT_SUPPLIER)
    
    # Customer location
    customer_lat = Column(Float, nullable=True)
    customer_lon = Column(Float, nullable=True)
    customer_address = Column(String(500), nullable=True)
    
    # Old system location fields
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    address = Column(String(500), nullable=True)
    
    # Delivery tracking
    driver_lat = Column(Float, nullable=True)
    driver_lon = Column(Float, nullable=True)
    last_location_update = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    ready_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    pickup_time = Column(String(50))
    
    # Pricing
    amount_paid = Column(Float, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders", foreign_keys=[user_id])
    supplier = relationship("Supplier", back_populates="orders", foreign_keys=[supplier_id])
    surprise_bag = relationship("SurpriseBag", back_populates="orders")
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
    
    # Relationships
    order = relationship("Order", back_populates="tracking_updates")


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)