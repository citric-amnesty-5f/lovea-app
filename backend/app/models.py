"""
Database models for LoveAI dating app
SQLAlchemy models with PostgreSQL
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Boolean, Column, Integer, String, DateTime, Date, Text,
    Float, ForeignKey, JSON, Enum as SQLEnum, Table
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


# Association tables for many-to-many relationships
user_interests = Table(
    'user_interests',
    Base.metadata,
    Column('profile_id', Integer, ForeignKey('profiles.id', ondelete='CASCADE')),
    Column('interest_id', Integer, ForeignKey('interests.id', ondelete='CASCADE'))
)

user_photos = Table(
    'user_photos',
    Base.metadata,
    Column('profile_id', Integer, ForeignKey('profiles.id', ondelete='CASCADE')),
    Column('photo_id', Integer, ForeignKey('photos.id', ondelete='CASCADE'))
)


# Enums
class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    OTHER = "other"


class InteractionType(str, enum.Enum):
    LIKE = "like"
    PASS = "pass"
    SUPER_LIKE = "super_like"


class MatchStatus(str, enum.Enum):
    ACTIVE = "active"
    UNMATCHED = "unmatched"
    BLOCKED = "blocked"


class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


# Models
class User(Base):
    """User account model with authentication"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sent_interactions = relationship("Interaction", foreign_keys="Interaction.from_user_id", back_populates="from_user", cascade="all, delete-orphan")
    received_interactions = relationship("Interaction", foreign_keys="Interaction.to_user_id", back_populates="to_user", cascade="all, delete-orphan")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender", cascade="all, delete-orphan")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver", cascade="all, delete-orphan")
    matches_as_user1 = relationship("Match", foreign_keys="Match.user1_id", back_populates="user1", cascade="all, delete-orphan")
    matches_as_user2 = relationship("Match", foreign_keys="Match.user2_id", back_populates="user2", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    blocks_initiated = relationship("Block", foreign_keys="Block.blocker_id", back_populates="blocker", cascade="all, delete-orphan")
    blocks_received = relationship("Block", foreign_keys="Block.blocked_id", back_populates="blocked", cascade="all, delete-orphan")
    reports_made = relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter", cascade="all, delete-orphan")
    reports_received = relationship("Report", foreign_keys="Report.reported_id", back_populates="reported", cascade="all, delete-orphan")


class Profile(Base):
    """User dating profile"""
    __tablename__ = 'profiles'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Basic info
    name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(SQLEnum(Gender), nullable=False)
    bio = Column(Text)
    occupation = Column(String(100))
    company = Column(String(100))
    school = Column(String(100))

    # Location
    location = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)

    # Physical attributes
    height = Column(Integer)  # in cm

    # Profile completion
    onboarding_completed = Column(Boolean, default=False)
    profile_completion = Column(Integer, default=0)  # 0-100%

    # Settings
    show_online = Column(Boolean, default=True)
    show_age = Column(Boolean, default=True)
    show_distance = Column(Boolean, default=True)

    # AI matching data
    personality_traits = Column(JSON)  # Store AI-analyzed personality
    ai_bio_score = Column(Float)  # AI evaluation of bio quality

    # Stats
    total_likes = Column(Integer, default=0)
    total_super_likes = Column(Integer, default=0)
    total_matches = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="profile")
    interests = relationship("Interest", secondary=user_interests, back_populates="users")
    photos = relationship("Photo", secondary=user_photos, back_populates="users", order_by="Photo.order")
    preferences = relationship("Preference", back_populates="profile", uselist=False, cascade="all, delete-orphan")


class Interest(Base):
    """User interests/hobbies"""
    __tablename__ = 'interests'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))  # sports, arts, music, etc.
    icon = Column(String(50))  # emoji or icon reference

    # Relationships
    users = relationship("Profile", secondary=user_interests, back_populates="interests")


class Photo(Base):
    """User photos"""
    __tablename__ = 'photos'

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False)  # S3 or CDN URL
    thumbnail_url = Column(String(500))
    order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # AI moderation
    ai_moderation_score = Column(Float)  # Content safety score
    is_approved = Column(Boolean, default=False)

    # Relationships
    users = relationship("Profile", secondary=user_photos, back_populates="photos")


class Preference(Base):
    """User dating preferences"""
    __tablename__ = 'preferences'

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Age preferences
    min_age = Column(Integer, default=18)
    max_age = Column(Integer, default=99)

    # Gender preferences
    looking_for = Column(JSON)  # Array of genders

    # Distance preferences
    max_distance = Column(Integer, default=50)  # in km

    # Other preferences
    show_me = Column(String(50), default='everyone')  # everyone, new_profiles, active_users

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    profile = relationship("Profile", back_populates="preferences")


class Interaction(Base):
    """User interactions (likes, passes, super likes)"""
    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    to_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    interaction_type = Column(SQLEnum(InteractionType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # AI data
    ai_compatibility_score = Column(Float)  # AI-calculated compatibility
    ai_reasoning = Column(Text)  # Why the AI thinks they're compatible

    # Relationships
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="sent_interactions")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="received_interactions")


class Match(Base):
    """Mutual matches between users"""
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user2_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.ACTIVE)

    # AI-generated conversation starters
    ai_ice_breakers = Column(JSON)  # Array of AI-generated conversation starters

    # Match quality
    compatibility_score = Column(Float)  # 0-100
    compatibility_reasons = Column(JSON)  # Array of reasons why they matched

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id], back_populates="matches_as_user1")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="matches_as_user2")
    messages = relationship("Message", back_populates="match", cascade="all, delete-orphan")


class Message(Base):
    """Chat messages between matched users"""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey('matches.id', ondelete='CASCADE'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    content = Column(Text, nullable=False)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.SENT)

    # AI moderation
    ai_safety_score = Column(Float)  # Content safety score
    is_flagged = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True))

    # Relationships
    match = relationship("Match", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")


class Notification(Base):
    """User notifications"""
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    type = Column(String(50), nullable=False)  # match, message, like, super_like
    title = Column(String(255), nullable=False)
    message = Column(Text)
    data = Column(JSON)  # Additional data (user_id, match_id, etc.)

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")


class Block(Base):
    """Blocked users"""
    __tablename__ = 'blocks'

    id = Column(Integer, primary_key=True, index=True)
    blocker_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    blocked_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    blocker = relationship("User", foreign_keys=[blocker_id], back_populates="blocks_initiated")
    blocked = relationship("User", foreign_keys=[blocked_id], back_populates="blocks_received")


class Report(Base):
    """User reports"""
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reported_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    reason = Column(String(100), nullable=False)  # inappropriate, spam, fake, etc.
    description = Column(Text)
    evidence = Column(JSON)  # Screenshots, message IDs, etc.

    status = Column(String(50), default='pending')  # pending, reviewed, resolved
    admin_notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reports_made")
    reported = relationship("User", foreign_keys=[reported_id], back_populates="reports_received")


class AILog(Base):
    """Log AI API calls for monitoring and cost tracking"""
    __tablename__ = 'ai_logs'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))

    operation = Column(String(100), nullable=False)  # matchmaking, bio_generation, etc.
    model = Column(String(50))  # gpt-4, gpt-3.5-turbo, etc.
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost = Column(Float)

    request_data = Column(JSON)
    response_data = Column(JSON)

    success = Column(Boolean, default=True)
    error_message = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
