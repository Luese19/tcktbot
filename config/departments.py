"""Department configuration for Help Desk Bot"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

DEPARTMENTS = {
    "HR": "Human Resources",
    "Operations": "Operations",
    "Purchasing": "Purchasing Office",
    "Sales": "Marketing & Communications",
    "Accounting": "Accounting",
    "Warehouse": "Warehouse",
    "Kitchen": "Kitechen Office",
    "Admin Office": "Admin Office",
    "Catering": "Catering",
    "Stewards": "Stewards",
    "Maintenance": "Maintenance",
    "IT": "IT Department",
}

PRIORITY_LEVELS = {
    "LOW": "Low Priority",
    "NORMAL": "Normal Priority",
    "HIGH": "High Priority",
    "URGENT": "Urgent"
}

# Department Auto-routing: Auto-assign priority based on department and keywords
DEPARTMENT_AUTO_ROUTING = {
    "HR": {
        "default": "NORMAL",
        "keywords": {
            "urgent": "URGENT",
            "asap": "HIGH",
            "complaint": "HIGH",
            "resign": "URGENT"
        }
    },
    "IT": {
        "default": "HIGH",
        "keywords": {
            "down": "URGENT",
            "server": "URGENT",
            "network": "HIGH",
            "offline": "URGENT",
            "password": "NORMAL"
        }
    },
    "Accounting": {
        "default": "NORMAL",
        "keywords": {
            "urgent": "URGENT",
            "payment": "HIGH",
            "invoice": "HIGH"
        }
    },
    "Operations": {
        "default": "NORMAL",
        "keywords": {
            "emergency": "URGENT",
            "critical": "HIGH"
        }
    },
    "Maintenance": {
        "default": "HIGH",
        "keywords": {
            "emergency": "URGENT",
            "broken": "HIGH",
            "urgent": "URGENT"
        }
    }
}


def get_auto_routed_priority(department: str, issue: str, description: str = "") -> str:
    """
    Auto-route priority based on department and keywords

    Args:
        department: Department name
        issue: Issue title
        description: Issue description

    Returns:
        Priority level (LOW, NORMAL, HIGH, URGENT)
    """
    if department not in DEPARTMENT_AUTO_ROUTING:
        return "NORMAL"

    dept_config = DEPARTMENT_AUTO_ROUTING[department]
    default_priority = dept_config.get("default", "NORMAL")
    keywords = dept_config.get("keywords", {})

    # Check keywords in issue and description
    combined_text = (issue + " " + description).lower()

    for keyword, priority in keywords.items():
        if keyword in combined_text:
            return priority

    return default_priority


def create_department_keyboard():
    """Create department selection keyboard"""
    keyboard = []
    codes = list(DEPARTMENTS.keys())
    for i in range(0, len(codes), 2):
        row = [InlineKeyboardButton(DEPARTMENTS[codes[i]], callback_data=f"dept_{codes[i]}")]
        if i + 1 < len(codes):
            row.append(InlineKeyboardButton(DEPARTMENTS[codes[i+1]], callback_data=f"dept_{codes[i+1]}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def create_priority_keyboard():
    """Create priority selection keyboard"""
    keyboard = []
    codes = list(PRIORITY_LEVELS.keys())
    for i in range(0, len(codes), 2):
        row = [InlineKeyboardButton(PRIORITY_LEVELS[codes[i]], callback_data=f"priority_{codes[i]}")]
        if i + 1 < len(codes):
            row.append(InlineKeyboardButton(PRIORITY_LEVELS[codes[i+1]], callback_data=f"priority_{codes[i+1]}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def create_confirmation_keyboard():
    """Create confirmation keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Submit Ticket", callback_data="confirm_submit"),
         InlineKeyboardButton("Cancel", callback_data="confirm_cancel")],
        [InlineKeyboardButton("Edit Details", callback_data="confirm_edit")]
    ])