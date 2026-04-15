# Telegram Help Desk Bot - Commands Knowledge Base

## Table of Contents

1. [User Commands](#user-commands)
2. [Group Commands](#group-commands)
3. [Admin Commands](#admin-commands)
4. [User Management Commands](#user-management-commands-super-admin-only)
5. [Queue Management Commands](#queue-management-commands)
6. [Task Scheduling Commands](#task-scheduling-commands-admin-only)
7. [Status & Help Commands](#status--help-commands)
8. [Command Examples](#command-examples)

---

## User Commands

### `/start`

**Description:** Start creating a new support ticket (DM only)

**Who can use:** Any user sending a direct message to the bot

**What happens:**

1. Bot initiates a multi-step conversation to collect ticket information
2. Guides you through: name, email, department, priority, issue, description
3. Allows file/photo attachments
4. Creates ticket and sends confirmation with ticket ID

**Example:**

```
User: /start
Bot: Hello! I'll help you create a support ticket...
```

---

### `/register_email`

**Description:** Register your company email address with the bot

**Who can use:** Any user

**What happens:**

1. Opens email registration conversation
2. Prompts for company email
3. Saves email-to-user mapping
4. Used for automatic email confirmations on tickets

**Example:**

```
User: /register_email
Bot: Please enter your company email address
User: john.doe@company.com
Bot: Email registered successfully!
```

---

### `/my_email`

**Description:** Check what email address you have registered

**Who can use:** Any user

**What happens:**

- Shows registered email or message if not registered
- Can be used in DM or group

**Example:**

```
User: /my_email
Bot: Your registered email: john.doe@company.com
```

---

### `/lookup`

**Description:** Find all your tickets by searching with your email

**Who can use:** Any user (no login required)

**What happens:**

1. Opens lookup conversation
2. Asks for company email
3. Shows all tickets associated with that email
4. Displays ticket ID, status, priority, created date

**Example:**

```
User: /lookup
Bot: Enter your company email to lookup your tickets:
User: john.doe@company.com
Bot: Found 3 tickets for john.doe@company.com...
```

---

### `/cancel`

**Description:** Cancel the current conversation/operation

**Who can use:** Any user during a conversation

**What happens:**

- Exits current conversation flow
- Cancels any in-progress ticket creation
- Returns to normal state

**Example:**

```
User: (during ticket creation) /cancel
Bot: Cancelled.
```

---

## Group Commands

### `/my_tickets`

**Description:** View all your open support tickets

**Who can use:** Any user (in groups or DM)

**What happens:**

1. Searches for all tickets where you are the creator (by email)
2. Lists ticket ID, issue title, priority, status, created date
3. Shows up to 20 most recent tickets
4. Use `/ticket_status TICKET_ID` for details

**Example:**

```
User: /my_tickets
Bot: 📋 Found 3 open tickets:
    🎫 TKT-20260415105500
       Issue: Internet not working
       Priority: HIGH | Status: open
       Created: 2026-04-15
```

---

### `/ticket_status TICKET_ID`

**Description:** Get detailed information about a specific ticket

**Who can use:** Any user

**Parameters:**

- `TICKET_ID`: The ticket identifier (e.g., TKT-20260415105500)

**What happens:**

1. Retrieves full ticket details
2. Shows: name, email, department, issue, description, priority, status
3. Displays number of attachments
4. Shows file names and types

**Example:**

```
User: /ticket_status TKT-20260415105500
Bot: 📋 Ticket Details:
    ID: TKT-20260415105500
    Name: John Doe
    Email: john.doe@company.com
    Issue: Internet not working
    Priority: HIGH
    Status: open
```

---

### `/ticket_replies TICKET_ID`

**Description:** View all comments and updates on a ticket

**Who can use:** Any user who created the ticket or admins

**Parameters:**

- `TICKET_ID`: The ticket identifier

**What happens:**

1. Retrieves all replies and admin notes for the ticket
2. Shows: who replied, timestamp, message content
3. Lists replies in chronological order

**Example:**

```
User: /ticket_replies TKT-20260415105500
Bot: 📋 Ticket TKT-20260415105500 - Replies:
    1. John Doe - 2026-04-15 10:55
       Internet is down in the office
    2. Admin - 2026-04-15 11:10
       We're investigating. Checking with IT team.
```

---

### Group Mention Ticket Creation

**Description:** Create a ticket by mentioning the bot in a group

**Who can use:** Any group member

**Format:** `@bot_name your issue here`

**What happens:**

1. Bot detects mention in group message
2. Analyzes message for department keywords
3. Auto-assigns priority based on keywords
4. Creates ticket automatically
5. Replies with confirmation and ticket ID
6. No need to enter details step-by-step

**Example:**

```
User: @mevithelpdeskbot office wifi down in lobby
Bot: ✅ Ticket created!
    🎫 TKT-20260415111741
    Issue: office wifi down in lobby
    Department: IT
    Priority: HIGH
```

---

### Reply to Bot Messages

**Description:** Reply to a ticket confirmation message to add updates

**Who can use:** The ticket creator or admins (in groups)

**What happens:**

1. When bot posts ticket confirmation, you can reply to it
2. Reply is automatically added as a comment on the ticket
3. Admin can see all updates

**Example:**

```
Bot: 🎫 Ticket TKT-20260415105500 created...
User: (replies to this message) Please hurry, I can't access files
Bot: ✅ Update added to ticket TKT-20260415105500
```

---

## Admin Commands

**Note:** Admin commands require authentication. Use `/admin` to login with the admin password.

### `/admin`

**Description:** Login to the admin panel

**Who can use:** Super admins (user IDs in `.env ADMIN_USER_IDS`)

**What happens:**

1. Opens authentication conversation
2. Prompts for admin password (from `.env ADMIN_PASSWORD`)
3. Creates admin session if password correct
4. Shows admin menu upon successful login

**Example:**

```
User: /admin
Bot: 🔐 Admin Access
    Enter admin password:
User: mypassword123
Bot: ✅ Authenticated!
    📊 Admin Commands:
    /list - View all tickets
    /view {ticket_id} - View ticket details
    ...
```

---

### `/list`

**Description:** View all tickets in the system (admin only)

**Who can use:** Authenticated admins

**What happens:**

1. Displays all tickets (up to 20 most recent)
2. Shows ticket ID, issue, email, priority
3. Use `/view TICKET_ID` for full details

**Example:**

```
User: /list
Bot: 📋 All Tickets (147 total):
    🎫 TKT-20260415111741
       Issue: WiFi down in lobby
       john@company.com | HIGH
    🎫 TKT-20260415105500
       Issue: Screen flickering
       jane@company.com | NORMAL
```

---

### `/view TICKET_ID`

**Description:** View complete details of a specific ticket (admin only)

**Who can use:** Authenticated admins

**Parameters:**

- `TICKET_ID`: The ticket identifier

**What happens:**

1. Displays full ticket information
2. Shows all details: name, email, department, priority, status, description
3. Lists all attachments with file names and types
4. Shows creation timestamp

**Example:**

```
User: /view TKT-20260415105500
Bot: 📋 Ticket Details:
    ID: TKT-20260415105500
    Name: Jane Smith
    Email: jane@company.com
    Department: HR
    Priority: NORMAL
    Status: open
    Created: 2026-04-15 10:55
    Issue: Screen flickering on monitor
    Description: Monitor screen flickers when using Excel...
    Attachments: 1 file
    - screenshot.png (image)
```

---

### `/delete TICKET_ID`

**Description:** Delete a ticket from the system (admin only)

**Who can use:** Authenticated admins

**Parameters:**

- `TICKET_ID`: The ticket identifier

**What happens:**

1. Permanently removes the ticket
2. Confirmation message shows ticket was deleted
3. Logged in admin activity

**Example:**

```
User: /delete TKT-20260415105500
Bot: ✓ Ticket TKT-20260415105500 deleted.
```

---

### `/reply TICKET_ID MESSAGE`

**Description:** Add an admin note or reply to a ticket (admin only)

**Who can use:** Authenticated admins

**Parameters:**

- `TICKET_ID`: The ticket identifier
- `MESSAGE`: The reply text (everything after ticket ID)

**What happens:**

1. Adds your message as a reply to the ticket
2. Reply is timestamped and attributed to admin
3. User can see the update via `/ticket_replies TICKET_ID`

**Example:**

```
User: /reply TKT-20260415105500 We've fixed the monitor. Testing now.
Bot: ✓ Reply added to ticket TKT-20260415105500
```

---

### `/replies TICKET_ID`

**Description:** View all replies and comments on a ticket (admin only)

**Who can use:** Authenticated admins

**Parameters:**

- `TICKET_ID`: The ticket identifier

**What happens:**

1. Shows all replies on the ticket
2. Lists: who replied, timestamp, message
3. Shows in chronological order

**Example:**

```
User: /replies TKT-20260415105500
Bot: 📋 Ticket TKT-20260415105500 - Replies:
    1. Jane Smith - 2026-04-15 10:55
       Screen flickering on monitor
    2. Admin - 2026-04-15 11:20
       We'll check your monitor
    3. Admin - 2026-04-15 14:30
       Issue resolved. Monitor replaced.
```

---

### `/group_tickets` or `/group_tickets CHAT_ID`

**Description:** View all tickets from a specific group (admin only)

**Who can use:** Authenticated admins

**Parameters:**

- `CHAT_ID` (optional): Group ID to view tickets from. If not provided, uses current group

**What happens:**

1. Shows all tickets created in that group
2. Displays statistics: open, in-progress, completed ticket counts
3. Lists 5 most recent tickets
4. Use `/view TICKET_ID` for full details

**Example:**

```
User: /group_tickets
Bot: 📊 Tickets from "Engineering Team"
    Chat ID: -1001234567890
    
    Statistics:
    🔴 Open: 5
    🟡 In Progress: 2
    🟢 Completed: 18
    📊 Total: 25
    
    Recent Tickets (last 5):
    1. 🔴 TKT-20260415111741 - WiFi issue
    2. 🟡 TKT-20260415105500 - Monitor flickering
    ...
```

---

## User Management Commands (Super Admin Only)

**Note:** Only super admins (from `.env ADMIN_USER_IDS`) can use these commands. No password login needed - these commands check user ID directly.

### `/add_admin USER_ID`

**Description:** Add a new admin user to the system

**Who can use:** Super admins only (defined in `.env ADMIN_USER_IDS`)

**Parameters:**

- `USER_ID`: Telegram user ID of the person to make admin

**What happens:**

1. Adds user to the admin list
2. User can now use admin commands after `/admin` login
3. Changes persist in database until bot restart (or permanent if stored)
4. New admin receives no notification

**Example:**

```
User: /add_admin 123456789
Bot: ✅ Successfully added user 123456789 to admin list.
    They can now use admin commands: /list, /view, /delete, /reply, etc.
```

---

### `/remove_admin USER_ID`

**Description:** Remove an admin user from the system

**Who can use:** Super admins only

**Parameters:**

- `USER_ID`: Telegram user ID of the admin to remove

**What happens:**

1. Removes user from admin list
2. User can no longer use admin commands
3. Existing admin sessions are not terminated immediately
4. Changes persist
5. Cannot remove super admins (from `.env`)

**Example:**

```
User: /remove_admin 123456789
Bot: ✅ Successfully removed user 123456789 from admin list.
    They can no longer use admin commands.
```

---

### `/list_admins`

**Description:** View all current admin users

**Who can use:** Super admins only

**What happens:**

1. Shows all admins in two categories:
   - 🔒 Super Admins (from `.env`, cannot be removed)
   - 👤 Dynamic Admins (can be removed via `/remove_admin`)
2. Lists user IDs

**Example:**

```
User: /list_admins
Bot: 👨‍💼 Admin Users:
    
    🔒 Super Admins (from .env - cannot be removed):
      • 7998468970
      • 5139651410
    
    👤 Dynamic Admins (can be removed):
      • 123456789
      • 987654321
    
    Total: 4 admin(s)
```

---

### `/add_it_member USER_ID`

**Description:** Add a user to the IT team (for reaction-based ticket creation)

**Who can use:** Super admins only

**Parameters:**

- `USER_ID`: Telegram user ID of the IT team member

**What happens:**

1. Adds user to IT team list
2. User can now create tickets by reacting to messages
3. When they react with configured emoji, ticket is created
4. Changes persist
5. IT team members don't need admin password

**Example:**

```
User: /add_it_member 111111111
Bot: ✅ Successfully added user 111111111 to IT team.
    They can now create tickets via reactions.
```

---

### `/remove_it_member USER_ID`

**Description:** Remove a user from the IT team

**Who can use:** Super admins only

**Parameters:**

- `USER_ID`: Telegram user ID of the IT team member to remove

**What happens:**

1. Removes user from IT team list
2. User can no longer create tickets via reactions
3. Cannot remove super IT members (from `.env`)
4. Changes persist

**Example:**

```
User: /remove_it_member 111111111
Bot: ✅ Successfully removed user 111111111 from IT team.
    They can no longer create tickets via reactions.
```

---

### `/list_it_members`

**Description:** View all IT team members

**Who can use:** Super admins only

**What happens:**

1. Shows all IT team members in two categories:
   - 🔒 Super IT Members (from `.env`, cannot be removed)
   - 👤 Dynamic IT Members (can be removed)
2. Lists user IDs

**Example:**

```
User: /list_it_members
Bot: 👨‍💻 IT Team Members:
    
    🔒 Super IT Members (from .env - cannot be removed):
      • 5139651410
      • 7998468970
    
    👤 Dynamic IT Members (can be removed):
      • 111111111
    
    Total: 3 IT member(s)
```

---

## Queue Management Commands

**Note:** These commands only work if `QUEUE_ENABLED=true` in `.env`

### `/my_position`

**Description:** Check your position in the ticket request queue

**Who can use:** Any user

**What happens:**

1. Shows your current position in queue
2. Displays total queue size
3. Estimates wait time in minutes
4. Shows message if you're not in queue

**Example:**

```
User: /my_position
Bot: 📍 Your Queue Status:
    Position: #3 of 15
    Estimated Wait: ~12 minutes
    Your request will be processed shortly.
```

---

### `/queue_status`

**Description:** View overall queue statistics (admin only)

**Who can use:** Authenticated admins (or users in `ADMIN_USER_IDS`)

**What happens:**

1. Shows queue statistics
2. Displays: total requests, queued, processing, completed, failed counts
3. Overall queue health status

**Example:**

```
User: /queue_status
Bot: 📊 Queue Status:
    📋 Total Requests: 145
    ⏳ Queued: 12
    ⚙️ Processing: 1
    ✅ Completed: 128
    ❌ Failed: 4
    Queue is operating normally.
```

---

## Task Scheduling Commands (Admin Only)

**Note:** Requires admin authentication. Use `/admin` to login first.

### `/schedule`

**Description:** Create a scheduled task (admin only)

**Who can use:** Authenticated admins

**What happens:**

1. Opens task scheduling conversation
2. Prompts for task type (Create Ticket, Send Message)
3. Asks for schedule type (One-time, Daily, Weekly, Monthly, Custom Cron)
4. Collects required parameters based on task type
5. Shows confirmation before creating

**Schedule Types:**

- **One-time**: Run once at specific date/time
- **Daily**: Run at same time every day
- **Weekly**: Run on specific day(s) each week
- **Monthly**: Run on specific day each month
- **Custom Cron**: Advanced scheduling with cron expressions

**Example:**

```
User: /schedule
Bot: 🗓️ Schedule a Task
    What would you like to schedule?
    [📝 Create Ticket] [💬 Send Message] [❌ Cancel]
```

---

### `/tasks`

**Description:** List all scheduled tasks (admin only)

**Who can use:** Authenticated admins

**What happens:**

1. Shows all scheduled tasks
2. Displays: task ID, type, schedule type, next run time
3. Shows 20 most recent tasks
4. Use `/delete TASK_ID` to remove a task

**Example:**

```
User: /tasks
Bot: 📋 Scheduled Tasks (5 total):
    1. Task-001: Create Ticket - Daily @ 09:00
       Next run: 2026-04-16 09:00
    2. Task-002: Send Message - One-time
       Next run: 2026-04-15 15:30
    ...
```

---

### `/delete TASK_ID`

**Description:** Delete a scheduled task (admin only)

**Who can use:** Authenticated admins

**Parameters:**

- `TASK_ID`: The task identifier

**What happens:**

1. Cancels the scheduled task
2. Task will no longer run
3. Confirmation message shows task was deleted

**Example:**

```
User: /delete Task-001
Bot: ✓ Scheduled task Task-001 deleted.
```

---

## Status & Help Commands

### `/help`

**Description:** Show all available commands and features

**Who can use:** Any user

**What happens:**

1. Shows comprehensive command list
2. Organizes commands by category
3. In DM: Shows all commands including admin commands
4. In group: Shows group-specific commands
5. Displays features and company info

**Example:**

```
User: /help
Bot: 📋 Help Desk Bot Commands

📧 User Commands:
  /start - Create a new support ticket
  /register_email - Register your company email
  ...
```

---

### `/status`

**Description:** Check the bot's health status

**Who can use:** Any user

**What happens:**

1. Shows bot online status
2. Displays bot name and username
3. Shows company name
4. Shows support email

**Example:**

```
User: /status
Bot: Bot Status: Online
    Bot: MeVit Help Desk Bot (@mevithelpdeskbot)
    Company: Marquis Events Place Inc
    Support Email: marxcorde@gmail.com
```

---

## Command Examples

### Example 1: Creating a Ticket via DM

```
1. User: /start
2. Bot: What's your name?
3. User: John Doe
4. Bot: What's your email?
5. User: john.doe@company.com
6. User chooses department, priority
7. User describes issue and uploads screenshot
8. Bot: ✅ Ticket TKT-20260415105500 created!
```

### Example 2: Creating a Ticket via Group Mention

```
1. User: @mevithelpdeskbot office printer not working in 3rd floor
2. Bot: ✅ Ticket created!
   🎫 TKT-20260415111741
   Issue: office printer not working in 3rd floor
   Department: IT (auto-detected)
   Priority: HIGH (auto-assigned based on keywords)
```

### Example 3: Admin Checking Tickets

```
1. User: /admin
2. User: (enters password)
3. User: /list
4. Bot: Shows all tickets
5. User: /view TKT-20260415105500
6. Bot: Shows full ticket details
7. User: /reply TKT-20260415105500 Printer cartridge replaced
8. Bot: Reply added successfully
```

### Example 4: Super Admin Managing Users

```
1. User: /list_admins
2. Bot: Shows current admins
3. User: /add_admin 123456789
4. Bot: User 123456789 added as admin
5. User: /add_it_member 111111111
6. Bot: User 111111111 added to IT team
```

### Example 5: Scheduling a Task

```
1. User: /schedule
2. Bot: What task? [Create Ticket] [Send Message]
3. User: (selects Create Ticket)
4. Bot: When should it run? [One-time] [Daily] [Weekly] ...
5. User: (selects Daily)
6. Bot: What time? 09:00
7. Bot: Ticket details? (collects info)
8. Bot: ✅ Task scheduled for daily at 09:00
```

---

## Tips & Best Practices

1. **Email Registration**: Register your email first with `/register_email` for automatic confirmations
2. **Ticket ID Format**: Always use `TKT-` prefix when referencing ticket IDs
3. **Group Mentions**: Include relevant keywords like "urgent", "asap", "issue" for proper priority assignment
4. **Admin Password**: Keep admin password secure and change it regularly
5. **File Attachments**: Supported formats: JPG, JPEG, PNG, PDF, DOC, DOCX (max 10 files, 10MB each)
6. **Super Admin Protection**: Super admins from `.env` cannot be removed - they're permanent
7. **Queue System**: If enabled, check `/my_position` to see when your tickets will be processed
8. **Task Scheduling**: Use cron expressions for complex schedules (e.g., "0 9 ** MON" = every Monday at 9 AM)

---

## Error Messages & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| ❌ Access denied. Use /admin to login | Not authenticated | Run `/admin` and enter password |
| ❌ Invalid password | Wrong password entered | Check `.env` for `ADMIN_PASSWORD` |
| ❌ Ticket not found | Invalid ticket ID | Use `/my_tickets` to find valid IDs |
| ❌ Must be in DM | Using `/start` in group | Use `/start` in direct message only |
| ❌ Invalid email | Email format error | Use valid email format (<user@domain.com>) |
| Permission denied | Not a super admin | Super admin user IDs in `.env` only |
| ❌ Description too short | Less than minimum length | Provide at least 10 characters |

---

## Configuration Reference

The following settings in `.env` affect command availability:

- `ADMIN_USER_IDS`: User IDs who are super admins
- `ADMIN_PASSWORD`: Password required to `/admin` login
- `IT_TEAM_USER_IDS`: User IDs who can create tickets via reactions
- `QUEUE_ENABLED`: Enable/disable `/my_position` and `/queue_status`
- `REACTION_TICKET_ENABLED`: Enable/disable reaction-based ticket creation
- `TICKET_REACTION_TRIGGERS`: Which emoji reactions create tickets (e.g., 👍)
- `MAX_MESSAGE_LENGTH`: Max characters in messages
- `MAX_FILE_SIZE_MB`: Max file upload size
- `MAX_ATTACHMENTS_PER_TICKET`: Max files per ticket

---

## Support

For issues or questions about commands:

- Use `/help` to view all available commands
- Check `/status` to confirm bot is working
- Contact support at: {SUPPORT_EMAIL from settings}

Last updated: April 15, 2026
