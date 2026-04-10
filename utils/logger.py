"""Logging configuration for the bot"""
import logging
import logging.handlers
from pathlib import Path

def setup_logging(log_level="INFO", log_file_path="./logs/bot.log"):
    """Configure logging"""
    logger = logging.getLogger("helpdesk_bot")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if logger.handlers:
        return logger

    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                                 datefmt='%Y-%m-%d %H:%M:%S')

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler
    try:
        Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not setup file logging: {e}")

    # Suppress PTB warnings about per_message and JobQueue
    logging.getLogger("telegram.ext.ConversationHandler").setLevel(logging.ERROR)
    logging.getLogger("telegram.ext._handlers.conversationhandler").setLevel(logging.ERROR)

    return logger

def get_logger(name="helpdesk_bot"):
    """Get logger instance"""
    return logging.getLogger(name)