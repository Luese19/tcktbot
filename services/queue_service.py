"""Queue service for managing group mention requests"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
from models.queue_models import QueuedRequest
from utils.logger import get_logger

logger = get_logger(__name__)

class QueueService:
    """Service for managing group mention request queue"""

    QUEUE_DIR = Path(__file__).parent.parent / "data" / "queue"
    QUEUE_FILE = QUEUE_DIR / "requests.json"
    PROCESSING_FILE = QUEUE_DIR / "processing.json"

    @classmethod
    def _ensure_queue_dir(cls):
        """Ensure queue directory exists"""
        cls.QUEUE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _load_queue(cls) -> List[QueuedRequest]:
        """Load queue from file"""
        cls._ensure_queue_dir()
        if not cls.QUEUE_FILE.exists():
            return []

        try:
            with open(cls.QUEUE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [QueuedRequest.from_dict(item) for item in data]
        except Exception as e:
            logger.error(f"Error loading queue: {e}")
            return []

    @classmethod
    def _save_queue(cls, queue: List[QueuedRequest]):
        """Save queue to file"""
        cls._ensure_queue_dir()
        try:
            with open(cls.QUEUE_FILE, 'w', encoding='utf-8') as f:
                json.dump([item.to_dict() for item in queue], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving queue: {e}")

    @classmethod
    def add_request(cls, user_id: int, chat_id: int, mention_text: str,
                   user_name: Optional[str] = None, user_email: Optional[str] = None) -> QueuedRequest:
        """Add a mention request to queue"""
        queue = cls._load_queue()

        # Generate request ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[-6:]
        request_id = f"REQ-{timestamp}-{user_id}"

        request = QueuedRequest(
            request_id=request_id,
            user_id=user_id,
            chat_id=chat_id,
            mention_text=mention_text,
            user_name=user_name,
            user_email=user_email,
            status="queued"
        )

        queue.append(request)
        cls._save_queue(queue)
        logger.info(f"Added request {request_id} to queue. Queue size: {len(queue)}")

        return request

    @classmethod
    def get_queue_position(cls, user_id: int) -> Optional[int]:
        """Get user's position in queue (1-indexed). Returns None if not in queue."""
        queue = cls._load_queue()
        queued_items = [req for req in queue if req.status == "queued"]

        for idx, req in enumerate(queued_items, 1):
            if req.user_id == user_id:
                return idx

        return None

    @classmethod
    def get_queue_size(cls) -> int:
        """Get current queue size (queued items only)"""
        queue = cls._load_queue()
        return len([req for req in queue if req.status == "queued"])

    @classmethod
    def get_next_request(cls) -> Optional[QueuedRequest]:
        """Get the next queued request to process"""
        queue = cls._load_queue()

        # Find first queued item
        for req in queue:
            if req.status == "queued":
                req.status = "processing"
                cls._save_queue(queue)
                return req

        return None

    @classmethod
    def mark_completed(cls, request_id: str, ticket_id: Optional[str] = None):
        """Mark request as completed"""
        queue = cls._load_queue()

        for req in queue:
            if req.request_id == request_id:
                req.status = "completed"
                req.processed_at = datetime.now()
                req.ticket_id = ticket_id
                break

        cls._save_queue(queue)
        logger.info(f"Request {request_id} marked as completed. Ticket: {ticket_id}")

    @classmethod
    def mark_failed(cls, request_id: str, reason: str = ""):
        """Mark request as failed"""
        queue = cls._load_queue()

        for req in queue:
            if req.request_id == request_id:
                req.status = "failed"
                req.processed_at = datetime.now()
                break

        cls._save_queue(queue)
        logger.error(f"Request {request_id} marked as failed. Reason: {reason}")

    @classmethod
    def get_request(cls, request_id: str) -> Optional[QueuedRequest]:
        """Get a specific request by ID"""
        queue = cls._load_queue()
        for req in queue:
            if req.request_id == request_id:
                return req
        return None

    @classmethod
    def get_requests_by_user(cls, user_id: int) -> List[QueuedRequest]:
        """Get all requests from a specific user"""
        queue = cls._load_queue()
        return [req for req in queue if req.user_id == user_id]

    @classmethod
    def get_estimated_wait_time(cls, user_id: int) -> Optional[timedelta]:
        """
        Estimate wait time for a user in queue.
        Assumes ~1 minute per request processed.
        """
        position = cls.get_queue_position(user_id)
        if position is None:
            return None

        # Estimate 1 minute per request
        estimated_minutes = position * 1
        return timedelta(minutes=estimated_minutes)

    @classmethod
    def cleanup_old_requests(cls, days: int = 7):
        """Remove completed requests older than specified days"""
        queue = cls._load_queue()
        cutoff_date = datetime.now() - timedelta(days=days)

        original_size = len(queue)
        queue = [
            req for req in queue
            if not (req.status in ["completed", "failed"] and req.processed_at and req.processed_at < cutoff_date)
        ]

        if len(queue) < original_size:
            cls._save_queue(queue)
            logger.info(f"Cleaned up {original_size - len(queue)} old requests")

    @classmethod
    def get_queue_stats(cls) -> dict:
        """Get queue statistics"""
        queue = cls._load_queue()

        stats = {
            'total': len(queue),
            'queued': len([r for r in queue if r.status == 'queued']),
            'processing': len([r for r in queue if r.status == 'processing']),
            'completed': len([r for r in queue if r.status == 'completed']),
            'failed': len([r for r in queue if r.status == 'failed'])
        }

        return stats
