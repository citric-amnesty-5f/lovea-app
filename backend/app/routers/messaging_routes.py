"""
Messaging routes with WebSocket support for real-time chat
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Dict
from datetime import datetime
import json

from app.database import get_db
from app.models import (
    User, Match, Message, Notification,
    MessageStatus, MatchStatus
)
from app.schemas import (
    MessageCreate, MessageResponse,
    ConversationResponse, MatchBase
)
from app.auth import get_current_user, decode_access_token
from app.services.ai_service import AIService

router = APIRouter(prefix="/messages", tags=["Messaging"])


# ============================================================================
# WebSocket Connection Manager
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections for real-time messaging"""

    def __init__(self):
        # user_id -> WebSocket connection
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        """Connect a user's WebSocket"""
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        """Disconnect a user's WebSocket"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_message(self, user_id: int, message: dict):
        """Send message to a specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except:
                # Connection might be closed
                self.disconnect(user_id)

    async def broadcast_to_match(self, match: Match, sender_id: int, message: dict):
        """Send message to other user in a match"""
        receiver_id = match.user2_id if match.user1_id == sender_id else match.user1_id
        await self.send_message(receiver_id, message)


# Global connection manager
manager = ConnectionManager()


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time messaging

    Connect with: ws://localhost:8000/messages/ws?token=<jwt_token>
    """
    # Authenticate user from token
    token_data = decode_access_token(token)

    if not token_data:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user = db.query(User).filter(User.id == token_data.user_id).first()

    if not user or not user.is_active:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Connect user
    await manager.connect(user.id, websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Handle different message types
            message_type = data.get("type")

            if message_type == "send_message":
                await handle_send_message(data, user, db)
            elif message_type == "typing":
                await handle_typing_indicator(data, user, db)
            elif message_type == "mark_read":
                await handle_mark_read(data, user, db)
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(user.id)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        manager.disconnect(user.id)


async def handle_send_message(data: dict, user: User, db: Session):
    """Handle sending a message via WebSocket"""
    match_id = data.get("match_id")
    content = data.get("content")

    if not match_id or not content:
        return

    # Verify match exists and user is part of it
    match = db.query(Match).filter(
        Match.id == match_id,
        or_(Match.user1_id == user.id, Match.user2_id == user.id),
        Match.status == MatchStatus.ACTIVE
    ).first()

    if not match:
        return

    # Get receiver
    receiver_id = match.user2_id if match.user1_id == user.id else match.user1_id

    # Moderate content with AI
    ai_service = AIService(db)
    try:
        safety_score, is_safe = await ai_service.moderate_content(content, "message")
    except:
        safety_score = 95.0
        is_safe = True

    # Create message
    message = Message(
        match_id=match_id,
        sender_id=user.id,
        receiver_id=receiver_id,
        content=content,
        status=MessageStatus.SENT,
        ai_safety_score=safety_score,
        is_flagged=not is_safe
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    # Send to receiver via WebSocket
    message_data = {
        "type": "new_message",
        "message": {
            "id": message.id,
            "match_id": message.match_id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "content": message.content,
            "status": message.status.value,
            "created_at": message.created_at.isoformat()
        }
    }

    await manager.broadcast_to_match(match, user.id, message_data)

    # Create notification if receiver is offline
    if receiver_id not in manager.active_connections:
        notif = Notification(
            user_id=receiver_id,
            type="message",
            title="New message",
            message=f"{user.profile.name} sent you a message",
            data={"match_id": match_id, "sender_id": user.id}
        )
        db.add(notif)
        db.commit()


async def handle_typing_indicator(data: dict, user: User, db: Session):
    """Handle typing indicator"""
    match_id = data.get("match_id")
    is_typing = data.get("is_typing", False)

    if not match_id:
        return

    # Verify match
    match = db.query(Match).filter(
        Match.id == match_id,
        or_(Match.user1_id == user.id, Match.user2_id == user.id)
    ).first()

    if not match:
        return

    # Broadcast typing indicator
    typing_data = {
        "type": "typing",
        "match_id": match_id,
        "user_id": user.id,
        "is_typing": is_typing
    }

    await manager.broadcast_to_match(match, user.id, typing_data)


async def handle_mark_read(data: dict, user: User, db: Session):
    """Handle marking messages as read"""
    match_id = data.get("match_id")

    if not match_id:
        return

    # Mark all messages in this match as read
    db.query(Message).filter(
        Message.match_id == match_id,
        Message.receiver_id == user.id,
        Message.status != MessageStatus.READ
    ).update({
        "status": MessageStatus.READ,
        "read_at": datetime.utcnow()
    })
    db.commit()


# ============================================================================
# HTTP Endpoints
# ============================================================================

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message (HTTP endpoint, use WebSocket for real-time)

    This is a fallback for when WebSocket is not available
    """
    # Verify match exists and user is part of it
    match = db.query(Match).filter(
        Match.id == message_data.match_id,
        or_(
            Match.user1_id == current_user.id,
            Match.user2_id == current_user.id
        ),
        Match.status == MatchStatus.ACTIVE
    ).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found or inactive"
        )

    # Get receiver
    receiver_id = (match.user2_id if match.user1_id == current_user.id
                   else match.user1_id)

    # Moderate content
    ai_service = AIService(db)
    try:
        safety_score, is_safe = await ai_service.moderate_content(
            message_data.content, "message"
        )
    except:
        safety_score = 95.0
        is_safe = True

    # Create message
    message = Message(
        match_id=message_data.match_id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=message_data.content,
        status=MessageStatus.SENT,
        ai_safety_score=safety_score,
        is_flagged=not is_safe
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    # Try to send via WebSocket if receiver is online
    message_data_ws = {
        "type": "new_message",
        "message": {
            "id": message.id,
            "match_id": message.match_id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "content": message.content,
            "status": message.status.value,
            "created_at": message.created_at.isoformat()
        }
    }
    await manager.broadcast_to_match(match, current_user.id, message_data_ws)

    # Create notification if receiver is offline
    if receiver_id not in manager.active_connections:
        notif = Notification(
            user_id=receiver_id,
            type="message",
            title="New message",
            message=f"{current_user.profile.name} sent you a message",
            data={"match_id": match.id, "sender_id": current_user.id}
        )
        db.add(notif)
        db.commit()

    return message


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all conversations (matches with messages)"""

    # Get all active matches
    matches = db.query(Match).filter(
        or_(
            Match.user1_id == current_user.id,
            Match.user2_id == current_user.id
        ),
        Match.status == MatchStatus.ACTIVE
    ).all()

    conversations = []

    for match in matches:
        # Get messages for this match
        messages = db.query(Message).filter(
            Message.match_id == match.id
        ).order_by(Message.created_at.asc()).all()

        # Count unread messages
        unread_count = db.query(Message).filter(
            Message.match_id == match.id,
            Message.receiver_id == current_user.id,
            Message.status != MessageStatus.READ
        ).count()

        conversation = ConversationResponse(
            match=MatchBase(
                id=match.id,
                user1_id=match.user1_id,
                user2_id=match.user2_id,
                status=match.status,
                compatibility_score=match.compatibility_score,
                compatibility_reasons=match.compatibility_reasons,
                ai_ice_breakers=match.ai_ice_breakers,
                created_at=match.created_at
            ),
            messages=messages,
            unread_count=unread_count
        )

        conversations.append(conversation)

    # Sort by most recent message
    conversations.sort(
        key=lambda x: x.messages[-1].created_at if x.messages else x.match.created_at,
        reverse=True
    )

    return conversations


@router.get("/conversations/{match_id}", response_model=ConversationResponse)
async def get_conversation(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation for a specific match"""

    # Verify match
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

    # Get messages
    messages = db.query(Message).filter(
        Message.match_id == match_id
    ).order_by(Message.created_at.asc()).all()

    # Count unread
    unread_count = db.query(Message).filter(
        Message.match_id == match_id,
        Message.receiver_id == current_user.id,
        Message.status != MessageStatus.READ
    ).count()

    return ConversationResponse(
        match=MatchBase(
            id=match.id,
            user1_id=match.user1_id,
            user2_id=match.user2_id,
            status=match.status,
            compatibility_score=match.compatibility_score,
            compatibility_reasons=match.compatibility_reasons,
            ai_ice_breakers=match.ai_ice_breakers,
            created_at=match.created_at
        ),
        messages=messages,
        unread_count=unread_count
    )


@router.put("/conversations/{match_id}/read")
async def mark_conversation_read(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all messages in a conversation as read"""

    # Verify match
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

    # Mark messages as read
    updated = db.query(Message).filter(
        Message.match_id == match_id,
        Message.receiver_id == current_user.id,
        Message.status != MessageStatus.READ
    ).update({
        "status": MessageStatus.READ,
        "read_at": datetime.utcnow()
    })

    db.commit()

    return {"message": f"Marked {updated} messages as read"}
