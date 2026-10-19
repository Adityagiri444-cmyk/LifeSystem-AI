from typing import List, Literal, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas.content import ContentItem, ContentRecommendationResponse
from app.services.auth import get_current_user
from app.services.content import CATALOG, get_content_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

Category = Literal["movement", "breathing", "music", "video", "entertainment", "journaling", "social"]


@router.get("/content", response_model=ContentRecommendationResponse)
def content_recommendations(
    max_minutes: Optional[int] = Query(default=None, ge=1, le=240),
    category: Optional[Category] = None,
    limit: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_content_recommendations(db, current_user.id, max_minutes, category, limit)


@router.get("/catalog", response_model=List[ContentItem])
def content_catalog(
    category: Optional[Category] = None,
    current_user: User = Depends(get_current_user),
):
    return [i for i in CATALOG if category is None or i["category"] == category]