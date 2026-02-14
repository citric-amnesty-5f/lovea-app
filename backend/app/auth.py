"""
Authentication utilities: JWT, password hashing, role-based access
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.models import User, UserRole
from app.schemas import TokenData

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ============================================================================
# Password Functions
# ============================================================================

def normalize_email(email: str) -> str:
    """Normalize email for consistent lookup and uniqueness checks."""
    return email.strip().lower()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


# ============================================================================
# JWT Functions
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Dictionary with user data (user_id, email, role)
        expires_delta: Optional expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    issued_at = datetime.now(timezone.utc)
    if expires_delta:
        expire = issued_at + expires_delta
    else:
        expire = issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Include iat/jti so multiple logins in the same second still produce unique tokens.
    to_encode.update({"exp": expire, "iat": issued_at, "jti": uuid4().hex})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode a JWT access token

    Args:
        token: JWT token string

    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if user_id is None or email is None or role is None:
            return None

        return TokenData(user_id=user_id, email=email, role=UserRole(role))

    except JWTError:
        return None


# ============================================================================
# Authentication Dependencies
# ============================================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token

    Usage:
        current_user: User = Depends(get_current_user)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (alias for get_current_user)
    """
    return current_user


# ============================================================================
# Role-Based Access Control
# ============================================================================

class RoleChecker:
    """
    Role-based access control dependency

    Usage:
        @router.get("/admin-only", dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
    """

    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {[r.value for r in self.allowed_roles]}"
            )
        return user


# Role checker instances for convenience
require_admin = RoleChecker([UserRole.ADMIN])
require_moderator = RoleChecker([UserRole.ADMIN, UserRole.MODERATOR])


# ============================================================================
# User Authentication Functions
# ============================================================================

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user with email and password

    Args:
        db: Database session
        email: User email
        password: Plain text password

    Returns:
        User if authenticated, None otherwise
    """
    user = db.query(User).filter(User.email == normalize_email(email)).first()

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def create_user_token(user: User) -> str:
    """
    Create access token for a user

    Args:
        user: User object

    Returns:
        JWT access token
    """
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value
        }
    )

    return access_token


# ============================================================================
# Permission Helpers
# ============================================================================

def can_access_profile(user: User, profile_user_id: int) -> bool:
    """
    Check if user can access a profile

    Args:
        user: Current user
        profile_user_id: Target profile's user ID

    Returns:
        True if user can access, False otherwise
    """
    # User can access their own profile
    if user.id == profile_user_id:
        return True

    # Admin can access any profile
    if user.role == UserRole.ADMIN:
        return True

    return False


def can_modify_user(user: User, target_user_id: int) -> bool:
    """
    Check if user can modify another user

    Args:
        user: Current user
        target_user_id: Target user ID

    Returns:
        True if user can modify, False otherwise
    """
    # User can modify themselves
    if user.id == target_user_id:
        return True

    # Admin can modify any user
    if user.role == UserRole.ADMIN:
        return True

    return False


def require_ownership_or_admin(user: User, resource_user_id: int):
    """
    Raise exception if user doesn't own resource and isn't admin

    Args:
        user: Current user
        resource_user_id: Resource owner's user ID

    Raises:
        HTTPException: If user lacks permission
    """
    if user.id != resource_user_id and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )
