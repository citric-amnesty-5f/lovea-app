"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, date
from typing import Optional, List
from app.models import UserRole, Gender, InteractionType, MatchStatus, MessageStatus


# ============================================================================
# Auth Schemas
# ============================================================================

class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: date
    gender: Gender

    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

    @validator('date_of_birth')
    def check_age(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError('Must be at least 18 years old')
        if age > 100:
            raise ValueError('Invalid date of birth')
        return v


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: UserRole


class TokenData(BaseModel):
    """Data stored in JWT token"""
    user_id: int
    email: str
    role: UserRole


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserCreate(UserBase):
    """User creation schema"""
    password: str


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """User in database"""
    id: int
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Profile Schemas
# ============================================================================

class InterestBase(BaseModel):
    """Interest schema"""
    id: int
    name: str
    category: Optional[str]
    icon: Optional[str]

    class Config:
        from_attributes = True


class PhotoBase(BaseModel):
    """Photo schema"""
    id: int
    url: str
    thumbnail_url: Optional[str]
    order: int
    is_primary: bool

    class Config:
        from_attributes = True


class PhotoCreate(BaseModel):
    """Photo creation schema"""
    url: str
    thumbnail_url: Optional[str] = None
    order: int = 0
    is_primary: bool = False


class PreferenceBase(BaseModel):
    """Preference schema"""
    min_age: int = Field(18, ge=18, le=99)
    max_age: int = Field(99, ge=18, le=99)
    looking_for: List[Gender]
    max_distance: int = Field(50, ge=1, le=500)
    show_me: str = "everyone"

    @validator('max_age')
    def max_age_greater_than_min(cls, v, values):
        if 'min_age' in values and v < values['min_age']:
            raise ValueError('max_age must be greater than or equal to min_age')
        return v

    class Config:
        from_attributes = True


class PreferenceCreate(PreferenceBase):
    """Preference creation schema"""
    pass


class PreferenceUpdate(BaseModel):
    """Preference update schema"""
    min_age: Optional[int] = Field(None, ge=18, le=99)
    max_age: Optional[int] = Field(None, ge=18, le=99)
    looking_for: Optional[List[Gender]] = None
    max_distance: Optional[int] = Field(None, ge=1, le=500)
    show_me: Optional[str] = None


class ProfileBase(BaseModel):
    """Base profile schema"""
    name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: date
    gender: Gender
    bio: Optional[str] = Field(None, max_length=500)
    occupation: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    school: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    height: Optional[int] = Field(None, ge=100, le=250)


class ProfileCreate(ProfileBase):
    """Profile creation schema"""
    interest_ids: Optional[List[int]] = []


class ProfileUpdate(BaseModel):
    """Profile update schema"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    occupation: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    school: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    height: Optional[int] = Field(None, ge=100, le=250)
    show_online: Optional[bool] = None
    show_age: Optional[bool] = None
    show_distance: Optional[bool] = None


class ProfileInDB(ProfileBase):
    """Profile in database"""
    id: int
    user_id: int
    onboarding_completed: bool
    profile_completion: int
    total_likes: int
    total_super_likes: int
    total_matches: int
    interests: List[InterestBase] = []
    photos: List[PhotoBase] = []
    preferences: Optional[PreferenceBase] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileDiscovery(BaseModel):
    """Profile for discovery/browsing"""
    id: int
    name: str
    age: int
    gender: Gender
    bio: Optional[str]
    occupation: Optional[str]
    location: Optional[str]
    distance: Optional[float]  # in km
    photos: List[PhotoBase]
    interests: List[InterestBase]
    ai_compatibility_score: Optional[float] = None
    ai_compatibility_reasons: Optional[List[str]] = None

    class Config:
        from_attributes = True


# ============================================================================
# Interaction Schemas
# ============================================================================

class InteractionCreate(BaseModel):
    """Create interaction (like/pass)"""
    to_user_id: int
    interaction_type: InteractionType


class InteractionResponse(BaseModel):
    """Interaction response"""
    id: int
    to_user_id: int
    interaction_type: InteractionType
    is_match: bool
    match_id: Optional[int] = None
    ai_compatibility_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Match Schemas
# ============================================================================

class MatchBase(BaseModel):
    """Match schema"""
    id: int
    user1_id: int
    user2_id: int
    status: MatchStatus
    compatibility_score: Optional[float]
    compatibility_reasons: Optional[List[str]]
    ai_ice_breakers: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class MatchWithProfile(MatchBase):
    """Match with other user's profile"""
    other_user_profile: ProfileDiscovery


# ============================================================================
# Message Schemas
# ============================================================================

class MessageCreate(BaseModel):
    """Create message"""
    match_id: int
    content: str = Field(..., min_length=1, max_length=2000)


class MessageResponse(BaseModel):
    """Message response"""
    id: int
    match_id: int
    sender_id: int
    receiver_id: int
    content: str
    status: MessageStatus
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation with messages"""
    match: MatchBase
    messages: List[MessageResponse]
    unread_count: int


# ============================================================================
# Notification Schemas
# ============================================================================

class NotificationResponse(BaseModel):
    """Notification response"""
    id: int
    type: str
    title: str
    message: Optional[str]
    data: Optional[dict]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Admin Schemas
# ============================================================================

class ReportResponse(BaseModel):
    """Report response for admin"""
    id: int
    reporter_id: int
    reported_id: int
    reason: str
    description: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """User statistics for admin"""
    total_users: int
    active_users: int
    verified_users: int
    total_matches: int
    total_messages: int
    new_users_today: int
    new_matches_today: int


class AIStats(BaseModel):
    """AI usage statistics"""
    total_api_calls: int
    total_tokens: int
    total_cost: float
    calls_by_operation: dict
    average_response_time: float


# ============================================================================
# AI Schemas
# ============================================================================

class AIMatchRequest(BaseModel):
    """Request AI matchmaking"""
    profile_id: int
    candidate_profile_ids: List[int]


class AIMatchResponse(BaseModel):
    """AI matchmaking response"""
    profile_id: int
    compatibility_score: float
    reasons: List[str]
    conversation_starters: List[str]


class AIBioRequest(BaseModel):
    """Request AI bio generation"""
    occupation: Optional[str]
    interests: List[str]
    personality_traits: Optional[List[str]]


class AIBioResponse(BaseModel):
    """AI bio generation response"""
    bio_suggestions: List[str]
    bio_score: float
    tips: List[str]
