# backend/routers/ratings.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.database import get_db
from backend.models import Rating, SurpriseBag, User
from backend.schemas import (
    RatingCreate, 
    RatingResponse, 
    RatingUpdate, 
    RatingStats,
    MyRatingResponse
)
from backend.auth import get_current_user

router = APIRouter(prefix="/api/surprise-bags", tags=["ratings"])

# ============================================
# 1. ПОЛУЧИТЬ РЕЙТИНГ ДЛЯ СЮРПРИЗА
# ============================================
@router.get("/{bag_id}/rating", response_model=RatingStats)
def get_bag_rating(
    bag_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить рейтинг и статистику для сюрприза
    """
    # Проверяем существует ли сюрприз
    bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
    if not bag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сюрприз не найден"
        )
    
    # Получаем все рейтинги
    ratings = db.query(Rating).filter(Rating.bag_id == bag_id).all()
    
    if not ratings:
        return RatingStats(
            average_rating=0.0,
            total_ratings=0,
            rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            recent_ratings=[]
        )
    
    # Вычисляем статистику
    avg_rating = sum(r.rating for r in ratings) / len(ratings)
    
    # Распределение оценок
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in ratings:
        rounded = int(round(r.rating))
        if rounded in distribution:
            distribution[rounded] += 1
    
    # Последние 5 оценок
    recent = sorted(ratings, key=lambda x: x.created_at, reverse=True)[:5]
    
    return RatingStats(
        average_rating=round(avg_rating, 2),
        total_ratings=len(ratings),
        rating_distribution=distribution,
        recent_ratings=[
            {
                "id": r.id,
                "rating": r.rating,
                "comment": r.comment,
                "user_id": r.user_id,
                "created_at": r.created_at.isoformat()
            }
            for r in recent
        ]
    )

# ============================================
# 2. ДОБАВИТЬ РЕЙТИНГ
# ============================================
@router.post("/{bag_id}/rating", response_model=RatingResponse)
def add_rating(
    bag_id: int,
    rating_data: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Добавить оценку для сюрприза
    """
    # Проверяем существует ли сюрприз
    bag = db.query(SurpriseBag).filter(SurpriseBag.id == bag_id).first()
    if not bag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сюрприз не найден"
        )
    
    # Проверяем валидность оценки
    if not 1.0 <= rating_data.rating <= 5.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Оценка должна быть от 1.0 до 5.0"
        )
    
    # Проверяем не оставлял ли пользователь уже оценку
    existing = db.query(Rating).filter(
        Rating.bag_id == bag_id,
        Rating.user_id == current_user.id
    ).first()
    
    if existing:
        # Обновляем существующую оценку
        existing.rating = rating_data.rating
        existing.comment = rating_data.comment
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    
    # Создаем новую оценку
    new_rating = Rating(
        bag_id=bag_id,
        user_id=current_user.id,
        rating=rating_data.rating,
        comment=rating_data.comment
    )
    
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    
    return new_rating

# ============================================
# 3. ОБНОВИТЬ РЕЙТИНГ
# ============================================
@router.put("/{bag_id}/rating", response_model=RatingResponse)
def update_rating(
    bag_id: int,
    rating_data: RatingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обновить свою оценку для сюрприза
    """
    # Находим оценку
    rating = db.query(Rating).filter(
        Rating.bag_id == bag_id,
        Rating.user_id == current_user.id
    ).first()
    
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Оценка не найдена"
        )
    
    # Обновляем
    rating.rating = rating_data.rating
    rating.comment = rating_data.comment
    rating.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(rating)
    
    return rating

# ============================================
# 4. УДАЛИТЬ РЕЙТИНГ
# ============================================
@router.delete("/{bag_id}/rating", status_code=status.HTTP_204_NO_CONTENT)
def delete_rating(
    bag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Удалить свою оценку для сюрприза
    """
    rating = db.query(Rating).filter(
        Rating.bag_id == bag_id,
        Rating.user_id == current_user.id
    ).first()
    
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Оценка не найдена"
        )
    
    db.delete(rating)
    db.commit()

# ============================================
# 5. ПОЛУЧИТЬ ВСЕ ОЦЕНКИ ПОЛЬЗОВАТЕЛЯ
# ============================================
@router.get("/my/ratings", response_model=List[RatingResponse])
def get_my_ratings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить все оценки текущего пользователя
    """
    ratings = db.query(Rating).filter(
        Rating.user_id == current_user.id
    ).all()
    
    return ratings

# ============================================
# 6. ПОЛУЧИТЬ ОЦЕНКУ ПОЛЬЗОВАТЕЛЯ ДЛЯ СЮРПРИЗА
# ============================================
@router.get("/{bag_id}/my-rating", response_model=Optional[MyRatingResponse])
def get_my_rating_for_bag(
    bag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить оценку текущего пользователя для конкретного сюрприза
    """
    rating = db.query(Rating).filter(
        Rating.bag_id == bag_id,
        Rating.user_id == current_user.id
    ).first()
    
    if not rating:
        return None
    
    return rating