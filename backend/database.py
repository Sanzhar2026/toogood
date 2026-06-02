# backend/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.pool import NullPool
import os

# ✅ БЕРЕМ ПЕРЕМЕННУЮ ОКРУЖЕНИЯ (Render установит её автоматически)
DATABASE_URL = os.getenv("DATABASE_URL")

# Если нет DATABASE_URL - используем SQLite для локальной разработки
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./SarqytGO.db?charset=utf8"
    print("⚠️ Используется SQLite (только для разработки)")

# ✅ ОПРЕДЕЛЯЕМ ТИП БД
is_sqlite = DATABASE_URL.startswith("sqlite")

# ✅ НАСТРОЙКИ ДЛЯ POSTGRESQL (Production)
if not is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,           # Количество соединений в пуле
        max_overflow=5,         # Дополнительные при пике
        pool_pre_ping=True,     # ✅ Проверка соединений перед использованием
        pool_recycle=300,       # ✅ Пересоздавать каждые 5 минут
        echo=False
    )
    print("✅ Используется PostgreSQL (production)")

# ✅ НАСТРОЙКИ ДЛЯ SQLITE (Локальная разработка)
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=NullPool,
        echo=False
    )
    print("⚠️ Используется SQLite (только для разработки)")

# Создаем scoped_session для потокобезопасности
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()

def get_db():
    """Получение сессии БД (с автоматическим закрытием)"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def init_db():
    """Создание всех таблиц в БД"""
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована")

def check_db_connection():
    """Проверка соединения с БД"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✅ Соединение с БД установлено")
        return True
    except Exception as e:
        print(f"❌ Ошибка соединения с БД: {e}")
        return False