"""
Chat Routes — REST + WebSocket.

REST endpoints (for history, conversations list, read receipts):
  GET  /chat/conversations          — list all conversations
  GET  /chat/conversations/{uid}    — message history with a user
  POST /chat/messages               — send a message (REST fallback)
  POST /chat/messages/{uid}/read    — mark conversation as read
  GET  /chat/unread-count           — total unread badge count
  GET  /chat/partners               — users this person can chat with
  DELETE /chat/messages/{msg_id}    — soft-delete a message

WebSocket:
  WS   /chat/ws                     — real-time channel (token in query param)
"""
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from shared.database import get_db, SessionLocal
from shared.schemas import ChatMessageCreate, ChatMessageResponse, ChatConversationSummary
from shared.models import User
from services.chat.service import ChatService
from services.chat.manager import manager
from services.auth.service import AuthService
from gateway.routes.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _msg_to_dict(msg, sender: User = None) -> dict:
    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "recipient_id": msg.recipient_id,
        "sender_name": (sender or msg.sender).full_name if (sender or msg.sender) else None,
        "sender_username": (sender or msg.sender).username,
        "content": msg.content,
        "is_read": msg.is_read,
        "created_at": msg.created_at.isoformat(),
    }


# ── REST endpoints ────────────────────────────────────────────────────────────

@router.get("/conversations", response_model=List[ChatConversationSummary])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all conversations for the current user, sorted by latest message."""
    return ChatService.get_conversations(db, current_user.id)


@router.get("/conversations/{partner_id}", response_model=List[ChatMessageResponse])
def get_conversation(
    partner_id: int,
    limit: int = Query(50, ge=1, le=200),
    before_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return message history between current user and partner_id."""
    msgs = ChatService.get_conversation(
        db, current_user.id, partner_id, limit=limit, before_id=before_id
    )
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "recipient_id": m.recipient_id,
            "sender_name": m.sender.full_name if m.sender else None,
            "sender_username": m.sender.username if m.sender else "",
            "content": m.content,
            "is_read": m.is_read,
            "created_at": m.created_at,
        }
        for m in msgs
    ]


@router.post("/messages", response_model=ChatMessageResponse, status_code=201)
async def send_message_rest(
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    REST fallback for sending a message.
    Also pushes the message over WebSocket to the recipient if they're online.
    """
    if payload.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    msg = ChatService.send_message(db, current_user.id, payload.recipient_id, payload.content)

    ws_payload = {
        "type": "new_message",
        "message": _msg_to_dict(msg, current_user),
    }
    await manager.send_to_user(payload.recipient_id, ws_payload)
    # Echo back to sender's other tabs
    await manager.send_to_user(current_user.id, ws_payload)

    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "recipient_id": msg.recipient_id,
        "sender_name": current_user.full_name,
        "sender_username": current_user.username,
        "content": msg.content,
        "is_read": msg.is_read,
        "created_at": msg.created_at,
    }


@router.post("/conversations/{partner_id}/read")
def mark_conversation_read(
    partner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all messages from partner_id to current user as read."""
    count = ChatService.mark_read(db, reader_id=current_user.id, sender_id=partner_id)
    return {"marked_read": count}


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Total unread message count — used for the nav badge."""
    return {"unread": ChatService.total_unread(db, current_user.id)}


@router.get("/partners")
def get_chat_partners(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return users this person is allowed to start a conversation with."""
    partners = ChatService.get_allowed_partners(db, current_user)
    return [
        {
            "id": p.id,
            "username": p.username,
            "full_name": p.full_name,
            "role": p.role,
            "is_online": manager.is_online(p.id),
        }
        for p in partners
    ]


@router.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a message (only visible to the deleting side)."""
    ok = ChatService.delete_message(db, message_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Message not found or not yours")
    return {"deleted": True}


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/ws")
async def chat_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    """
    Persistent WebSocket channel for real-time chat.

    Client connects with:  ws://host/chat/ws?token=<jwt>

    Incoming JSON frames:
      { "type": "message",   "recipient_id": 5, "content": "Hello!" }
      { "type": "read",      "sender_id": 5 }
      { "type": "ping" }

    Outgoing JSON frames:
      { "type": "new_message",  "message": { ...ChatMessageResponse } }
      { "type": "read_receipt", "reader_id": X, "sender_id": Y }
      { "type": "presence",     "user_id": X, "online": true/false }
      { "type": "pong" }
      { "type": "error",        "detail": "..." }
    """
    # Authenticate via token query param (headers not available in WS handshake)
    db: Session = SessionLocal()
    try:
        username = AuthService.verify_token(token)
        if not username:
            await websocket.close(code=4001)
            return
        current_user = AuthService.get_user_by_username(db, username)
        if not current_user or not current_user.is_active:
            await websocket.close(code=4001)
            return
    finally:
        db.close()

    await manager.connect(websocket, current_user.id)

    # Notify contacts that this user came online
    db = SessionLocal()
    try:
        partners = ChatService.get_allowed_partners(db, current_user)
        partner_ids = [p.id for p in partners]
    finally:
        db.close()

    for pid in partner_ids:
        await manager.send_to_user(pid, {
            "type": "presence",
            "user_id": current_user.id,
            "online": True,
        })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "detail": "Invalid JSON"}))
                continue

            msg_type = data.get("type")

            # ── Send a message ────────────────────────────────────────────────
            if msg_type == "message":
                recipient_id = data.get("recipient_id")
                content = (data.get("content") or "").strip()
                if not recipient_id or not content:
                    await websocket.send_text(json.dumps({"type": "error", "detail": "recipient_id and content required"}))
                    continue
                if recipient_id == current_user.id:
                    await websocket.send_text(json.dumps({"type": "error", "detail": "Cannot message yourself"}))
                    continue

                db = SessionLocal()
                try:
                    msg = ChatService.send_message(db, current_user.id, recipient_id, content)
                    payload = {
                        "type": "new_message",
                        "message": {
                            "id": msg.id,
                            "sender_id": msg.sender_id,
                            "recipient_id": msg.recipient_id,
                            "sender_name": current_user.full_name,
                            "sender_username": current_user.username,
                            "content": msg.content,
                            "is_read": msg.is_read,
                            "created_at": msg.created_at.isoformat(),
                        },
                    }
                finally:
                    db.close()

                # Deliver to recipient
                await manager.send_to_user(recipient_id, payload)
                # Echo to sender's other tabs
                await manager.send_to_user(current_user.id, payload)

            # ── Mark read ─────────────────────────────────────────────────────
            elif msg_type == "read":
                sender_id = data.get("sender_id")
                if not sender_id:
                    continue
                db = SessionLocal()
                try:
                    ChatService.mark_read(db, reader_id=current_user.id, sender_id=sender_id)
                finally:
                    db.close()
                # Notify the sender their messages were read
                await manager.send_to_user(sender_id, {
                    "type": "read_receipt",
                    "reader_id": current_user.id,
                    "sender_id": sender_id,
                })

            # ── Ping / keepalive ──────────────────────────────────────────────
            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, current_user.id)
        # Notify contacts that user went offline
        for pid in partner_ids:
            await manager.send_to_user(pid, {
                "type": "presence",
                "user_id": current_user.id,
                "online": False,
            })
