"""Ticket service for handling ticket creation and management"""
import json
from datetime import datetime
from pathlib import Path

class TicketService:
    """Service for managing support tickets"""

    # Store tickets relative to the bot directory
    TICKETS_DIR = Path(__file__).parent.parent / "data" / "tickets"

    @classmethod
    def _ensure_tickets_dir(cls):
        """Ensure tickets directory exists"""
        cls.TICKETS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_attachment_dir(cls, ticket_id: str) -> Path:
        """Get or create attachment directory for a ticket"""
        att_dir = cls.TICKETS_DIR / ticket_id / "attachments"
        att_dir.mkdir(parents=True, exist_ok=True)
        return att_dir

    @classmethod
    def get_attachment_path(cls, ticket_id: str, filename: str) -> Path:
        """Get full path for an attachment"""
        return cls.get_attachment_dir(ticket_id) / filename

    @classmethod
    def save_attachment(cls, ticket_id: str, filename: str, file_content: bytes) -> str:
        """Save attachment file and return its path"""
        if ticket_id:
            att_path = cls.get_attachment_path(ticket_id, filename)
        else:
            # Temporary location before ticket_id is known
            temp_dir = cls.TICKETS_DIR / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            att_path = temp_dir / filename

        with open(att_path, 'wb') as f:
            f.write(file_content)

        return str(att_path)

    @classmethod
    def create_ticket(cls, ticket_data: dict, attachment_paths: list = None) -> str:
        """
        Create a new ticket from user data

        Args:
            ticket_data: Dict with keys: name, email, department, issue, description, priority, attachments (optional)
            attachment_paths: List of attachment file paths

        Returns:
            ticket_id: Unique ticket identifier
        """
        cls._ensure_tickets_dir()

        # Generate ticket ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        ticket_id = f"TKT-{timestamp}"

        # Create ticket object
        ticket = {
            "ticket_id": ticket_id,
            "created_at": datetime.now().isoformat(),
            "name": ticket_data.get("name"),
            "email": ticket_data.get("email"),
            "department": ticket_data.get("department"),
            "issue": ticket_data.get("issue"),
            "description": ticket_data.get("description", ""),
            "priority": ticket_data.get("priority"),
            "status": "open",
            "attachments": []
        }

        # Add attachment info
        if ticket_data.get('attachments'):
            for att_info in ticket_data['attachments']:
                ticket['attachments'].append({
                    'filename': att_info.get('filename'),
                    'type': att_info.get('type')
                })

        # Save ticket to JSON file
        ticket_file = cls.TICKETS_DIR / f"{ticket_id}.json"
        with open(ticket_file, 'w', encoding='utf-8') as f:
            json.dump(ticket, f, indent=2, ensure_ascii=False)

        return ticket_id

    @classmethod
    def get_ticket(cls, ticket_id: str) -> dict:
        """Get ticket by ID"""
        ticket_file = cls.TICKETS_DIR / f"{ticket_id}.json"
        if not ticket_file.exists():
            return None

        with open(ticket_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def list_tickets(cls) -> list:
        """List all tickets"""
        cls._ensure_tickets_dir()
        tickets = []

        for ticket_file in cls.TICKETS_DIR.glob("*.json"):
            with open(ticket_file, 'r', encoding='utf-8') as f:
                tickets.append(json.load(f))

        return sorted(tickets, key=lambda t: t['created_at'], reverse=True)

    @classmethod
    def delete_ticket(cls, ticket_id: str) -> bool:
        """Delete a ticket and its attachments"""
        try:
            # Delete ticket JSON
            ticket_file = cls.TICKETS_DIR / f"{ticket_id}.json"
            if ticket_file.exists():
                ticket_file.unlink()

            # Delete attachments directory
            import shutil
            att_dir = cls.TICKETS_DIR / ticket_id
            if att_dir.exists():
                shutil.rmtree(att_dir)

            return True
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error deleting ticket {ticket_id}: {e}")
            return False

    @classmethod
    def add_reply(cls, ticket_id: str, reply_text: str, user_name: str = "Support Team") -> bool:
        """Add a reply/note to a ticket"""
        try:
            ticket = cls.get_ticket(ticket_id)
            if not ticket:
                return False

            if 'replies' not in ticket:
                ticket['replies'] = []

            from datetime import datetime
            ticket['replies'].append({
                'timestamp': datetime.now().isoformat(),
                'user': user_name,
                'text': reply_text
            })

            ticket_file = cls.TICKETS_DIR / f"{ticket_id}.json"
            with open(ticket_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(ticket, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error adding reply to ticket {ticket_id}: {e}")
            return False
