from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./sarqyn.db?charset=utf8"



def _add_unicode_support(dbapi_conn, connection_record):
    dbapi_conn.execute("PRAGMA encoding = 'UTF-8'")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 20},
    pool_pre_ping=True,
)

# Подключаем поддержку UTF-8
from sqlalchemy import event
event.listen(engine, 'connect', _add_unicode_support)



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()