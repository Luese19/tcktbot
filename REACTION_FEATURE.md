---
name: Reaction-Based Ticket Creation Feature
description: IT team members react to messages to create support tickets in Spiceworks
type: project
---

## Feature Overview

IT team members can now react to employee messages in Telegram groups with specific emoji reactions. When they do, a support ticket is automatically created in Spiceworks.

### How It Works

1. **Employee sends a message** in a Telegram group describing an issue
2. **IT team member reacts** with a configured emoji (👍, 🎫, or ✅ by default)
3. **Bot detects the reaction** and automatically creates a ticket in Spiceworks
4. **Notifications are sent** to:
   - IT team member (confirmation with ticket ID)
   - Employee (group message with ticket ID)

### Configuration

**In `.env` file:**

```env
# Enable/disable the feature
REACTION_TICKET_ENABLED=true

# Comma-separated list of IT team member Telegram user IDs
IT_TEAM_USER_IDS=123456789,987654321

# Reactions that trigger ticket creation (emoji only)
TICKET_REACTION_TRIGGERS=🎫,👍,✅
```

### Setup Steps

1. **Get IT team member IDs:**
   - Each IT team member needs to know their Telegram user ID
   - They can get it by messaging `@userinfobot` on Telegram
   - Or by reacting to any message once, then checking bot logs for their ID

2. **Add to configuration:**

   ```env
   IT_TEAM_USER_IDS=ID1,ID2,ID3
   REACTION_TICKET_ENABLED=true
   TICKET_REACTION_TRIGGERS=🎫,👍,✅
   ```

3. **Restart the bot:**

   ```bash
   python bot/main.py
   ```

### Ticket Creation Details

**Automatic department detection** based on keywords:

- IT: computer, laptop, printer, network, wifi, server, password, email, access, vpn
- Maintenance: repair, broken, plumbing, electrical, heating, cooling
- HR: payroll, benefits, leave, vacation, training, recruitment
- Accounting: invoice, payment, receipt, finance, budget, expense
- Operations: supply, stock, inventory, schedule, logistics
- Facilities: office, room, building, cleanup, equipment

**Priority auto-assignment** per department with keyword-based escalation

**Ticket ID format:** `RTK-{chat_id}-{message_id}`

### Example Usage

**In a Telegram group:**

```
Employee: @bot My printer is offline and won't print
[IT member reacts with 🎫]
→ Bot automatically creates ticket RTK-123456-789
→ IT member gets: ✅ Ticket Created Successfully! Ticket ID: RTK-123456-789
→ Employee gets: 🎫 Your issue has been registered as a support ticket!
→ Ticket sent to Spiceworks
```

### Features

✅ Only IT team members can trigger tickets  
✅ Multiple reaction types configurable  
✅ Works in groups and supergroups  
✅ Auto-detects department and priority  
✅ Notifications to both IT and employee  
✅ Message content automatically extracted  
✅ Mentions/usernames cleaned from issue text  
✅ Thread-safe ticket creation  
✅ Comprehensive logging for debugging  

### Logging

Check logs for reaction-based activity:

```bash
tail -f logs/bot.log | grep REACTION
```

**Log examples:**

- `[REACTION HANDLER] Reaction detected` - Reaction received
- `[REACTION] IT team member {id} reacted` - Valid IT team member
- `[REACTION] Ticket created successfully` - Ticket created
- `[REACTION] User {id} is not an IT team member` - Unauthorized user

### Troubleshooting

**Reactions not triggering tickets:**

1. Check `REACTION_TICKET_ENABLED=true` in .env
2. Verify user ID is in `IT_TEAM_USER_IDS`
3. Confirm reaction emoji is in `TICKET_REACTION_TRIGGERS`
4. Check logs: `grep REACTION logs/bot.log`

**Getting user ID:**

- Message `@userinfobot` on Telegram
- Or react to any message and check bot logs

**Feature disabled by default:**
Set `REACTION_TICKET_ENABLED=true` in .env to enable
