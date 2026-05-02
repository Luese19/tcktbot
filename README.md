# Telegram Help Desk Ticketing Bot

A comprehensive Telegram bot for creating and managing help desk tickets, integrated with Spiceworks via email. Supports multiple ticket creation methods, admin management, scheduling, and team collaboration.

## Features

- **Multiple Ticket Creation Methods**:
  - `/start` conversation flow for guided ticket creation
  - Group mentions: `@bot issue description`
  - Reaction-based tickets (configurable emoji triggers like 🎫, 👍, ✅)
  - Media and file attachments support

- **Admin Management**:
  - Super admin configuration via environment variables
  - Dynamic admin addition/removal
  - Ticket lookup and management (`/lookup`, `/admin`)
  - User management commands (`/add_admin`, `/remove_admin`)

- **Email Integration**:
  - SMTP integration for sending tickets to Spiceworks
  - Company email domain validation
  - Automatic ticket routing based on department and keywords

- **Scheduling & Automation**:
  - Task scheduling with `/schedule`
  - Monthly cleanup scheduler
  - Queue system for group mentions with timeouts

- **Team Collaboration**:
  - IT team user management
  - Private welcome messages for registered employees
  - Message caching for reaction lookups
  - Group command handlers

- **Security & Reliability**:
  - Single instance management to prevent conflicts
  - File upload limits and validation
  - Conversation timeouts
  - Comprehensive logging

## Prerequisites

- Python 3.8+
- Telegram Bot Token (obtain from [@BotFather](https://t.me/botfather))
- SMTP server access for email integration
- Spiceworks email configuration for external ticketing

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ticketing-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment configuration**:
   Create a `.env` file in the root directory with the following variables:

   ```env
   # Bot Configuration
   TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

   # Company Settings
   COMPANY_NAME=Your Company Name
   COMPANY_EMAIL_DOMAIN=company.com

   # Email/SMTP Configuration
   SMTP_SERVER=smtp.company.com
   SMTP_PORT=587
   SMTP_USERNAME=helpdesk@company.com
   SMTP_PASSWORD=your_smtp_password
   SMTP_USE_TLS=true
   SPICEWORKS_EMAIL=helpdesk@company.com

   # Admin Configuration (comma-separated Telegram user IDs)
   ADMIN_USER_IDS=123456789,987654321

   # Optional IT Team (comma-separated Telegram user IDs)
   IT_TEAM_USER_IDS=111222333,444555666

   # Application Settings
   LOG_LEVEL=INFO
   LOG_FILE_PATH=./logs/bot.log
   MAX_MESSAGE_LENGTH=4000
   CONVERSATION_TIMEOUT_MINUTES=30
   MAX_FILE_SIZE_MB=10
   MAX_ATTACHMENTS_PER_TICKET=5
   ADMIN_PASSWORD=admin123

   # Field Validation
   MIN_NAME_LENGTH=2
   MAX_NAME_LENGTH=100
   MIN_ISSUE_LENGTH=5
   MAX_ISSUE_LENGTH=200
   MIN_DESCRIPTION_LENGTH=10
   MAX_DESCRIPTION_LENGTH=2000

   # Queue Settings
   QUEUE_ENABLED=true
   QUEUE_TIMEOUT_MINUTES=30
   REQUEST_TIMEOUT_MINUTES=60
   CONCURRENT_TICKET_CREATION=1

   # Reaction-Based Tickets
   REACTION_TICKET_ENABLED=false
   TICKET_REACTION_TRIGGERS=🎫,👍,✅
   ```

## Configuration

### Required Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather
- `ADMIN_USER_IDS`: Comma-separated list of Telegram user IDs with super admin privileges

### Email Configuration

- `SMTP_SERVER`: Your SMTP server hostname
- `SMTP_USERNAME`/`SMTP_PASSWORD`: SMTP authentication credentials
- `SPICEWORKS_EMAIL`: Email address where tickets will be sent

### Department Configuration

Departments are configured in `config/departments.py`. Current departments include:
- HR, Operations, Purchasing, Sales, Accounting
- Warehouse, Kitchen, Admin Office, Catering
- Stewards, Maintenance, IT

### Priority Auto-Routing

Tickets are automatically prioritized based on department and keywords:
- IT tickets default to HIGH priority
- HR complaints and urgent requests get elevated priority
- Keyword matching for "urgent", "down", "server", etc.

## Usage

### For Users

1. **Register your email** (if required):
   ```
   /register_email
   ```

2. **Create ticket via conversation**:
   ```
   /start
   ```
   Follow the guided prompts to select department, provide details, and submit.

3. **Create ticket in groups**:
   ```
   @YourBot I need help with my computer
   ```

4. **View your tickets**:
   ```
   /my_tickets
   ```

5. **Get help**:
   ```
   /help
   ```

### For Admins

1. **Login to admin panel**:
   ```
   /admin
   ```

2. **Add/remove admins**:
   ```
   /add_admin <user_id>
   /remove_admin <user_id>
   ```

3. **Lookup user tickets**:
   ```
   /lookup <user_id>
   ```

4. **Schedule tasks**:
   ```
   /schedule
   ```

5. **View bot status**:
   ```
   /status
   ```

### For IT Team

- React to messages with configured emojis (🎫, 👍, ✅) to create tickets
- Access admin commands for ticket management

## Deployment

### Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

2. **Environment setup**:
   Create a `.env` file as described in Installation section.

3. **Single instance management**:
   The bot includes process management to prevent multiple instances.

### Manual Deployment

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   Set up `.env` file with all required variables.

3. **Run the bot**:
   ```bash
   python main.py
   ```

### Production Considerations

- Use a process manager like systemd or supervisor
- Configure log rotation for `./logs/bot.log`
- Set up monitoring for the bot process
- Ensure data directories (`./data`) are backed up regularly
- Configure firewall rules for SMTP access

## Architecture Overview

### Handler Priority Groups

The bot uses prioritized handler groups for proper message processing:

- **Group -99**: Message caching (lowest priority)
- **Group -1**: Reaction-based ticket creation (highest user priority)
- **Group 0**: Group mentions, media, confirmations, private welcomes
- **Group 1**: Email registration
- **Group 2**: Main conversation handler
- **Group 3**: Admin and lookup handlers
- **Group 4**: General commands

### Service Layer

- **EmployeeService**: User registration and welcome status
- **TicketService**: Ticket creation, management, and email sending
- **UserManagerService**: Admin and IT team user management
- **MessageCacheService**: Group message caching for reactions
- **SchedulerManager**: Task scheduling and cleanup

### Data Flow

1. User interaction → Handler processing
2. Data validation → Service layer processing
3. Ticket creation → Email sending to Spiceworks
4. Admin notifications → Telegram messages

### Key Components

- `main.py`: Application entry point and handler registration
- `handlers/`: Individual handler modules for different functionalities
- `services/`: Business logic and data management
- `config/`: Configuration management and department settings
- `utils/`: Logging, scheduling, and utility functions
- `data/`: Persistent data storage (tickets, employees, etc.)

## API Reference

### User Commands

- `/start`: Begin ticket creation conversation
- `/help`: Display help information
- `/my_tickets`: View user's tickets
- `/register_email`: Register company email
- `/my_email`: Check registered email
- `/ticket_status <ticket_id>`: Check ticket status
- `/ticket_replies <ticket_id>`: View ticket replies
- `/status`: Show bot status

### Admin Commands

- `/admin`: Access admin panel
- `/lookup <user_id>`: Search user tickets
- `/add_admin <user_id>`: Add admin user
- `/remove_admin <user_id>`: Remove admin user
- `/add_it_member <user_id>`: Add IT team member
- `/remove_it_member <user_id>`: Remove IT team member
- `/list_admins`: List all admin users
- `/list_it_members`: List all IT team members
- `/list`: List all tickets
- `/view <ticket_id>`: View specific ticket
- `/delete <ticket_id>`: Delete ticket
- `/reply <ticket_id>`: Reply to ticket
- `/replies <ticket_id>`: View ticket replies
- `/group_tickets`: View group tickets

### Scheduling Commands

- `/schedule`: Schedule automated tasks
- `/tasks`: List scheduled tasks
- `/delete <task_id>`: Delete scheduled task

### Queue Commands

- `/queue_status`: View queue status (admins)
- `/my_position`: Check your position in queue

### Handler Responsibilities

- **ConversationHandler**: Guided ticket creation flow
- **MentionHandler**: Group mention processing and queue management
- **ReactionHandler**: Emoji-based ticket creation
- **AdminHandler**: Administrative functions and user management
- **EmailRegistrationHandler**: User email registration
- **PrivateWelcomeHandler**: Welcome messages for registered employees

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install dependencies: `pip install -r requirements.txt`
4. Make changes following the existing code structure
5. Test thoroughly with different scenarios
6. Submit a pull request

### Code Structure

- Use type hints and docstrings
- Follow PEP 8 style guidelines
- Add logging with `get_logger(__name__)`
- Handle exceptions appropriately
- Test file uploads and email sending

### Testing Guidelines

- Test ticket creation through all methods
- Verify email integration works correctly
- Test admin commands and permissions
- Check conversation timeouts and error handling
- Validate file upload limits

## License

This project is licensed under the MIT License.

## Troubleshooting

### Common Issues

1. **Bot not responding**:
   - Check TELEGRAM_BOT_TOKEN is correct
   - Verify bot is not blocked by Telegram
   - Check logs for error messages

2. **Email not sending**:
   - Verify SMTP settings in .env
   - Check SMTP server connectivity
   - Ensure credentials are correct

3. **Admin commands not working**:
   - Confirm ADMIN_USER_IDS contains your user ID
   - Check user ID format (should be numeric)

4. **File uploads failing**:
   - Check MAX_FILE_SIZE_MB setting
   - Verify file type is supported
   - Ensure data directory permissions

### Logs

Check `./logs/bot.log` for detailed error information and debugging messages.