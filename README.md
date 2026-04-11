# Telegram Help Desk Bot 🎫

A professional Telegram bot for creating and managing support tickets with intelligent routing, file attachments, and admin management.

## Features ✨

- **Ticket Creation** - Users submit support requests with validation
- **Field Validation** - Name, issue, and description length checks
- **File Attachments** - Support for images (JPG, PNG) and documents (PDF, DOCX)
- **HTML Emails** - Professional formatted emails to Spiceworks
- **Auto-Priority Routing** - Intelligent priority assignment based on department and keywords
- **Ticket Lookup** - Users can check their tickets by email
- **Admin Panel** - Full ticket management with authentication
- **Ticket Replies** - Add notes and comments to tickets
- **Error Recovery** - Automatic retry with exponential backoff
- **Spiceworks Integration** - Direct email integration with Spiceworks ticketing system

## Setup 🚀

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Telegram Bot Token (from @BotFather)
- Gmail App Password for email sending

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ticketingbot.git
cd ticketingbot
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure .env file**
```
TELEGRAM_BOT_TOKEN=your_token
COMPANY_NAME=Your Company
COMPANY_EMAIL_DOMAIN=company.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SPICEWORKS_EMAIL=support@company.com
ADMIN_PASSWORD=secure_password
```

5. **Run the bot**
```bash
python bot/main.py
```

## Commands 📖

### User Commands
- `/start` - Create new ticket
- `/lookup` - Check your tickets
- `/help` - Show help
- `/status` - Bot status

### Admin Commands (after `/admin`)
- `/list` - View all tickets
- `/view {id}` - View ticket
- `/delete {id}` - Delete ticket
- `/reply {id} {msg}` - Add note
- `/replies {id}` - View notes

## Project Structure

```
ticketingbot/
├── bot/
│   ├── config/          # Configuration
│   ├── handlers/        # Command handlers
│   ├── services/        # Business logic
│   ├── utils/           # Utilities
│   ├── data/            # Ticket storage
│   └── main.py          # Entry point
├── .gitignore
├── .env                 # (Not committed)
├── requirements.txt
└── README.md
```

## Configuration

Create `.env` file with:
- `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather
- `COMPANY_NAME` - Your company name
- `COMPANY_EMAIL_DOMAIN` - Company email domain
- `ADMIN_PASSWORD` - Admin panel password
- SMTP settings for email

For Gmail: Use App Password, not regular password

## Features

### Auto-Priority Routing
Automatically assigns priority based on department:
- IT: HIGH by default, URGENT for "server down"
- HR: NORMAL by default
- Maintenance: HIGH by default

### Ticket Storage
Tickets stored as JSON in `bot/data/tickets/`

### Email Integration
- HTML formatted emails
- File attachments
- Spiceworks integration

## Troubleshooting

- **Bot not responding**: Check logs and TELEGRAM_BOT_TOKEN
- **Emails not sending**: Verify SMTP credentials and use Gmail App Password
- **File upload issues**: Check MAX_FILE_SIZE_MB and file format

## Security

- Never commit `.env` file
- Use strong admin passwords
- Use Gmail App Passwords for SMTP
- Review logs regularly

## License

MIT License

---

Made with ❤️ for efficient ticketing
