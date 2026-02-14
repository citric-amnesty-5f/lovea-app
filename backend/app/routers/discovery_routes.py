"""
Discovery and matching routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, not_
from typing import List, Optional
from datetime import datetime, timedelta
import math

from app.database import get_db
from app.models import (
    User, Profile, Interaction, Match, Block,
    InteractionType, MatchStatus, Notification
)
from app.schemas import (
    ProfileDiscovery, InteractionCreate, InteractionResponse,
    MatchWithProfile, MatchBase
)
from app.auth import get_current_user
from app.services.ai_service import AIService

router = APIRouter(prefix="/discovery", tags=["Discovery & Matching"])


# ============================================================================
# Discovery
# ============================================================================

@router.get("/profiles", response_model=List[ProfileDiscovery])
async def get_discovery_profiles(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get profiles for discovery/swiping

    Returns profiles that:
    - Match user's preferences (age, gender, distance)
    - User hasn't interacted with yet
    - Are not blocked
    - Have completed onboarding
    """
    user_profile = current_user.profile

    if not user_profile or not user_profile.preferences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your profile and preferences first"
        )

    prefs = user_profile.preferences

    # Get users the current user has already interacted with
    interacted_ids = db.query(Interaction.to_user_id).filter(
        Interaction.from_user_id == current_user.id
    ).all()
    interacted_ids = [i[0] for i in interacted_ids]

    # Get blocked users
    blocked_ids = db.query(Block.blocked_id).filter(
        Block.blocker_id == current_user.id
    ).all()
    blocked_ids = [b[0] for b in blocked_ids]

    # Get users who blocked current user
    blocked_by_ids = db.query(Block.blocker_id).filter(
        Block.blocked_id == current_user.id
    ).all()
    blocked_by_ids = [b[0] for b in blocked_by_ids]

    # Calculate age range
    today = datetime.now()
    min_birth_date = today - timedelta(days=prefs.max_age * 365)
    max_birth_date = today - timedelta(days=prefs.min_age * 365)

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

    # Build query
    query = db.query(Profile).join(User).filter(
        # Exclude current user
        Profile.user_id != current_user.id,
        # Exclude interacted users
        Profile.user_id.not_in(interacted_ids + blocked_ids + blocked_by_ids),
        # Only active users
        User.is_active == True,
        # Onboarding completed
        Profile.onboarding_completed == True,
        # Age range
        Profile.date_of_birth.between(min_birth_date, max_birth_date),
        # Gender preference
        Profile.gender.in_(looking_for_values)
    )

    # Get candidates
    candidates = query.limit(limit * 3).all()  # Get more for AI filtering

    if not candidates:
        return []

    # Convert to ProfileDiscovery with AI scoring
    ai_service = AIService(db)
    discovery_profiles = []

    for candidate in candidates[:limit]:
        # Calculate distance if both have coordinates
        distance = None
        if (user_profile.latitude and user_profile.longitude and
            candidate.latitude and candidate.longitude):
            distance = calculate_distance(
                user_profile.latitude, user_profile.longitude,
                candidate.latitude, candidate.longitude
            )

        # Calculate age
        age = (today.year - candidate.date_of_birth.year -
               ((today.month, today.day) <
                (candidate.date_of_birth.month, candidate.date_of_birth.day)))

        # Get AI compatibility (async, could be moved to background task)
        try:
            score, reasons, _ = await ai_service.calculate_compatibility(
                user_profile, candidate
            )
        except:
            score = None
            reasons = None

        discovery_profile = ProfileDiscovery(
            id=candidate.id,
            name=candidate.name,
            age=age,
            gender=candidate.gender,
            bio=candidate.bio,
            occupation=candidate.occupation,
            location=candidate.location,
            distance=distance,
            photos=candidate.photos,
            interests=candidate.interests,
            ai_compatibility_score=score,
            ai_compatibility_reasons=reasons
        )

        discovery_profiles.append(discovery_profile)

    # Sort by AI compatibility if available
    discovery_profiles.sort(
        key=lambda x: x.ai_compatibility_score or 0,
        reverse=True
    )

    return discovery_profiles


# ============================================================================
# Interactions (Like, Pass, Super Like)
# ============================================================================

@router.post("/interact", response_model=InteractionResponse)
async def create_interaction(
    interaction_data: InteractionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create interaction (like, pass, super like)

    Automatically creates match if mutual like
    """
    # Check if target user exists
    target_profile = db.query(Profile).filter(
        Profile.user_id == interaction_data.to_user_id
    ).first()

    if not target_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if already interacted
    existing = db.query(Interaction).filter(
        Interaction.from_user_id == current_user.id,
        Interaction.to_user_id == interaction_data.to_user_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already interacted with this user"
        )

    # Get AI compatibility score if like/super_like
    ai_score = None
    if interaction_data.interaction_type in [InteractionType.LIKE, InteractionType.SUPER_LIKE]:
        ai_service = AIService(db)
        try:
            score, reasons, ice_breakers = await ai_service.calculate_compatibility(
                current_user.profile, target_profile
            )
            ai_score = score
        except:
            pass

    # Create interaction
    interaction = Interaction(
        from_user_id=current_user.id,
        to_user_id=interaction_data.to_user_id,
        interaction_type=interaction_data.interaction_type,
        ai_compatibility_score=ai_score
    )
    db.add(interaction)
    db.flush()

    # Update profile stats
    if interaction_data.interaction_type == InteractionType.LIKE:
        target_profile.total_likes += 1
    elif interaction_data.interaction_type == InteractionType.SUPER_LIKE:
        target_profile.total_super_likes += 1

    # Check for match (mutual like)
    is_match = False
    match_id = None

    if interaction_data.interaction_type in [InteractionType.LIKE, InteractionType.SUPER_LIKE]:
        # Check if other user liked back
        mutual_like = db.query(Interaction).filter(
            Interaction.from_user_id == interaction_data.to_user_id,
            Interaction.to_user_id == current_user.id,
            Interaction.interaction_type.in_([InteractionType.LIKE, InteractionType.SUPER_LIKE])
        ).first()

        if mutual_like:
            # Create match
            is_match = True

            # Get AI ice breakers
            ai_service = AIService(db)
            try:
                ice_breakers = await ai_service.generate_ice_breakers(
                    current_user.profile, target_profile
                )
                compatibility_score = ai_score
                compatibility_reasons = reasons if ai_score else []
            except:
                ice_breakers = []
                compatibility_score = None
                compatibility_reasons = []

            match = Match(
                user1_id=min(current_user.id, interaction_data.to_user_id),
                user2_id=max(current_user.id, interaction_data.to_user_id),
                status=MatchStatus.ACTIVE,
                ai_ice_breakers=ice_breakers,
                compatibility_score=compatibility_score,
                compatibility_reasons=compatibility_reasons
            )
            db.add(match)
            db.flush()
            match_id = match.id

            # Update match counts
            current_user.profile.total_matches += 1
            target_profile.total_matches += 1

            # Create notifications for both users
            notif1 = Notification(
                user_id=current_user.id,
                type="match",
                title="It's a Match! 🎉",
                message=f"You and {target_profile.name} liked each other!",
                data={"match_id": match.id, "user_id": interaction_data.to_user_id}
            )
            notif2 = Notification(
                user_id=interaction_data.to_user_id,
                type="match",
                title="It's a Match! 🎉",
                message=f"You and {current_user.profile.name} liked each other!",
                data={"match_id": match.id, "user_id": current_user.id}
            )
            db.add(notif1)
            db.add(notif2)

    db.commit()
    db.refresh(interaction)

    return InteractionResponse(
        id=interaction.id,
        to_user_id=interaction.to_user_id,
        interaction_type=interaction.interaction_type,
        is_match=is_match,
        match_id=match_id,
        ai_compatibility_score=ai_score,
        created_at=interaction.created_at
    )


# ============================================================================
# Matches
# ============================================================================

@router.get("/matches", response_model=List[MatchWithProfile])
async def get_my_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active matches for current user"""

    # Get matches
    matches = db.query(Match).filter(
        or_(
            Match.user1_id == current_user.id,
            Match.user2_id == current_user.id
        ),
        Match.status == MatchStatus.ACTIVE
    ).all()

    result = []
    today = datetime.now()

    for match in matches:
        # Get other user's profile
        other_user_id = match.user2_id if match.user1_id == current_user.id else match.user1_id
        other_profile = db.query(Profile).filter(Profile.user_id == other_user_id).first()

        if not other_profile:
            continue

        # Calculate age
        age = (today.year - other_profile.date_of_birth.year -
               ((today.month, today.day) <
                (other_profile.date_of_birth.month, other_profile.date_of_birth.day)))

        # Build response
        match_response = MatchWithProfile(
            id=match.id,
            user1_id=match.user1_id,
            user2_id=match.user2_id,
            status=match.status,
            compatibility_score=match.compatibility_score,
            compatibility_reasons=match.compatibility_reasons,
            ai_ice_breakers=match.ai_ice_breakers,
            created_at=match.created_at,
            other_user_profile=ProfileDiscovery(
                id=other_profile.id,
                name=other_profile.name,
                age=age,
                gender=other_profile.gender,
                bio=other_profile.bio,
                occupation=other_profile.occupation,
                location=other_profile.location,
                distance=None,
                photos=other_profile.photos,
                interests=other_profile.interests
            )
        )

        result.append(match_response)

    # Sort by creation date (newest first)
    result.sort(key=lambda x: x.created_at, reverse=True)

    return result


@router.delete("/matches/{match_id}")
async def unmatch(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unmatch with a user"""

    match = db.query(Match).filter(
        Match.id == match_id,
        or_(
            Match.user1_id == current_user.id,
            Match.user2_id == current_user.id
        )
    ).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    # Update status instead of deleting (for data retention)
    match.status = MatchStatus.UNMATCHED
    db.commit()

    return {"message": "Unmatched successfully"}


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates in kilometers
    Using Haversine formula
    """
    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c

    return round(distance, 1)
