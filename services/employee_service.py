"""Employee registration service for managing email-to-Telegram user mapping"""
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)

class EmployeeService:
    """Service for managing employee email registrations"""

    REGISTRY_DIR = Path(__file__).parent.parent / "data" / "employees"
    REGISTRY_FILE = REGISTRY_DIR / "registrations.json"

    @classmethod
    def _ensure_registry_dir(cls):
        """Ensure registry directory exists"""
        cls.REGISTRY_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _load_registry(cls) -> dict:
        """Load employee registry from file"""
        cls._ensure_registry_dir()
        if not cls.REGISTRY_FILE.exists():
            return {}

        try:
            with open(cls.REGISTRY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading employee registry: {e}")
            return {}

    @classmethod
    def _save_registry(cls, registry: dict):
        """Save employee registry to file"""
        cls._ensure_registry_dir()
        try:
            with open(cls.REGISTRY_FILE, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving employee registry: {e}")

    @classmethod
    def register_email(cls, user_id: int, email: str, user_name: str = None) -> bool:
        """
        Register an employee's email with their Telegram user ID

        Args:
            user_id: Telegram user ID
            email: Employee's company email
            user_name: Employee's full name (optional)

        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            registry = cls._load_registry()

            # Store by user_id for lookup
            registry[str(user_id)] = {
                "user_id": user_id,
                "email": email,
                "name": user_name or "Unknown",
                "registered_at": datetime.now().isoformat()
            }

            cls._save_registry(registry)
            logger.info(f"Employee {user_id} registered email: {email}")
            return True

        except Exception as e:
            logger.error(f"Error registering email for user {user_id}: {e}")
            return False

    @classmethod
    def get_employee_email(cls, user_id: int) -> Optional[str]:
        """
        Get registered email for a user ID

        Args:
            user_id: Telegram user ID

        Returns:
            str: Employee email if found, None otherwise
        """
        try:
            registry = cls._load_registry()
            employee = registry.get(str(user_id))

            if employee:
                return employee["email"]

            return None

        except Exception as e:
            logger.error(f"Error getting email for user {user_id}: {e}")
            return None

    @classmethod
    def get_employee_info(cls, user_id: int) -> Optional[dict]:
        """
        Get full employee info (email, name, registration date)

        Args:
            user_id: Telegram user ID

        Returns:
            dict: Employee info if found, None otherwise
        """
        try:
            registry = cls._load_registry()
            return registry.get(str(user_id))

        except Exception as e:
            logger.error(f"Error getting employee info for user {user_id}: {e}")
            return None

    @classmethod
    def unregister_email(cls, user_id: int) -> bool:
        """
        Remove email registration for a user

        Args:
            user_id: Telegram user ID

        Returns:
            bool: True if unregistration successful
        """
        try:
            registry = cls._load_registry()

            if str(user_id) in registry:
                del registry[str(user_id)]
                cls._save_registry(registry)
                logger.info(f"Employee {user_id} unregistered")
                return True

            return False

        except Exception as e:
            logger.error(f"Error unregistering email for user {user_id}: {e}")
            return False

    @classmethod
    def get_all_employees(cls) -> list:
        """Get all registered employees"""
        try:
            registry = cls._load_registry()
            return list(registry.values())

        except Exception as e:
            logger.error(f"Error getting all employees: {e}")
            return []

    @classmethod
    def is_registered(cls, user_id: int) -> bool:
        """Check if user has registered email"""
        return cls.get_employee_email(user_id) is not None

    @classmethod
    def get_inactive_users(cls, months_inactive: int = 4) -> list:
        """
        Get list of users with no ticket activity in N+ months

        Args:
            months_inactive: Months of inactivity to check (default: 4)

        Returns:
            List of user_info dicts for inactive users
        """
        from datetime import datetime, timedelta
        from services.ticket_service import TicketService

        try:
            all_users = cls.get_all_employees()
            if not all_users:
                return []

            cutoff_date = datetime.now() - timedelta(days=30 * months_inactive)
            inactive_users = []

            for user_info in all_users:
                user_email = user_info.get('email')
                if not user_email:
                    continue

                # Get all tickets for this user
                user_tickets = TicketService.get_tickets_by_user_email(user_email)

                # Check if user has any recent activity
                has_recent_activity = False

                if user_tickets:
                    for ticket in user_tickets:
                        try:
                            created_at_str = ticket.get('created_at')
                            if created_at_str:
                                created_at = datetime.fromisoformat(created_at_str)
                                if created_at >= cutoff_date:
                                    has_recent_activity = True
                                    break
                        except (ValueError, TypeError):
                            continue

                # Add to inactive list if no recent activity found
                if not has_recent_activity:
                    inactive_users.append(user_info)

            return inactive_users

        except Exception as e:
            logger.error(f"Error getting inactive users: {e}")
            return []

    @classmethod
    def delete_user_registration(cls, user_id: int) -> bool:
        """
        Delete/unregister a user (wrapper for unregister_email)

        Args:
            user_id: Telegram user ID to delete

        Returns:
            bool: True if deletion successful
        """
        return cls.unregister_email(user_id)
