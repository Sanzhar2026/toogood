# backend/routers/users.py - ПОЛНАЯ ВЕРСИЯ БЕЗ ENUM

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid
import os
from datetime import datetime, timedelta
from jose import jwt
from backend.database import get_db
from backend.models import User

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================
SECRET_KEY = os.getenv("SECRET_KEY", "sarqyn-super-secret-key-2024")
ALGORITHM = "HS256"

router = APIRouter(prefix="/users", tags=["users"])

AVATAR_DIR = Path("uploads/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# ПОЛУЧЕНИЕ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ ИЗ ТОКЕНА
# ============================================================
def get_current_user_from_token(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Получить текущего пользователя из JWT токена"""
    
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = auth_header.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # ✅ role - уже строка (VARCHAR)
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User is not active")
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError as e:
        print(f"❌ JWT Error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        print(f"❌ Token error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


# ============================================================
# ОТЛАДКА - ПРОВЕРКА АВАТАРОВ
# ============================================================
@router.get("/debug-avatars")
async def debug_avatars():
    """Отладка - посмотреть какие аватары есть на сервере"""
    files = []
    if AVATAR_DIR.exists():
        files = [f.name for f in AVATAR_DIR.glob("*.webp")]
    
    return {
        "avatars_dir_exists": AVATAR_DIR.exists(),
        "avatars_dir_path": str(AVATAR_DIR.absolute()),
        "files": files,
        "count": len(files)
    }


# ============================================================
# ЗАГРУЗКА АВАТАРА
# ============================================================
@router.post("/{user_id}/avatar")
async def upload_avatar(
    user_id: int,
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Загрузка аватара пользователя"""
    
    # ✅ ИСПРАВЛЕНО: роль как строка (БЕЗ ENUM)
    if current_user.id != user_id and current_user.role != "admin":
        return JSONResponse(
            status_code=403,
            content={"success": False, "detail": "Недостаточно прав"}
        )
    
    # Проверяем тип файла
    if not avatar.content_type.startswith("image/"):
        return JSONResponse(
            status_code=400,
            content={"success": False, "detail": "Файл должен быть изображением"}
        )
    
    # Проверяем размер файла (макс 2MB)
    avatar.file.seek(0, 2)
    size = avatar.file.tell()
    avatar.file.seek(0)
    if size > 2 * 1024 * 1024:
        return JSONResponse(
            status_code=400,
            content={"success": False, "detail": "Файл не должен превышать 2 MB"}
        )
    
    try:
        # Генерируем имя файла
        filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}.webp"
        file_path = AVATAR_DIR / filename
        
        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(avatar.file, buffer)
        
        # Удаляем старые аватары
        for old_file in AVATAR_DIR.glob(f"avatar_{user_id}_*.webp"):
            if old_file != file_path:
                try:
                    old_file.unlink()
                except:
                    pass
        
        # Обновляем URL аватара в БД
        avatar_url = f"/uploads/avatars/{filename}"
        if hasattr(current_user, 'avatar_url'):
            current_user.avatar_url = avatar_url
            db.commit()
        
        print(f"✅ Аватар загружен для пользователя {user_id}: {filename}")
        
        return {
            "success": True,
            "avatar_url": avatar_url,
            "filename": filename,
            "user_id": user_id
        }
        
    except Exception as e:
        print(f"❌ Ошибка загрузки аватара: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": f"Ошибка загрузки: {str(e)}"}
        )


# ============================================================
# УДАЛЕНИЕ АВАТАРА
# ============================================================
@router.delete("/{user_id}/avatar")
async def delete_avatar(
    user_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Удаление аватара пользователя"""
    
    # ✅ ИСПРАВЛЕНО: роль как строка (БЕЗ ENUM)
    if current_user.id != user_id and current_user.role != "admin":
        return JSONResponse(
            status_code=403,
            content={"success": False, "detail": "Недостаточно прав"}
        )
    
    try:
        deleted_count = 0
        for old_file in AVATAR_DIR.glob(f"avatar_{user_id}_*.webp"):
            old_file.unlink()
            deleted_count += 1
        
        # Обновляем URL в БД
        if hasattr(current_user, 'avatar_url'):
            current_user.avatar_url = None
            db.commit()
        
        if deleted_count == 0:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Аватар не найден"}
            )
        
        print(f"✅ Аватар удален для пользователя {user_id}")
        
        return {
            "success": True,
            "message": "Аватар удален",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        print(f"❌ Ошибка удаления аватара: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": f"Ошибка удаления: {str(e)}"}
        )


# ============================================================
# ПОЛУЧЕНИЕ АВАТАРА (ПУБЛИЧНЫЙ ДОСТУП)
# ============================================================
@router.get("/{user_id}/avatar")
async def get_avatar(
    user_id: int,
):
    """Получить файл аватара (публичный доступ)"""
    
    try:
        avatar_files = list(AVATAR_DIR.glob(f"avatar_{user_id}_*.webp"))
        
        if avatar_files:
            file_path = avatar_files[0]
            return FileResponse(
                file_path,
                media_type="image/webp",
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Content-Type": "image/webp"
                }
            )
        
        # Если нет аватара - возвращаем default
        default_avatar = Path("uploads/avatars/default.png")
        if default_avatar.exists():
            return FileResponse(
                default_avatar,
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Content-Type": "image/png"
                }
            )
        
        return JSONResponse(
            status_code=404,
            content={"success": False, "detail": "Аватар не найден"}
        )
        
    except Exception as e:
        print(f"❌ Ошибка получения аватара: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": f"Ошибка: {str(e)}"}
        )


# ============================================================
# ПОЛУЧЕНИЕ ФАЙЛА АВАТАРА (ПРЯМОЙ ДОСТУП)
# ============================================================
@router.get("/avatar-file/{user_id}")
async def get_avatar_file(
    user_id: int,
):
    """Получить файл аватара напрямую (минуя статику)"""
    
    try:
        print(f"🔍 Looking for avatar of user {user_id}")
        print(f"📁 Path: {AVATAR_DIR.absolute()}")
        
        # Ищем файл аватара
        avatar_files = list(AVATAR_DIR.glob(f"avatar_{user_id}_*.webp"))
        
        print(f"📄 Found files: {[f.name for f in avatar_files]}")
        
        if avatar_files:
            file_path = avatar_files[0]
            print(f"✅ Serving: {file_path.name} ({file_path.stat().st_size} bytes)")
            return FileResponse(
                file_path,
                media_type="image/webp",
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Content-Type": "image/webp"
                }
            )
        
        print(f"❌ No avatar for user {user_id}")
        
        # Если нет аватара, возвращаем 204 No Content
        return JSONResponse(
            status_code=204,
            content={"detail": "No avatar"}
        )
        
    except Exception as e:
        print(f"❌ Ошибка получения файла аватара: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": f"Ошибка: {str(e)}"}
        )


# ============================================================
# ПОЛУЧЕНИЕ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ
# ============================================================
@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Получить профиль текущего пользователя"""
    
    # ✅ Ищем аватар
    avatar_url = None
    avatar_files = list(AVATAR_DIR.glob(f"avatar_{current_user.id}_*.webp"))
    if avatar_files:
        avatar_url = f"/uploads/avatars/{avatar_files[0].name}"
    
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "full_name": current_user.full_name,
            "phone": current_user.phone,
            "email": current_user.email,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "avatar_url": avatar_url
        }
    }


# ============================================================
# ОБНОВЛЕНИЕ ПРОФИЛЯ
# ============================================================
@router.put("/profile")
async def update_profile(
    request: Request,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Обновить профиль текущего пользователя"""
    
    try:
        data = await request.json()
        
        if "first_name" in data:
            current_user.first_name = data["first_name"].strip()
        if "last_name" in data:
            current_user.last_name = data["last_name"].strip()
        if "full_name" in data:
            current_user.full_name = data["full_name"].strip()
        if "phone" in data:
            current_user.phone = data["phone"].strip()
        if "email" in data:
            current_user.email = data["email"].strip()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Профиль обновлен",
            "user": {
                "id": current_user.id,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "full_name": current_user.full_name,
                "phone": current_user.phone,
                "email": current_user.email,
                "role": current_user.role
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка обновления профиля: {e}")
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": f"Ошибка: {str(e)}"}
        )