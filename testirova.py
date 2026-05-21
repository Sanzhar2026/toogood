# add_payment_columns.py
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime, Float
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./toogood.db")

def add_payment_columns():
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    
    # Reflect existing table
    orders = Table('orders', metadata, autoload_with=engine)
    
    # Add columns if they don't exist
    with engine.connect() as conn:
        try:
            conn.execute("ALTER TABLE orders ADD COLUMN payment_id VARCHAR(100)")
            print("✅ Added payment_id column")
        except Exception as e:
            print(f"payment_id column may already exist: {e}")
        
        try:
            conn.execute("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(50) DEFAULT 'pending'")
            print("✅ Added payment_status column")
        except Exception as e:
            print(f"payment_status column may already exist: {e}")
        
        try:
            conn.execute("ALTER TABLE orders ADD COLUMN payment_method VARCHAR(50)")
            print("✅ Added payment_method column")
        except Exception as e:
            print(f"payment_method column may already exist: {e}")
        
        try:
            conn.execute("ALTER TABLE orders ADD COLUMN paid_at DATETIME")
            print("✅ Added paid_at column")
        except Exception as e:
            print(f"paid_at column may already exist: {e}")
        
        try:
            conn.execute("ALTER TABLE orders ADD COLUMN payment_amount FLOAT")
            print("✅ Added payment_amount column")
        except Exception as e:
            print(f"payment_amount column may already exist: {e}")
        
        try:
            conn.execute("ALTER TABLE orders ADD COLUMN transaction_id VARCHAR(100)")
            print("✅ Added transaction_id column")
        except Exception as e:
            print(f"transaction_id column may already exist: {e}")
        
        conn.commit()
    
    print("\n✅ All payment columns added successfully!")

if __name__ == "__main__":
    add_payment_columns()