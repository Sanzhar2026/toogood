# backend/models.py - ПОЛНАЯ ВЕРСИЯ С НОВЫМИ МОДЕЛЯМИ

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
    NEARBY = "nearby"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class CourierType(str, enum.Enum):
    PEDESTRIAN = "pedestrian"
    DRIVER = "driver"


# ======== Food model (старый, для совместимости) ========
class Food(Base):
    __tablename__ = "foods"
    id = Column(Integer, primary_key=True, index=True)
    name_ru = Column(String(255))
    name_kz = Column(String(255))
    price = Column(Float)
    image = Column(String(500))
    discount = Column(Integer, default=0)


# ======== SupplierProduct model (НОВЫЙ - товары поставщика) ========
class SupplierProduct(Base):
    """Товары/блюда, которые добавляет сам поставщик"""
    __tablename__ = "supplier_products"
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    
    # Название на разных языках
    name_ru = Column(String(255), nullable=False)
    name_kz = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=True)
    
    # Описание
    description_ru = Column(Text, nullable=True)
    description_kz = Column(Text, nullable=True)
    
    # Цена
    price = Column(Float, nullable=False)
    
    # Категория (блюдо, напиток, десерт и т.д.)
    category = Column(String(100), nullable=True)
    
    # Изображение
    image_url = Column(String(500), nullable=True)
    
    # Доступность
    is_available = Column(Boolean, default=True)
    
    # Время приготовления (в минутах)
    preparation_time = Column(Integer, default=15)
    
    # Создан
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    supplier = relationship("Supplier", back_populates="products")
    surprise_bag_items = relationship("SurpriseBagItem", back_populates="supplier_product")


# ======== CartItem model ========
class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    surprise_bag_id = Column(Integer, ForeignKey("surprise_bags.id", ondelete="CASCADE"))
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="cart_items")
    surprise_bag = relationship("SurpriseBag", back_populates="cart_items")


# ======== User model ========
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(50), unique=True, nullable=False)
    phone_verified = Column(Boolean, default=False)
    password = Column(String(255), nullable=False)
    
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    
    role = Column(SQLEnum(UserRole), default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    supplier_profile = relationship("Supplier", back_populates="user", uselist=False)
    cart_items = relationship("CartItem", back_populates="user")
    courier_profile = relationship("CourierProfile", back_populates="user", uselist=False)
    
    supplier_reviews = relationship("SupplierReview", back_populates="user", cascade="all, delete-orphan")
    surprise_bag_reviews = relationship("SurpriseBagReview", back_populates="user", cascade="all, delete-orphan")


# ======== Supplier model ========
class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    business_name = Column(String(255), nullable=False)
    business_type = Column(String(100))  # restaurant, cafe, fastfood, supermarket, bakery
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
    reviews = relationship("SupplierReview", back_populates="supplier", cascade="all, delete-orphan")
    
    # НОВОЕ: Связь с товарами поставщика
    products = relationship("SupplierProduct", back_populates="supplier", cascade="all, delete-orphan")


# ======== SupplierReview model ========
class SupplierReview(Base):
    __tablename__ = "supplier_reviews"
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    supplier = relationship("Supplier", back_populates="reviews")
    user = relationship("User", back_populates="supplier_reviews")


# ======== SurpriseBagItem model (ОБНОВЛЕН) ========
class SurpriseBagItem(Base):
    __tablename__ = "surprise_bag_items"
    
    id = Column(Integer, primary_key=True)
    surprise_bag_id = Column(Integer, ForeignKey("surprise_bags.id", ondelete="CASCADE"))
    
    # НОВОЕ: Связь с товаром поставщика
    supplier_product_id = Column(Integer, ForeignKey("supplier_products.id", ondelete="CASCADE"), nullable=True)
    
    # Старые поля (для обратной совместимости)
    product_id = Column(Integer, nullable=True)
    product_name = Column(String(255), nullable=True)
    product_price = Column(Integer, nullable=True)
    
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    surprise_bag = relationship("SurpriseBag", back_populates="items")
    supplier_product = relationship("SupplierProduct", back_populates="surprise_bag_items")


# ======== SurpriseBagReview model ========
class SurpriseBagReview(Base):
    __tablename__ = "surprise_bag_reviews"
    
    id = Column(Integer, primary_key=True)
    surprise_bag_id = Column(Integer, ForeignKey("surprise_bags.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    surprise_bag = relationship("SurpriseBag", back_populates="reviews")
    user = relationship("User", back_populates="surprise_bag_reviews")


# ======== SurpriseBag model (ОБНОВЛЕН) ========
class SurpriseBag(Base):
    __tablename__ = "surprise_bags"
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"))
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
    city = Column(String(100), nullable=True)
    hide_contents = Column(Boolean, default=False)
    rating = Column(Float, default=0)
    total_reviews = Column(Integer, default=0)
    
    @property
    def is_surprise_type(self) -> bool:
        return self.hide_contents == True
    
    @property
    def is_search_type(self) -> bool:
        return self.hide_contents == False
    
    @property
    def type_display(self) -> str:
        return "🎁 Surprise" if self.hide_contents else "📋 Search"
    
    supplier = relationship("Supplier", back_populates="surprise_bags")
    orders = relationship("Order", back_populates="surprise_bag")
    cart_items = relationship("CartItem", back_populates="surprise_bag")
    items = relationship("SurpriseBagItem", back_populates="surprise_bag", cascade="all, delete-orphan")
    reviews = relationship("SurpriseBagReview", back_populates="surprise_bag", cascade="all, delete-orphan")


# ======== Order model ========
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    food_id = Column(Integer, ForeignKey("foods.id", ondelete="SET NULL"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    surprise_bag_id = Column(Integer, ForeignKey("surprise_bags.id", ondelete="SET NULL"), nullable=True)
    items = Column(Text, nullable=True)
    total_amount = Column(Float, nullable=True)
    order_number = Column(String(50), unique=True, nullable=True)
    
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    
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
    cancelled_at = Column(DateTime, nullable=True)
    pickup_time = Column(String(50))
    amount_paid = Column(Float, nullable=True)
    
    assigned_courier_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    delivery_type = Column(String(50), default="delivery")
    
    user = relationship("User", back_populates="orders", foreign_keys=[user_id])
    supplier = relationship("Supplier", back_populates="orders", foreign_keys=[supplier_id])
    surprise_bag = relationship("SurpriseBag", back_populates="orders")
    assigned_courier = relationship("User", foreign_keys=[assigned_courier_id])
    tracking_updates = relationship("OrderTracking", back_populates="order")


# ======== OrderTracking model ========
class OrderTracking(Base):
    __tablename__ = "order_tracking"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    status = Column(SQLEnum(OrderStatus), nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    message = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    order = relationship("Order", back_populates="tracking_updates")


# ======== CourierProfile model ========
class CourierProfile(Base):
    __tablename__ = "courier_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
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
    
    current_order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    current_order_status = Column(String(50), default=None)
    
    proposed_order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    proposed_order_expires_at = Column(DateTime, nullable=True)
    
    last_online_at = Column(DateTime, nullable=True)
    last_offline_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="courier_profile")
    current_order = relationship("Order", foreign_keys=[current_order_id])
    proposed_order = relationship("Order", foreign_keys=[proposed_order_id])


# ======== SupplierCourier model ========
class SupplierCourier(Base):
    __tablename__ = "supplier_couriers"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"))
    courier_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ======== AssignedOrder model ========
class AssignedOrder(Base):
    __tablename__ = "assigned_orders"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    courier_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    status = Column(String(50), default="assigned")
    assigned_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    order = relationship("Order", backref="assignments")
    courier = relationship("User", backref="assignments")


# ======== Admin model ========
class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ======== TemporaryReservation model ========
class TemporaryReservation(Base):
    __tablename__ = "temporary_reservations"
    
    id = Column(Integer, primary_key=True)
    bag_id = Column(Integer, ForeignKey("surprise_bags.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1)
    reserved_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_paid = Column(Boolean, default=False)
    
    bag = relationship("SurpriseBag", backref="reservations")
    user = relationship("User", backref="reservations")