"""
Admin routes with role-based access control
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import (
    User, Profile, Match, Message, Report, AILog,
    Interaction, Block, UserRole
)
from app.schemas import (
    UserInDB, ReportResponse, UserStats, AIStats
)
from app.auth import get_current_user, require_admin, require_moderator

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================================================
# User Management
# ============================================================================

@router.get("/users", response_model=List[UserInDB], dependencies=[Depends(require_admin)])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None,
    role: Optional[UserRole] = None,
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""

    query = db.query(User)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if role is not None:
        query = query.filter(User.role == role)

    users = query.offset(skip).limit(limit).all()

    return users


@router.get("/users/{user_id}", response_model=UserInDB, dependencies=[Depends(require_admin)])
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only)"""

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.put("/users/{user_id}/activate", dependencies=[Depends(require_admin)])
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Activate a user account (admin only)"""

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = True
    db.commit()

    return {"message": f"User {user_id} activated successfully"}


@router.put("/users/{user_id}/deactivate", dependencies=[Depends(require_admin)])
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate a user account (admin only)"""

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = False
    db.commit()

    return {"message": f"User {user_id} deactivated successfully"}


@router.put("/users/{user_id}/role", dependencies=[Depends(require_admin)])
async def change_user_role(
    user_id: int,
    new_role: UserRole,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user role (admin only)"""

    # Prevent self-demotion
    if user_id == current_user.id and new_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.role = new_role
    db.commit()

    return {"message": f"User {user_id} role changed to {new_role.value}"}


@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user account (admin only)

    WARNING: This will cascade delete all related data
    """
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(user)
    db.commit()

    return {"message": f"User {user_id} deleted successfully"}


# ============================================================================
# Reports Management
# ============================================================================

@router.get("/reports", response_model=List[ReportResponse], dependencies=[Depends(require_moderator)])
async def get_reports(
    status: Optional[str] = Query(None, regex="^(pending|reviewed|resolved)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get user reports (moderator/admin only)"""

    query = db.query(Report)

    if status:
        query = query.filter(Report.status == status)

    reports = query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()

    return reports


@router.get("/reports/{report_id}", response_model=ReportResponse, dependencies=[Depends(require_moderator)])
async def get_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """Get specific report (moderator/admin only)"""

    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    return report


@router.put("/reports/{report_id}/resolve", dependencies=[Depends(require_moderator)])
async def resolve_report(
    report_id: int,
    admin_notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve a report (moderator/admin only)"""

    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    report.status = "resolved"
    report.resolved_at = datetime.utcnow()
    if admin_notes:
        report.admin_notes = admin_notes

    db.commit()

    return {"message": f"Report {report_id} resolved"}


# ============================================================================
# Statistics
# ============================================================================

@router.get("/stats/users", response_model=UserStats, dependencies=[Depends(require_admin)])
async def get_user_stats(db: Session = Depends(get_db)):
    """Get user statistics (admin only)"""

    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    verified_users = db.query(func.count(User.id)).filter(User.is_verified == True).scalar()

    total_matches = db.query(func.count(Match.id)).scalar()
    total_messages = db.query(func.count(Message.id)).scalar()

    # New users today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    new_users_today = db.query(func.count(User.id)).filter(
        User.created_at >= today_start
    ).scalar()

    # New matches today
    new_matches_today = db.query(func.count(Match.id)).filter(
        Match.created_at >= today_start
    ).scalar()

    return UserStats(
        total_users=total_users,
        active_users=active_users,
        verified_users=verified_users,
        total_matches=total_matches,
        total_messages=total_messages,
        new_users_today=new_users_today,
        new_matches_today=new_matches_today
    )


@router.get("/stats/ai", response_model=AIStats, dependencies=[Depends(require_admin)])
async def get_ai_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """Get AI usage statistics (admin only)"""

    # Date range
    since = datetime.utcnow() - timedelta(days=days)

    # Total API calls
    total_calls = db.query(func.count(AILog.id)).filter(
        AILog.created_at >= since
    ).scalar()

    # Total tokens
    total_tokens = db.query(func.sum(AILog.total_tokens)).filter(
        AILog.created_at >= since
    ).scalar() or 0

    # Total cost
    total_cost = db.query(func.sum(AILog.cost)).filter(
        AILog.created_at >= since
    ).scalar() or 0.0

    # Calls by operation
    calls_by_op = db.query(
        AILog.operation,
        func.count(AILog.id).label('count')
    ).filter(
        AILog.created_at >= since
    ).group_by(AILog.operation).all()

    calls_by_operation = {op: count for op, count in calls_by_op}

    # Average response time (if we had timing data)
    avg_response_time = 0.0  # Placeholder

    return AIStats(
        total_api_calls=total_calls,
        total_tokens=total_tokens,
        total_cost=round(total_cost, 2),
        calls_by_operation=calls_by_operation,
        average_response_time=avg_response_time
    )


# ============================================================================
# Content Moderation
# ============================================================================

@router.get("/moderation/flagged-messages", dependencies=[Depends(require_moderator)])
async def get_flagged_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get flagged messages for review (moderator/admin only)"""

    messages = db.query(Message).filter(
        Message.is_flagged == True
    ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()

    return messages


@router.delete("/moderation/messages/{message_id}", dependencies=[Depends(require_moderator)])
async def delete_message(
    message_id: int,
    db: Session = Depends(get_db)
):
    """Delete a message (moderator/admin only)"""

    message = db.query(Message).filter(Message.id == message_id).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    db.delete(message)
    db.commit()

    return {"message": f"Message {message_id} deleted"}


# ============================================================================
# Activity Monitoring
# ============================================================================

@router.get("/activity/recent-logins", dependencies=[Depends(require_admin)])
async def get_recent_logins(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get recent user logins (admin only)"""

    users = db.query(User).filter(
        User.last_login.isnot(None)
    ).order_by(User.last_login.desc()).limit(limit).all()

    return [
        {
            "user_id": user.id,
            "email": user.email,
            "last_login": user.last_login,
            "role": user.role.value
        }
        for user in users
    ]


@router.get("/activity/popular-interests", dependencies=[Depends(require_admin)])
async def get_popular_interests(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get most popular interests (admin only)"""

    from app.models import Interest, user_interests

    # Query interests with user count
    popular = db.query(
        Interest.name,
        func.count(user_interests.c.user_id).label('user_count')
    ).join(
        user_interests,
        Interest.id == user_interests.c.interest_id
    ).group_by(
        Interest.id, Interest.name
    ).order_by(
        func.count(user_interests.c.user_id).desc()
    ).limit(limit).all()

    return [
        {"interest": name, "user_count": count}
        for name, count in popular
    ]


@router.get("/activity/match-rate", dependencies=[Depends(require_admin)])
async def get_match_rate(db: Session = Depends(get_db)):
    """Calculate overall match rate (admin only)"""

    total_likes = db.query(func.count(Interaction.id)).filter(
        or_(
            Interaction.interaction_type == "like",
            Interaction.interaction_type == "super_like"
        )
    ).scalar()

    total_matches = db.query(func.count(Match.id)).scalar()

    match_rate = (total_matches / total_likes * 100) if total_likes > 0 else 0

    return {
        "total_likes": total_likes,
        "total_matches": total_matches,
        "match_rate_percent": round(match_rate, 2)
    }
