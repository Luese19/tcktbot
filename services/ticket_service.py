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
            "updated_at": datetime.now().isoformat(),
            "name": ticket_data.get("name"),
            "email": ticket_data.get("email"),
            "department": ticket_data.get("department"),
            "issue": ticket_data.get("issue"),
            "description": ticket_data.get("description", ""),
            "priority": ticket_data.get("priority"),
            "status": "open",
            "attachments": [],
            "status_history": [
                {
                    "status": "open",
                    "updated_at": datetime.now().isoformat(),
                    "updated_by": "system"
                }
            ]
        }

        # Add optional group tracking fields
        if ticket_data.get("group_id"):
            ticket["group_id"] = ticket_data.get("group_id")
            ticket["group_name"] = ticket_data.get("group_name", "Unknown Group")
            ticket["group_type"] = ticket_data.get("group_type", "group")
            ticket["bot_message_id"] = ticket_data.get("bot_message_id")
            ticket["source_message_id"] = ticket_data.get("source_message_id")

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

            # Update ticket timestamp
            ticket['updated_at'] = datetime.now().isoformat()

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

    @classmethod
    def update_ticket_status(cls, ticket_id: str, new_status: str, updated_by: str = "admin") -> dict:
        """
        Update ticket status and track history

        Args:
            ticket_id: Ticket ID to update
            new_status: New status value (e.g., "open", "in_progress", "completed")
            updated_by: Who made the update

        Returns:
            Updated ticket dict or None if failed
        """
        try:
            ticket = cls.get_ticket(ticket_id)
            if not ticket:
                return None

            # Only update if new status is different
            if ticket.get('status') == new_status:
                return ticket

            # Update status
            ticket['status'] = new_status
            ticket['updated_at'] = datetime.now().isoformat()

            # Track status history
            if 'status_history' not in ticket:
                ticket['status_history'] = []

            ticket['status_history'].append({
                'status': new_status,
                'updated_at': datetime.now().isoformat(),
                'updated_by': updated_by
            })

            # Save updated ticket
            ticket_file = cls.TICKETS_DIR / f"{ticket_id}.json"
            with open(ticket_file, 'w', encoding='utf-8') as f:
                json.dump(ticket, f, indent=2, ensure_ascii=False)

            return ticket
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error updating ticket status {ticket_id}: {e}")
            return None

    @classmethod
    def get_tickets_by_user_email(cls, email: str) -> list:
        """
        Get all tickets for a specific user by email

        Args:
            email: User email address

        Returns:
            List of tickets sorted by creation date (newest first)
        """
        tickets = cls.list_tickets()
        user_tickets = [t for t in tickets if t.get('email', '').lower() == email.lower()]
        return sorted(user_tickets, key=lambda t: t.get('created_at', ''), reverse=True)

    @classmethod
    def get_tickets_older_than(cls, days: int) -> list:
        """
        Get all tickets created more than N days ago

        Args:
            days: Number of days (tickets older than this will be returned)

        Returns:
            List of ticket IDs that are older than specified days
        """
        from datetime import datetime, timedelta

        try:
            tickets = cls.list_tickets()
            cutoff_date = datetime.now() - timedelta(days=days)
            old_tickets = []

            for ticket in tickets:
                try:
                    created_at_str = ticket.get('created_at')
                    if created_at_str:
                        created_at = datetime.fromisoformat(created_at_str)
                        if created_at < cutoff_date:
                            old_tickets.append(ticket.get('ticket_id'))
                except (ValueError, TypeError):
                    from utils.logger import get_logger

                    logger = get_logger(__name__)
                    logger.warning(f"Could not parse created_at for {ticket.get('ticket_id')}")
                    continue

            return old_tickets
        except Exception as e:
            from utils.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"Error getting tickets older than {days} days: {e}")
            return []

    @classmethod
    def find_similar_tickets(cls, issue_text: str, max_results: int = 3) -> list:
        """
        Find tickets with similar issues using keyword matching

        Args:
            issue_text: Issue text to search for
            max_results: Maximum number of similar tickets to return

        Returns:
            List of similar tickets with similarity scores (highest first)
        """
        try:
            # Get all open tickets
            all_tickets = cls.list_tickets()
            open_tickets = [t for t in all_tickets if t.get('status') == 'open']

            if not open_tickets:
                return []

            # Extract keywords from issue_text
            issue_words = set(w.lower() for w in issue_text.split() if len(w) > 3)

            if not issue_words:
                return []

            # Calculate similarity scores
            scored_tickets = []
            for ticket in open_tickets:
                ticket_words = set(w.lower() for w in ticket.get('issue', '').split() if len(w) > 3)
                if not ticket_words:
                    continue

                # Calculate intersection and similarity percentage
                common_words = issue_words & ticket_words
                if common_words:
                    similarity = len(common_words) / max(len(issue_words), len(ticket_words))
                    # Only include if >20% similar
                    if similarity > 0.2:
                        scored_tickets.append((ticket, similarity))

            # Sort by similarity score and return top results
            scored_tickets.sort(key=lambda x: x[1], reverse=True)
            return [t[0] for t in scored_tickets[:max_results]]

        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error finding similar tickets: {e}")
            return []

    @classmethod
    def get_ticket_source_info(cls, ticket_id: str) -> dict:
        """
        Get group/message tracking info from a ticket

        Returns:
            Dict with group_id, bot_message_id, group_name, group_type if available, else empty dict
        """
        try:
            ticket = cls.get_ticket(ticket_id)
            if not ticket:
                return {}

            source_info = {}
            if 'group_id' in ticket:
                source_info['group_id'] = ticket['group_id']
            if 'bot_message_id' in ticket:
                source_info['bot_message_id'] = ticket['bot_message_id']
            if 'group_name' in ticket:
                source_info['group_name'] = ticket['group_name']
            if 'group_type' in ticket:
                source_info['group_type'] = ticket['group_type']

            return source_info
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error getting ticket source info for {ticket_id}: {e}")
            return {}

    @classmethod
    def save_ticket_source_info(cls, ticket_id: str, group_id: int, group_name: str,
                                 group_type: str, bot_message_id: int, source_message_id: int) -> bool:
        """
        Save group/message tracking info to an existing ticket

        Args:
            ticket_id: Ticket to update
            group_id: Telegram group chat ID
            group_name: Group display name
            group_type: "group" or "supergroup"
            bot_message_id: Message ID of bot's confirmation
            source_message_id: Message ID of original mention

        Returns:
            True if successful, False otherwise
        """
        try:
            ticket = cls.get_ticket(ticket_id)
            if not ticket:
                return False

            ticket['group_id'] = group_id
            ticket['group_name'] = group_name
            ticket['group_type'] = group_type
            ticket['bot_message_id'] = bot_message_id
            ticket['source_message_id'] = source_message_id

            ticket_file = cls.TICKETS_DIR / f"{ticket_id}.json"
            with open(ticket_file, 'w', encoding='utf-8') as f:
                json.dump(ticket, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error saving ticket source info for {ticket_id}: {e}")
            return False
