"""Department configuration for Help Desk Bot"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

DEPARTMENTS = {
    "HR": "Human Resources",
    "Operations": "Operations",
    "Purchasing": "Purchasing Office",
    "Sales": "Marketing & Communications",
    "Accounting": "Accounting",
    "Warehouse": "Warehouse",
    "Kitchen": "Kitchen Office",
    "Admin Ops": "Admin Ops",
    "Catering": "Catering",
    "Stewards": "Stewards",
    "Maintenance": "Maintenance",
    "IT": "IT Department",
    "Pastry": "Pastry",
    "Despatching": "Despatching"
}

PRIORITY_LEVELS = {
    "LOW": "Low Priority",
    "NORMAL": "Normal Priority",
    "HIGH": "High Priority",
    "URGENT": "Urgent"
}

# Department Auto-routing: Auto-assign priority based on department and keywords
DEPARTMENT_AUTO_ROUTING = {
    "IT": {
        "default": "NORMAL",
        "keywords": {
            "down": "URGENT",
            "server": "URGENT",
            "network": "HIGH",
            "offline": "URGENT",
            "password": "NORMAL",
            "access": "NORMAL",
            "email": "NORMAL",
            "computer": "HIGH",
            "laptop": "NORMAL",
            "printer": "HIGH",
            "software": "NORMAL",
            "hardware": "NORMAL",
            "urgent": "URGENT",
            "asap": "HIGH",
            "error": "HIGH",
            "pc": "NORMAL",
            "mac": "NORMAL",
            "windows": "NORMAL",
            "update": "HIGH",
            "Permit": "URGENT",
            "tv remote": "NORMAL",
            "projector": "NORMAL",
            "presentation": "NORMAL",
            "conference": "NORMAL",
            "video": "NORMAL",
            "audio": "NORMAL",
            "zoom": "NORMAL",
            "teams": "NORMAL",
            "slack": "NORMAL",
            "email": "NORMAL",
            "phone": "NORMAL",
            "tablet": "NORMAL",
            "mobile": "NORMAL",
            "aircondition": "HIGH",
            "hvac": "HIGH",
            "heat": "HIGH",
            "temperature": "HIGH",
            "light": "HIGH",
            "bulb": "HIGH",
            "ac": "HIGH",
            "internet": "HIGH"
        }
    },
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
    if not department or department not in DEPARTMENT_AUTO_ROUTING:
        return "NORMAL"

    dept_config = DEPARTMENT_AUTO_ROUTING[department]
    default_priority = dept_config.get("default", "NORMAL")
    keywords = dept_config.get("keywords", {})

    # Combine issue and description for keyword search
    text_to_search = f"{issue} {description}".lower()

    # Check for keywords (longer keywords first to match "server down" before "server")
    sorted_keywords = sorted(keywords.keys(), key=len, reverse=True)
    
    for kw in sorted_keywords:
        if kw.lower() in text_to_search:
            return keywords[kw]

    return default_priority

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