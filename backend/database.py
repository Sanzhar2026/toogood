
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./sarqyn.db?charset=utf8"



import sys
from sqlalchemy import create_engine, event

# Принудительно ставим UTF-8 везде
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def set_sqlite_encoding(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA encoding = 'UTF-8';")
    cursor.execute("PRAGMA foreign_keys = ON;")   # полезно
    dbapi_conn.commit()

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 20,
    },
    pool_pre_ping=True,
    echo=False   # ← важно выключить, если echo=True — часто вызывает ошибку
)

event.listen(engine, 'connect', set_sqlite_encoding)