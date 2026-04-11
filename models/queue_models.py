"""Queue models for managing group mention requests"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class QueuedRequest:
    """Represents a queued mention request"""
    request_id: str
    user_id: int
    chat_id: int
    mention_text: str
    submitted_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    ticket_id: Optional[str] = None
    status: str = "queued"  # queued, processing, completed, failed
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'mention_text': self.mention_text,
            'submitted_at': self.submitted_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'ticket_id': self.ticket_id,
            'status': self.status,
            'user_name': self.user_name,
            'user_email': self.user_email
        }

    @staticmethod
    def from_dict(data: dict) -> 'QueuedRequest':
        """Create from dictionary"""
        return QueuedRequest(
            request_id=data['request_id'],
            user_id=data['user_id'],
            chat_id=data['chat_id'],
            mention_text=data['mention_text'],
            submitted_at=datetime.fromisoformat(data['submitted_at']),
            processed_at=datetime.fromisoformat(data['processed_at']) if data.get('processed_at') else None,
            ticket_id=data.get('ticket_id'),
            status=data.get('status', 'queued'),
            user_name=data.get('user_name'),
            user_email=data.get('user_email')
        )
