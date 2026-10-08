from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User
from app.schemas.bottleneck import BottleneckResponse
from app.services.auth import get_current_user
from app.services.bottleneck import detect_bottlenecks

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/bottlenecks", response_model=List[BottleneckResponse])
def get_bottlenecks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return detect_bottlenecks(db, current_user.id)