"""
Profile management routes
"""
import base64
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import User, Profile, Interest, Photo, Preference, Match, Notification, MatchStatus
from app.schemas import (
    ProfileInDB, ProfileUpdate, ProfileCreate,
    InterestBase, PhotoCreate, PhotoBase,
    PreferenceCreate, PreferenceUpdate, PreferenceBase
)
from app.auth import get_current_user, require_ownership_or_admin
from app.services.ai_service import AIService
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"

router = APIRouter(prefix="/profiles", tags=["Profiles"])


# ============================================================================
# Profile CRUD
# ============================================================================

@router.get("/me", response_model=ProfileInDB)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile"""
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    return current_user.profile


@router.get("/{user_id}", response_model=ProfileInDB)
async def get_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile by user ID"""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    return profile


@router.put("/me", response_model=ProfileInDB)
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    profile = current_user.profile

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    # Update fields
    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    # Calculate profile completion
    profile.profile_completion = calculate_profile_completion(profile)

    db.commit()
    db.refresh(profile)

    return profile


@router.post("/complete-onboarding")
async def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark onboarding as completed and create initial matches"""
    profile = current_user.profile

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    profile.onboarding_completed = True
    db.commit()

    # Auto-create initial matches for better UX
    try:
        matches_created = await auto_create_initial_matches(current_user, db)
        return {
            "message": "Onboarding completed successfully",
            "matches_created": matches_created
        }
    except Exception as e:
        # Don't fail onboarding if auto-match fails
        print(f"Auto-match failed: {e}")
        return {"message": "Onboarding completed successfully", "matches_created": 0}


async def auto_create_initial_matches(
    current_user: User,
    db: Session,
    num_matches: int = 3
) -> int:
    """
    Auto-create initial matches for newly onboarded users

    Args:
        current_user: The newly onboarded user
        db: Database session
        num_matches: Number of matches to create (default: 3)

    Returns:
        Number of matches created
    """
    user_profile = current_user.profile

    if not user_profile or not user_profile.preferences:
        return 0

    prefs = user_profile.preferences

    # Calculate age range from date of birth
    if user_profile.date_of_birth:
        user_age = (datetime.now().date() - user_profile.date_of_birth).days // 365
    else:
        user_age = 25  # Default fallback

    min_birth_date = datetime.now().date() - timedelta(days=prefs.max_age * 365)
    max_birth_date = datetime.now().date() - timedelta(days=prefs.min_age * 365)

    # Normalize looking_for values (handle both enum objects and string values)
    from app.models import Gender
    looking_for_values = []
    for g in (prefs.looking_for or []):
        if isinstance(g, Gender):
            looking_for_values.append(g.value)
        elif isinstance(g, str):
            looking_for_values.append(g)
        else:
            looking_for_values.append(str(g))

    if not looking_for_values:
        looking_for_values = [g.value for g in Gender]

    # Query compatible users
    candidates = db.query(Profile).join(User).filter(
        Profile.user_id != current_user.id,
        User.is_active == True,
        Profile.onboarding_completed == True,
        # Age preference
        Profile.date_of_birth.between(min_birth_date, max_birth_date),
        # Gender preference
        Profile.gender.in_(looking_for_values)
    ).limit(10).all()

    if not candidates:
        return 0

    # Calculate compatibility for each candidate
    ai_service = AIService(db)
    scored_candidates = []

    for candidate in candidates:
        try:
            # Check if match already exists
            existing_match = db.query(Match).filter(
                or_(
                    and_(
                        Match.user1_id == min(current_user.id, candidate.user_id),
                        Match.user2_id == max(current_user.id, candidate.user_id)
                    )
                )
            ).first()

            if existing_match:
                continue

            # Calculate AI compatibility
            score, reasons, ice_breakers = await ai_service.calculate_compatibility(
                user_profile, candidate
            )

            scored_candidates.append({
                'candidate': candidate,
                'score': score,
                'reasons': reasons,
                'ice_breakers': ice_breakers
            })
        except Exception as e:
            print(f"Error calculating compatibility with user {candidate.user_id}: {e}")
            continue

    # Sort by compatibility score and create top matches
    scored_candidates.sort(key=lambda x: x['score'], reverse=True)
    matches_created = 0

    for item in scored_candidates[:num_matches]:
        try:
            match = Match(
                user1_id=min(current_user.id, item['candidate'].user_id),
                user2_id=max(current_user.id, item['candidate'].user_id),
                status=MatchStatus.ACTIVE,
                ai_ice_breakers=item['ice_breakers'],
                compatibility_score=item['score'],
                compatibility_reasons=item['reasons']
            )
            db.add(match)
            db.flush()

            # Create notifications for both users
            notif1 = Notification(
                user_id=current_user.id,
                type="match",
                title="Welcome Match! 🎉",
                message=f"You matched with {item['candidate'].name}!",
                data={"match_id": match.id, "user_id": item['candidate'].user_id}
            )

            notif2 = Notification(
                user_id=item['candidate'].user_id,
                type="match",
                title="New Match! 💕",
                message=f"You matched with {user_profile.name}!",
                data={"match_id": match.id, "user_id": current_user.id}
            )

            db.add(notif1)
            db.add(notif2)
            matches_created += 1

        except Exception as e:
            print(f"Error creating match: {e}")
            continue

    db.commit()
    return matches_created


# ============================================================================
# Interests
# ============================================================================

@router.get("/interests/all", response_model=List[InterestBase])
async def get_all_interests(db: Session = Depends(get_db)):
    """Get all available interests"""
    interests = db.query(Interest).all()
    return interests


@router.post("/me/interests", response_model=ProfileInDB)
async def add_interests(
    interest_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add interests to current user's profile"""
    profile = current_user.profile

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    # Get interests
    interests = db.query(Interest).filter(Interest.id.in_(interest_ids)).all()

    if not interests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid interests found"
        )

    # Add interests (avoid duplicates)
    for interest in interests:
        if interest not in profile.interests:
            profile.interests.append(interest)

    # Update profile completion
    profile.profile_completion = calculate_profile_completion(profile)

    db.commit()
    db.refresh(profile)

    return profile


@router.delete("/me/interests/{interest_id}", response_model=ProfileInDB)
async def remove_interest(
    interest_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove interest from current user's profile"""
    profile = current_user.profile

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    # Find and remove interest
    interest = db.query(Interest).filter(Interest.id == interest_id).first()

    if interest and interest in profile.interests:
        profile.interests.remove(interest)
        db.commit()
        db.refresh(profile)

    return profile


# ============================================================================
# Photos
# ============================================================================


class PhotoUploadData(BaseModel):
    """Photo upload via base64 data URI"""
    data: str  # base64 data URI (e.g. "data:image/png;base64,...")
    is_primary: bool = False
    order: int = 0


@router.post("/me/photos/upload", response_model=PhotoBase)
async def upload_photo(
    upload_data: PhotoUploadData,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a photo from base64 data URI.
    Saves the file to disk and creates a Photo record.
    """
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    if len(profile.photos) >= 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 6 photos allowed")

    # Parse base64 data URI
    data_uri = upload_data.data
    if not data_uri.startswith("data:"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid data URI format")

    try:
        header, encoded = data_uri.split(",", 1)
        # e.g. "data:image/png;base64" -> "image/png"
        mime_type = header.split(":")[1].split(";")[0]
        ext_map = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        ext = ext_map.get(mime_type, ".jpg")
        image_data = base64.b64decode(encoded)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid base64 image data")

    # Validate file size (5MB max)
    if len(image_data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image too large. Max 5MB.")

    # Save file to disk
    filename = f"{uuid.uuid4().hex}{ext}"
    photos_dir = UPLOADS_DIR / "photos"
    photos_dir.mkdir(parents=True, exist_ok=True)
    filepath = photos_dir / filename
    filepath.write_bytes(image_data)

    # Build URL for the photo
    photo_url = f"/uploads/photos/{filename}"

    # Create Photo record
    new_photo = Photo(
        url=photo_url,
        thumbnail_url=photo_url,
        order=upload_data.order,
        is_primary=upload_data.is_primary,
    )
    db.add(new_photo)
    db.flush()

    profile.photos.append(new_photo)

    # If first photo or marked primary, set as primary
    if len(profile.photos) == 1 or upload_data.is_primary:
        for photo in profile.photos:
            if photo.id != new_photo.id:
                photo.is_primary = False
        new_photo.is_primary = True

    profile.profile_completion = calculate_profile_completion(profile)
    db.commit()
    db.refresh(new_photo)

    return new_photo


@router.post("/me/photos", response_model=PhotoBase)
async def add_photo(
    photo_data: PhotoCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add photo to current user's profile

    Note: In production, implement actual file upload to S3/CloudFlare
    For now, accepts URL directly
    """
    profile = current_user.profile

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    # Check photo limit (max 6 photos)
    if len(profile.photos) >= 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 6 photos allowed"
        )

    # Create photo
    new_photo = Photo(
        url=photo_data.url,
        thumbnail_url=photo_data.thumbnail_url,
        order=photo_data.order,
        is_primary=photo_data.is_primary
    )
    db.add(new_photo)
    db.flush()

    # Add to profile
    profile.photos.append(new_photo)

    # If this is the first photo or marked as primary, set as primary
    if len(profile.photos) == 1 or photo_data.is_primary:
        # Unset other primary photos
        for photo in profile.photos:
            if photo.id != new_photo.id:
                photo.is_primary = False
        new_photo.is_primary = True

    # Update profile completion
    profile.profile_completion = calculate_profile_completion(profile)

    db.commit()
    db.refresh(new_photo)

    return new_photo


@router.delete("/me/photos/{photo_id}")
async def delete_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete photo from current user's profile"""
    profile = current_user.profile

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    # Find photo
    photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if not photo or photo not in profile.photos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )

    # Remove from profile and delete
    profile.photos.remove(photo)
    db.delete(photo)
    db.commit()

    return {"message": "Photo deleted successfully"}


# ============================================================================
# Preferences
# ============================================================================

@router.get("/me/preferences", response_model=PreferenceBase)
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's dating preferences"""
    profile = current_user.profile

    if not profile or not profile.preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found"
        )

    return profile.preferences


@router.put("/me/preferences", response_model=PreferenceBase)
async def update_preferences(
    preference_data: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's dating preferences"""
    profile = current_user.profile

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    preferences = profile.preferences

    if not preferences:
        # Create preferences if they don't exist
        preferences = Preference(profile_id=profile.id)
        db.add(preferences)

    # Update fields
    update_data = preference_data.dict(exclude_unset=True)

    # Validate merged age range before persisting to avoid invalid state.
    merged_min_age = update_data.get("min_age", preferences.min_age)
    merged_max_age = update_data.get("max_age", preferences.max_age)
    if merged_max_age < merged_min_age:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="max_age must be greater than or equal to min_age"
        )

    for field, value in update_data.items():
        setattr(preferences, field, value)

    db.commit()
    db.refresh(preferences)

    return preferences


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_profile_completion(profile: Profile) -> int:
    """
    Calculate profile completion percentage

    Factors:
    - Basic info (name, DOB, gender): 20%
    - Bio: 15%
    - Occupation: 10%
    - Location: 10%
    - Photos (at least 2): 25%
    - Interests (at least 3): 20%
    """
    completion = 20  # Basic info always present

    if profile.bio:
        completion += 15

    if profile.occupation:
        completion += 10

    if profile.location:
        completion += 10

    if len(profile.photos) >= 2:
        completion += 25
    elif len(profile.photos) == 1:
        completion += 12

    if len(profile.interests) >= 3:
        completion += 20
    elif len(profile.interests) > 0:
        completion += 10

    return min(completion, 100)
