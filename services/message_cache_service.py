"""Service to cache recent messages for reaction-based ticket creation"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import threading

from utils.logger import get_logger

logger = get_logger(__name__)

# Global message cache: {chat_id: {message_id: message_data}}
_message_cache: Dict[int, Dict[int, dict]] = defaultdict(dict)
_cache_lock = threading.Lock()

# Cache expiration: 24 hours
CACHE_EXPIRY_HOURS = 24


class MessageCacheService:
    """Service to cache and retrieve messages"""

    @staticmethod
    def store_message(chat_id: int, message_id: int, text: str, sender_name: str = "Unknown") -> None:
        """Store a message in cache for later retrieval"""
        try:
            with _cache_lock:
                _message_cache[chat_id][message_id] = {
                    "text": text,
                    "sender_name": sender_name,
                    "timestamp": datetime.utcnow()
                }
            logger.info(f"[CACHE] Stored message {message_id} in chat {chat_id}: {text[:80]}")
            logger.info(f"[CACHE] Cache now has {len(_message_cache[chat_id])} messages in this chat")
        except Exception as e:
            logger.error(f"[CACHE] Error storing message: {e}", exc_info=True)

    @staticmethod
    def get_message(chat_id: int, message_id: int) -> Optional[str]:
        """Retrieve message text from cache"""
        try:
            with _cache_lock:
                logger.debug(f"[CACHE] Looking for message {message_id} in chat {chat_id}")
                logger.debug(f"[CACHE] Available chats: {list(_message_cache.keys())}")

                if chat_id in _message_cache:
                    logger.debug(f"[CACHE] Chat {chat_id} found, messages: {list(_message_cache[chat_id].keys())}")
                    if message_id in _message_cache[chat_id]:
                        msg_data = _message_cache[chat_id][message_id]
                        # Check if not expired
                        age = datetime.utcnow() - msg_data["timestamp"]
                        if age < timedelta(hours=CACHE_EXPIRY_HOURS):
                            logger.info(f"[CACHE] Found message {message_id}: {msg_data['text'][:80]} (age: {age})")
                            return msg_data.get("text", "")
                        else:
                            # Remove expired message
                            logger.warning(f"[CACHE] Message {message_id} expired (age: {age})")
                            del _message_cache[chat_id][message_id]
                    else:
                        logger.warning(f"[CACHE] Message {message_id} not found in chat {chat_id}")
                else:
                    logger.warning(f"[CACHE] Chat {chat_id} not found in cache")

            return None
        except Exception as e:
            logger.error(f"[CACHE] Error retrieving message: {e}", exc_info=True)
            return None

    @staticmethod
    def cleanup_expired() -> None:
        """Remove expired messages from cache"""
        try:
            with _cache_lock:
                expired_count = 0
                for chat_id in list(_message_cache.keys()):
                    for msg_id in list(_message_cache[chat_id].keys()):
                        msg_data = _message_cache[chat_id][msg_id]
                        if datetime.utcnow() - msg_data["timestamp"] >= timedelta(hours=CACHE_EXPIRY_HOURS):
                            del _message_cache[chat_id][msg_id]
                            expired_count += 1

                    # Clean up empty chat caches
                    if not _message_cache[chat_id]:
                        del _message_cache[chat_id]

                if expired_count > 0:
                    logger.info(f"[CACHE] Cleaned up {expired_count} expired messages")
        except Exception as e:
            logger.warning(f"[CACHE] Error during cleanup: {e}")

    @staticmethod
    def get_cache_stats() -> dict:
        """Get cache statistics"""
        with _cache_lock:
            total_chats = len(_message_cache)
            total_messages = sum(len(msgs) for msgs in _message_cache.values())
            return {
                "total_chats": total_chats,
                "total_messages": total_messages
            }


__all__ = ['MessageCacheService']
