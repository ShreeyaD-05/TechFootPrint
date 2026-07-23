"""
Chat Service — database operations for direct messages.
"""
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, case

from shared.models import ChatMessage, User


class ChatService:

    # ── Sending ───────────────────────────────────────────────────────────────

    @staticmethod
    def send_message(
        db: Session,
        sender_id: int,
        recipient_id: int,
        content: str,
    ) -> ChatMessage:
        msg = ChatMessage(
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=content.strip(),
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    # ── History ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_conversation(
        db: Session,
        user_a: int,
        user_b: int,
        limit: int = 50,
        before_id: Optional[int] = None,
    ) -> List[ChatMessage]:
        """
        Return messages between two users, newest-last.
        Respects soft-delete flags so each side only sees their own view.
        """
        q = db.query(ChatMessage).filter(
            or_(
                and_(
                    ChatMessage.sender_id == user_a,
                    ChatMessage.recipient_id == user_b,
                    ChatMessage.deleted_by_sender == False,
                ),
                and_(
                    ChatMessage.sender_id == user_b,
                    ChatMessage.recipient_id == user_a,
                    ChatMessage.deleted_by_recipient == False,
                ),
            )
        )
        if before_id:
            q = q.filter(ChatMessage.id < before_id)
        msgs = q.order_by(ChatMessage.created_at.desc()).limit(limit).all()
        return list(reversed(msgs))

    # ── Conversations list ────────────────────────────────────────────────────

    @staticmethod
    def get_conversations(db: Session, user_id: int) -> List[dict]:
        """
        Return one entry per conversation partner, with last message + unread count.
        """
        # All messages involving this user
        all_msgs = db.query(ChatMessage).filter(
            or_(
                and_(ChatMessage.sender_id == user_id, ChatMessage.deleted_by_sender == False),
                and_(ChatMessage.recipient_id == user_id, ChatMessage.deleted_by_recipient == False),
            )
        ).order_by(ChatMessage.created_at.desc()).all()

        # Group by partner
        seen: dict = {}  # partner_id → latest ChatMessage
        for msg in all_msgs:
            partner_id = msg.recipient_id if msg.sender_id == user_id else msg.sender_id
            if partner_id not in seen:
                seen[partner_id] = msg

        if not seen:
            return []

        # Unread counts (messages sent TO me that I haven't read)
        unread_rows = db.query(
            ChatMessage.sender_id,
            func.count(ChatMessage.id).label("cnt"),
        ).filter(
            ChatMessage.recipient_id == user_id,
            ChatMessage.is_read == False,
            ChatMessage.deleted_by_recipient == False,
            ChatMessage.sender_id.in_(list(seen.keys())),
        ).group_by(ChatMessage.sender_id).all()

        unread_map = {r.sender_id: r.cnt for r in unread_rows}

        # Fetch partner user objects
        partners = db.query(User).filter(User.id.in_(list(seen.keys()))).all()
        partner_map = {p.id: p for p in partners}

        result = []
        for partner_id, last_msg in seen.items():
            partner = partner_map.get(partner_id)
            if not partner:
                continue
            result.append({
                "partner_id": partner_id,
                "partner_name": partner.full_name,
                "partner_username": partner.username,
                "partner_role": partner.role,
                "last_message": last_msg.content[:80],
                "last_message_at": last_msg.created_at,
                "unread_count": unread_map.get(partner_id, 0),
            })

        # Sort by last message time descending
        result.sort(key=lambda x: x["last_message_at"], reverse=True)
        return result

    # ── Read receipts ─────────────────────────────────────────────────────────

    @staticmethod
    def mark_read(db: Session, reader_id: int, sender_id: int) -> int:
        """Mark all messages from sender_id to reader_id as read."""
        updated = db.query(ChatMessage).filter(
            ChatMessage.sender_id == sender_id,
            ChatMessage.recipient_id == reader_id,
            ChatMessage.is_read == False,
        ).update({"is_read": True})
        db.commit()
        return updated

    # ── Unread total ──────────────────────────────────────────────────────────

    @staticmethod
    def total_unread(db: Session, user_id: int) -> int:
        return db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.recipient_id == user_id,
            ChatMessage.is_read == False,
            ChatMessage.deleted_by_recipient == False,
        ).scalar() or 0

    # ── Delete (soft) ─────────────────────────────────────────────────────────

    @staticmethod
    def delete_message(db: Session, message_id: int, user_id: int) -> bool:
        msg = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not msg:
            return False
        if msg.sender_id == user_id:
            msg.deleted_by_sender = True
        elif msg.recipient_id == user_id:
            msg.deleted_by_recipient = True
        else:
            return False
        db.commit()
        return True

    # ── Allowed partners ──────────────────────────────────────────────────────

    @staticmethod
    def get_allowed_partners(db: Session, user: User) -> List[User]:
        """
        Return users this person is allowed to chat with:
        - Students: their assigned faculty mentor(s)
        - Faculty/dept_admin/management: students in their college
        - super_admin: everyone in the system
        """
        from shared.models import MentorAssignment

        if user.role == "super_admin":
            return db.query(User).filter(
                User.id != user.id,
                User.is_active == True,
            ).order_by(User.full_name).all()

        if user.role == "student":
            # Assigned mentors
            assignments = db.query(MentorAssignment).filter(
                MentorAssignment.student_id == user.id,
                MentorAssignment.is_active == True,
            ).all()
            mentor_ids = [a.mentor_id for a in assignments]
            if not mentor_ids:
                # Fall back: any faculty in same college
                return db.query(User).filter(
                    User.college_id == user.college_id,
                    User.role.in_(["faculty", "dept_admin", "management"]),
                    User.is_active == True,
                ).order_by(User.full_name).all()
            return db.query(User).filter(User.id.in_(mentor_ids), User.is_active == True).all()

        # Faculty / dept_admin / management
        return db.query(User).filter(
            User.college_id == user.college_id,
            User.role == "student",
            User.is_active == True,
        ).order_by(User.full_name).all()
