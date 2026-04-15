# Quick Command Reference Guide

## 📋 All Commands at a Glance

### 👤 User Commands (Everyone)

| Command | Purpose | Example |
|---------|---------|---------|
| `/start` | Create new ticket | `/start` |
| `/register_email` | Register company email | `/register_email` |
| `/my_email` | Check registered email | `/my_email` |
| `/lookup` | Find tickets by email | `/lookup` |
| `/cancel` | Cancel current operation | `/cancel` |
| `/help` | Show all commands | `/help` |
| `/status` | Check bot status | `/status` |

### 📌 Ticket Queries (Everyone)

| Command | Purpose | Example |
|---------|---------|---------|
| `/my_tickets` | View your open tickets | `/my_tickets` |
| `/ticket_status` | Get ticket details | `/ticket_status TKT-123456` |
| `/ticket_replies` | View ticket updates | `/ticket_replies TKT-123456` |

### 🎯 Group Features (Everyone)

| Feature | How to Use | Example |
|---------|-----------|---------|
| Mention bot | Create ticket via mention | `@bot your issue` |
| Reply to message | Add update to ticket | Reply to bot's message |

### 🔐 Admin Commands (Requires `/admin` login)

| Command | Purpose | Example |
|---------|---------|---------|
| `/admin` | Login to admin panel | `/admin` |
| `/list` | View all tickets | `/list` |
| `/view` | View ticket details | `/view TKT-123456` |
| `/delete` | Delete a ticket | `/delete TKT-123456` |
| `/reply` | Add admin note | `/reply TKT-123456 Fixed!` |
| `/replies` | View ticket replies | `/replies TKT-123456` |
| `/group_tickets` | View group tickets | `/group_tickets` |

### 👥 Super Admin Only (No password needed, based on user ID)

| Command | Purpose | Example |
|---------|---------|---------|
| `/add_admin` | Add new admin | `/add_admin 123456789` |
| `/remove_admin` | Remove admin | `/remove_admin 123456789` |
| `/list_admins` | View all admins | `/list_admins` |
| `/add_it_member` | Add IT team member | `/add_it_member 111111111` |
| `/remove_it_member` | Remove IT team member | `/remove_it_member 111111111` |
| `/list_it_members` | View IT team members | `/list_it_members` |

### ⏰ Task Scheduling (Requires `/admin` login)

| Command | Purpose | Example |
|---------|---------|---------|
| `/schedule` | Create scheduled task | `/schedule` |
| `/tasks` | List scheduled tasks | `/tasks` |
| `/delete` | Delete task | `/delete Task-001` |

### 📊 Queue Management (If enabled)

| Command | Purpose | Who Uses | Example |
|---------|---------|---------|---------|
| `/my_position` | Check queue position | Anyone | `/my_position` |
| `/queue_status` | View queue stats | Admins | `/queue_status` |

---

## 🎯 Common Use Cases

### I want to create a ticket

**Option 1 - Direct Message:**

```
/start → Fill in details → Get ticket ID
```

**Option 2 - In Group:**

```
@bot my issue here → Instant ticket created
```

---

### I want to check my ticket status

```
/my_tickets → Find ticket ID → /ticket_status TKT-xxxxx
```

---

### I want to add a comment to my ticket

```
Reply to the bot's ticket message in the group
```

---

### I'm an admin and want to see all tickets

```
/admin → Enter password → /list → /view TKT-xxxxx
```

---

### I'm a super admin and want to add another admin

```
/add_admin 123456789 → Done! They can now login with /admin
```

---

### I'm an IT person and want to create tickets via reactions

**1. Super admin adds you:**

```
/add_it_member YOUR_USER_ID
```

**2. You create tickets by:**

```
React with configured emoji (e.g., 👍) to any message
Ticket is created automatically
```

---

### I want to schedule an automated task

```
/admin → Enter password → /schedule
Select task type (Create Ticket / Send Message)
Select schedule type (One-time / Daily / Weekly / Monthly / Cron)
Fill in details → Confirm
```

---

## 📝 Parameter Reference

### TICKET_ID

Format: `TKT-20260415105500`

- Unique identifier for each ticket
- Created automatically
- Find with `/my_tickets`

### USER_ID

Format: `123456789` (numeric)

- Telegram user ID
- Used for admin/IT team management
- Find in bot logs or ask Telegram for your ID

### TASK_ID

Format: `Task-001` (alphanumeric)

- Unique identifier for scheduled tasks
- Created during `/schedule`
- View with `/tasks`

### CHAT_ID

Format: `-1001234567890` (usually negative)

- Group/channel identifier
- Use with `/group_tickets CHAT_ID`
- Optional if already in the group

---

## 🚀 Getting Started Checklist

- [ ] `/start` to understand the flow
- [ ] `/register_email` to register your email
- [ ] Create first ticket (via `/start` or group mention)
- [ ] `/my_tickets` to see your tickets
- [ ] `/ticket_status TKT-xxxxx` to check status
- [ ] `/help` to explore all commands

---

## ⚡ Tips & Tricks

| Tip | How | Benefit |
|-----|-----|---------|
| Auto-priority | Use keywords like "urgent", "asap" | Faster response for critical issues |
| Email link | Register email with `/register_email` | Get email confirmations on updates |
| File uploads | Attach screenshots/documents | Better bug reporting |
| Group replies | Reply to bot's message | Easy ticket updates |
| Queue position | `/my_position` when queue enabled | Know wait time |
| Reactions (IT) | React to messages in group | Create tickets instantly |

---

## 🔒 Admin Tips

1. **Manage admins dynamically:** Use `/add_admin` and `/remove_admin` instead of restarting bot

2. **View statistics:** Use `/group_tickets` to see team's workload

3. **Queue monitoring:** `/queue_status` shows processing health

4. **Task automation:** `/schedule` to automate repetitive tickets

5. **Quick access:** Bookmark these in Telegram favorites:
   - `/admin` - Quick login
   - `/list` - See all tickets
   - `/my_position` - Check queue

---

## ❌ Common Issues

| Issue | Solution |
|-------|----------|
| Can't create ticket in group | Use `/start` in DM, or mention bot: `@bot issue` |
| Admin login failed | Check password with super admin |
| Ticket not found | Use `/my_tickets` to find correct ID |
| IT member can't react | Ask super admin to run `/add_it_member YOUR_ID` |
| Queue commands missing | Super admin needs to enable `QUEUE_ENABLED=true` in `.env` |

---

## 📞 Support

- **General Help:** `/help`
- **Bot Status:** `/status`
- **Ticket Lookup:** `/lookup`
- **Manual:** See `COMMANDS_KNOWLEDGE_BASE.md` for detailed docs

---

## Keyboard Shortcuts (In Progress)

*Coming soon: Quick access buttons for common commands*

---

Last updated: April 15, 2026
Version: 1.0
