from sqlalchemy import Column, Integer, String, Float, ForeignKey
from backend.database import Base

class Food(Base):
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    name_ru = Column(String(255))
    name_kz = Column(String(255))
    price = Column(Float)
    image = Column(String(500))
    discount = Column(Integer, default=0)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    food_id = Column(Integer, ForeignKey("foods.id"))
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    address = Column(String(500), nullable=True)  # ADD THIS FIELD