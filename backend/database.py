# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.pool import NullPool
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sarqyn.db?charset=utf8")

# Определяем, используем ли SQLite
is_sqlite = DATABASE_URL.startswith("sqlite")

# Настройки для SQLite (оптимизация для Render)
if is_sqlite:
    # Для SQLite используем NullPool и timeout
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 30  # Таймаут для избежания блокировок при одновременных запросах
        },
        poolclass=NullPool,  # Отключаем пул соединений для SQLite
        echo=False
    )
else:
    # Для PostgreSQL (если переключитесь позже)
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,  # Максимум соединений в пуле
        max_overflow=10,  # Дополнительные соединения при пике
        pool_pre_ping=True,  # Проверка соединений перед использованием
        echo=False
    )

# Создаем scoped_session для потокобезопасности
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Create Base
Base = declarative_base()

# Dependency
def get_db():
    """Получение сессии БД (с автоматическим закрытием)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция для инициализации БД (создание таблиц)
def init_db():
    """Создание всех таблиц в БД"""
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована")

# Функция для проверки соединения
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