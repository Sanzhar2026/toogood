# backend/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid
from datetime import datetime, timedelta
from backend.routes.users import router as users_router
from backend.database import get_db
from backend.models import User, UserRole
from jose import jwt
import os
SECRET_KEY = os.getenv("SECRET_KEY", "sarqyn-super-secret-key-2024") # 👈 Должен совпадать с main.py
ALGORITHM = "HS256"

router = APIRouter(prefix="/users", tags=["users"])

AVATAR_DIR = Path("uploads/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)


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
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        print(f"❌ Token error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/debug-avatars")
async def debug_avatars():
    """Отладка - посмотреть какие аватары есть на сервере"""
    import os
    avatars_dir = Path("uploads/avatars")
    
    files = []
    if avatars_dir.exists():
        files = [f.name for f in avatars_dir.glob("*.webp")]
    
    return {
        "avatars_dir_exists": avatars_dir.exists(),
        "avatars_dir_path": str(avatars_dir.absolute()),
        "files": files,
        "count": len(files)
    }


@router.post("/{user_id}/avatar")
async def upload_avatar(
    user_id: int,
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Загрузка аватара пользователя"""
    
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    if not avatar.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Файл должен быть изображением")
    
    avatar.file.seek(0, 2)
    size = avatar.file.tell()
    avatar.file.seek(0)
    if size > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Файл не должен превышать 2 MB")
    
    filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}.webp"
    file_path = AVATAR_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(avatar.file, buffer)
    
    for old_file in AVATAR_DIR.glob(f"avatar_{user_id}_*.webp"):
        if old_file != file_path:
            try:
                old_file.unlink()
            except:
                pass
    
    avatar_url = f"/uploads/avatars/{filename}"
    
    return {"success": True, "avatar_url": avatar_url}


@router.delete("/{user_id}/avatar")
async def delete_avatar(
    user_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Удаление аватара пользователя"""
    
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    deleted_count = 0
    for old_file in AVATAR_DIR.glob(f"avatar_{user_id}_*.webp"):
        old_file.unlink()
        deleted_count += 1
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Аватар не найден")
    
    return {"success": True, "message": "Аватар удален"}


@router.get("/{user_id}/avatar")
async def get_avatar(
    user_id: int,
):
    """Получить файл аватара (публичный доступ)"""
    
    avatar_files = list(AVATAR_DIR.glob(f"avatar_{user_id}_*.webp"))
    
    if avatar_files:
        return FileResponse(avatar_files[0])
    
    default_avatar = Path("uploads/avatars/default.png")
    if default_avatar.exists():
        return FileResponse(default_avatar)
    
    raise HTTPException(status_code=404, detail="Аватар не найден")

@router.get("/avatar-file/{user_id}")
async def get_avatar_file(
    user_id: int,
):
    """Получить файл аватара напрямую (минуя статику)"""
    
    from pathlib import Path
    
    # Директория с аватарами
    AVATAR_DIR = Path("uploads/avatars")
    
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
    raise HTTPException(status_code=204, detail="No avatar")
