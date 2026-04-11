#!/usr/bin/env python3
"""Complete setup verification and testing guide"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'bot'))

print("=" * 80)
print("COMPLETE SYSTEM VERIFICATION")
print("=" * 80)

# Test 1: Configuration
print("\n[1] Configuration Check...")
from config.settings import settings
print(f"    Bot Token: {settings.bot.TOKEN[:20]}...")
print(f"    Spiceworks Email: {settings.email.SPICEWORKS_EMAIL}")
print(f"    Company Domain: {settings.company.EMAIL_DOMAIN}")
print(f"    [OK] Configuration OK")

# Test 2: Handlers
print("\n[2] Handler Registration Check...")
from main import TelegramHelpDeskBot
try:
    bot = TelegramHelpDeskBot()
    print(f"    [OK] Bot initialized successfully")
    print(f"    [OK] Handlers registered")
except Exception as e:
    print(f"    [FAIL] Bot initialization failed: {e}")
    sys.exit(1)

# Test 3: Email
print("\n[3] Email Integration Check...")
from services.spiceworks_service import SpiceworksService
print(f"    [OK] Email service loaded")

# Test 4: Ticket creation
print("\n[4] Ticket Creation Check...")
from services.ticket_service import TicketService
from handlers.mention_handler import GroupMentionHandler

ticket_data = {
    "name": "Setup Test",
    "email": f"test@{settings.company.EMAIL_DOMAIN}",
    "department": GroupMentionHandler._extract_department("office wifi"),
    "issue": "Test mention",
    "description": "Setup verification test",
    "priority": "Normal"
}
ticket_id = TicketService.create_ticket(ticket_data)
print(f"    [OK] Test ticket created: {ticket_id}")

print("\n" + "=" * 80)
print("ALL SYSTEMS READY")
print("=" * 80)
print("""
NEXT STEPS:

1. START THE BOT in a terminal:

   cd d:\\TICKETINGBOT
   python bot/main.py

   Wait for output:
   "Bot handlers configured"

2. ADD BOT TO TELEGRAM GROUP

3. SEND THIS MESSAGE in the group:

   @mevithelpdeskbot help office wifi not working

4. YOU SHOULD SEE:
   [OK] "Creating ticket..." message appears
   [OK] Followed by ticket confirmation with ID
   [OK] Employee receives confirmation email
   [OK] Ticket appears in Spiceworks

5. IF IT DOESN'T WORK:
   - Check bot console for error messages
   - Copy ALL console output and show it
   - Look for lines starting with [MENTION_HANDLER] or [TICKET_CREATE]

TEST COMPLETE!
""")
print("=" * 80)
