from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserProfile
from app.schemas.profile import ProfileCreate, ProfileResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])

@router.post("/", response_model=ProfileResponse)
def create_or_update_profile(
    profile_data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    if profile:
        profile.age_range = profile_data.age_range
        profile.availability = profile_data.availability
        profile.preferences = profile_data.preferences
    else:
        profile = UserProfile(
            user_id=current_user.id,
            age_range=profile_data.age_range,
            availability=profile_data.availability,
            preferences=profile_data.preferences,
        )
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/", response_model=ProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile