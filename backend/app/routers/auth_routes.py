"""
Authentication routes: register, login, logout
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import User, Profile, Preference, UserRole, Gender, Match, MatchStatus, Notification
from app.schemas import UserRegister, UserLogin, Token, UserInDB
from app.auth import (
    get_password_hash,
    authenticate_user,
    create_user_token,
    get_current_user,
    normalize_email
)
from app.services.ai_service import AIService
from datetime import timedelta
from sqlalchemy import and_, or_

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account

    - Creates user account with hashed password
    - Creates empty profile
    - Creates default preferences
    - Returns JWT access token
    """
    normalized_email = normalize_email(user_data.email)

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        # Create user
        new_user = User(
            email=normalized_email,
            password_hash=get_password_hash(user_data.password),
            role=UserRole.USER
        )
        db.add(new_user)
        db.flush()  # Get user ID without committing

        # Create profile
        new_profile = Profile(
            user_id=new_user.id,
            name=user_data.name,
            date_of_birth=user_data.date_of_birth,
            gender=user_data.gender,
            onboarding_completed=False,
            profile_completion=10  # Basic info completed
        )
        db.add(new_profile)
        db.flush()

        # Create default preferences (looking for all genders by default)
        default_preferences = Preference(
            profile_id=new_profile.id,
            min_age=18,
            max_age=99,
            looking_for=[g.value for g in Gender],
            max_distance=50
        )
        db.add(default_preferences)

        # Commit all changes
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

    # Auto-create initial matches so the user sees profiles immediately
    try:
        await create_initial_matches_for_user(new_user, db)
    except Exception as e:
        # Don't fail registration if auto-match fails
        print(f"Auto-match on registration failed (non-fatal): {e}")

    # Create access token
    access_token = create_user_token(new_user)

    return Token(
        access_token=access_token,
        user_id=new_user.id,
        role=new_user.role
    )


async def create_initial_matches_for_user(user: User, db: Session, num_matches: int = 5):
    """
    Create initial matches for a newly registered user.
    Finds compatible profiles and creates match records so the user
    can see matches immediately when they visit the matches tab.
    """
    user_profile = user.profile
    if not user_profile or not user_profile.preferences:
        return 0

    prefs = user_profile.preferences

    # Calculate age range
    min_birth_date = datetime.now().date() - timedelta(days=prefs.max_age * 365)
    max_birth_date = datetime.now().date() - timedelta(days=prefs.min_age * 365)

    # Normalize looking_for values
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

    # Find compatible profiles (demo users who completed onboarding)
    candidates = db.query(Profile).join(User).filter(
        Profile.user_id != user.id,
        User.is_active == True,
        Profile.onboarding_completed == True,
        Profile.date_of_birth.between(min_birth_date, max_birth_date),
        Profile.gender.in_(looking_for_values)
    ).limit(20).all()

    if not candidates:
        return 0

    # Score and create matches
    ai_service = AIService(db)
    scored = []

    for candidate in candidates:
        try:
            # Check no existing match
            existing = db.query(Match).filter(
                Match.user1_id == min(user.id, candidate.user_id),
                Match.user2_id == max(user.id, candidate.user_id)
            ).first()
            if existing:
                continue

            score, reasons, ice_breakers = await ai_service.calculate_compatibility(
                user_profile, candidate
            )
            scored.append({
                'candidate': candidate,
                'score': score,
                'reasons': reasons,
                'ice_breakers': ice_breakers
            })
        except Exception as e:
            print(f"Compatibility calc failed for user {candidate.user_id}: {e}")
            continue

    # Sort by score and create top matches
    scored.sort(key=lambda x: x['score'], reverse=True)
    matches_created = 0

    for item in scored[:num_matches]:
        try:
            match = Match(
                user1_id=min(user.id, item['candidate'].user_id),
                user2_id=max(user.id, item['candidate'].user_id),
                status=MatchStatus.ACTIVE,
                ai_ice_breakers=item['ice_breakers'],
                compatibility_score=item['score'],
                compatibility_reasons=item['reasons']
            )
            db.add(match)
            db.flush()

            # Notify both users
            db.add(Notification(
                user_id=user.id,
                type="match",
                title="New Match! 🎉",
                message=f"You matched with {item['candidate'].name}!",
                data={"match_id": match.id, "user_id": item['candidate'].user_id}
            ))
            db.add(Notification(
                user_id=item['candidate'].user_id,
                type="match",
                title="New Match! 💕",
                message=f"You matched with {user_profile.name}!",
                data={"match_id": match.id, "user_id": user.id}
            ))
            matches_created += 1
        except Exception as e:
            print(f"Error creating match: {e}")
            continue

    db.commit()
    print(f"Created {matches_created} initial matches for user {user.id}")
    return matches_created


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password

    - Authenticates user
    - Updates last_login timestamp
    - Returns JWT access token
    """
    # Authenticate user
    user = authenticate_user(db, credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token = create_user_token(user)

    return Token(
        access_token=access_token,
        user_id=user.id,
        role=user.role
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user

    Note: With JWT, we can't truly invalidate tokens on the server side.
    Client should discard the token.
    In production, implement token blacklist or use refresh tokens.
    """
    return {
        "message": "Successfully logged out",
        "detail": "Please discard your access token"
    }


@router.get("/me", response_model=UserInDB)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information
    """
    return current_user


@router.post("/verify-token")
async def verify_token(current_user: User = Depends(get_current_user)):
    """
    Verify if the provided token is valid

    Useful for frontend to check if user is still authenticated
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }
