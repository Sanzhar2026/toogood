# create_admin.py
from backend.database import SessionLocal
from backend.models import Admin
import hashlib

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

db = SessionLocal()

admin = db.query(Admin).filter(Admin.username == "ACCOUNTA@#$26").first()
if not admin:
    admin = Admin(
        username="ACCOUNTA@#$26",
        password_hash=hash_password("CEVONICQW%&%y*")
    )
    db.add(admin)
    db.commit()
    print("✅ Админ создан")
else:
    print(f"Админ уже существует: {admin.username}")

db.close()