"""Group-specific command handlers for ticket queries and management"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from utils.logger import get_logger
from services.ticket_service import TicketService
from services.employee_service import EmployeeService
from config.settings import settings

logger = get_logger(__name__)


class GroupCommandHandlers:
    """Handlers for group-specific commands"""

    @staticmethod
    async def my_tickets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's tickets via /my_tickets command"""
        try:
            user_id = update.effective_user.id
            user_email = None

            # Try to get registered email first
            registered_email = EmployeeService.get_employee_email(user_id)
            if registered_email:
                user_email = registered_email
            else:
                # Generate email from user ID if not registered
                user_email = f"user.{user_id}@{settings.company.EMAIL_DOMAIN}"

            # Get user's tickets
            user_tickets = TicketService.get_tickets_by_user_email(user_email)

            if not user_tickets:
                await update.message.reply_text(
                    "📭 You have no tickets yet.\n\n"
                    "Create one by:\n"
                    "• Mentioning me in a group (e.g., @bot my issue)\n"
                    "• Using /start in a DM"
                )
                return

            # Show last 5 tickets
            response = f"🎫 Your Tickets ({len(user_tickets)} total, showing last 5):\n\n"
            for ticket in user_tickets[:5]:
                status_emoji = {
                    "open": "🔴",
                    "in_progress": "🟡",
                    "completed": "🟢"
                }.get(ticket.get('status', 'open'), "⚪")

                created_date = ticket.get('created_at', 'N/A')[:10]

                response += (
                    f"{status_emoji} **{ticket.get('ticket_id')}**\n"
                    f"   Issue: {ticket.get('issue', 'N/A')[:40]}\n"
                    f"   Status: {ticket.get('status', 'open').capitalize()} | "
                    f"Priority: {ticket.get('priority', 'N/A')} | "
                    f"Created: {created_date}\n\n"
                )

            response += f"Use `/ticket_status {{ticket_id}}` for details"
            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in my_tickets_command: {e}", exc_info=True)
            await update.message.reply_text("❌ Error retrieving your tickets.")

    @staticmethod
    async def ticket_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show ticket status via /ticket_status command"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "📋 Ticket Status Lookup\n\n"
                    "Usage: `/ticket_status {ticket_id}`\n"
                    "Example: `/ticket_status TKT-20260410225504`",
                    parse_mode="Markdown"
                )
                return

            ticket_id = context.args[0].upper()

            # Validate ticket ID format
            if not ticket_id.startswith("TKT-"):
                await update.message.reply_text(
                    f"❌ Invalid ticket ID format. Expected format: TKT-YYYYMMDDHHMMSS\n"
                    f"You provided: {ticket_id}"
                )
                return

            ticket = TicketService.get_ticket(ticket_id)

            if not ticket:
                await update.message.reply_text(f"❌ Ticket {ticket_id} not found.")
                return

            # Format status with emoji
            status_emoji = {
                "open": "🔴",
                "in_progress": "🟡",
                "completed": "🟢"
            }.get(ticket.get('status', 'open'), "⚪")

            # Build response
            created_date = ticket.get('created_at', 'N/A')[:10]
            updated_date = ticket.get('updated_at', ticket.get('created_at', 'N/A'))[:10]

            response = f"""📋 **Ticket Details**

**ID:** `{ticket.get('ticket_id')}`
{status_emoji} **Status:** {ticket.get('status', 'open').capitalize()}
**Priority:** {ticket.get('priority', 'N/A')}
**Department:** {ticket.get('department', 'N/A')}

**Issue:** {ticket.get('issue', 'N/A')}

**Created:** {created_date}
**Last Updated:** {updated_date}

**Replies:** {len(ticket.get('replies', []))} comment(s)
**Attachments:** {len(ticket.get('attachments', []))} file(s)"""

            if len(response) > 4000:
                response = response[:3950] + "...\n\n(message truncated)"

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in ticket_status_command: {e}", exc_info=True)
            await update.message.reply_text("❌ Error retrieving ticket details.")

    @staticmethod
    async def ticket_replies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show ticket replies via /ticket_replies command"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "💬 View Ticket Updates\n\n"
                    "Usage: `/ticket_replies {ticket_id}`\n"
                    "Example: `/ticket_replies TKT-20260410225504`",
                    parse_mode="Markdown"
                )
                return

            ticket_id = context.args[0].upper()

            # Validate ticket ID format
            if not ticket_id.startswith("TKT-"):
                await update.message.reply_text(
                    f"❌ Invalid ticket ID format. Expected format: TKT-YYYYMMDDHHMMSS\n"
                    f"You provided: {ticket_id}"
                )
                return

            ticket = TicketService.get_ticket(ticket_id)

            if not ticket:
                await update.message.reply_text(f"❌ Ticket {ticket_id} not found.")
                return

            replies = ticket.get('replies', [])

            if not replies:
                await update.message.reply_text(
                    f"💬 Ticket {ticket_id}: No replies yet."
                )
                return

            response = f"💬 **Ticket {ticket_id} - Updates ({len(replies)} total):**\n\n"
            for idx, reply in enumerate(replies, 1):
                timestamp = reply.get('timestamp', 'N/A')[:16]
                user = reply.get('user', 'Unknown')
                text = reply.get('text', 'N/A')[:200]

                response += f"{idx}. **{user}** _{timestamp}_\n```\n{text}\n```\n\n"

                if len(response) > 3500:
                    response = response[:3450] + "\n\n...(truncated)"
                    break

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in ticket_replies_command: {e}", exc_info=True)
            await update.message.reply_text("❌ Error retrieving ticket replies.")

    @staticmethod
    async def group_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show group-specific help when /help is used in a group"""
        try:
            chat = update.effective_chat

            # Check if in group
            if chat.type in ["group", "supergroup"]:
                bot_info = await context.bot.get_me()
                bot_mention = f"@{bot_info.username}" if bot_info.username else "@bot"

                msg = f"""👋 **Help Desk Bot - Group Commands**

**📢 Create Ticket:**
Mention me in any message:
```
{bot_mention} my issue here
```
Attachments supported (photos, documents)

**📋 View Your Tickets:**
`/my_tickets` - See all your open tickets

**🔍 Check Ticket Status:**
`/ticket_status {{ticket_id}}`
Example: `/ticket_status TKT-20260410225504`

**💬 View Ticket Updates:**
`/ticket_replies {{ticket_id}}` - See all comments and updates

**Quick Tips:**
✓ Reply to my ticket message to add updates
✓ Include attachments when mentioning me
✓ Check similar issues before creating new tickets
✓ Use /register_email to link your company email

Need help? Use `/help` for full command list."""

                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                # In DM, show standard help
                bot_info = await context.bot.get_me()
                bot_mention = f"@{bot_info.username}" if bot_info.username else "@bot_name"

                msg = f"""📋 **Help Desk Bot Commands**

**📧 Email Registration:**
`/register_email` - Register your company email
`/my_email` - Check your registered email

**🎫 Create Ticket:**
`/start` - Create a new support ticket (DM only)
`/cancel` - Cancel current ticket

**📢 Group Mentions:**
Mention the bot in a group:
```
{bot_mention} your issue here
```
Example: `{bot_mention} office internet down`
Tickets created instantly!

**📋 Check Tickets:**
`/my_tickets` - View your tickets
`/ticket_status {{id}}` - Get ticket details
`/ticket_replies {{id}}` - View ticket updates

**🔐 Admin Commands:**
`/admin` - Login to admin panel
`/list` - View all tickets
`/view {{ticket_id}}` - View ticket details
`/delete {{ticket_id}}` - Delete ticket
`/reply {{ticket_id}} {{message}}` - Add reply to ticket
`/replies {{ticket_id}}` - View ticket replies

**Features:**
✓ Email registration for employees
✓ Automatic confirmation emails
✓ File uploads (JPG, PNG, PDF, DOCX)
✓ Auto-priority routing
✓ Instant ticket creation
✓ Group collaboration with replies

Company: {settings.company.NAME}
Support: {settings.email.SPICEWORKS_EMAIL}"""

                await update.message.reply_text(msg, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in group_help_command: {e}", exc_info=True)
            await update.message.reply_text("❌ Error retrieving help information.")

    @staticmethod
    async def handle_ticket_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle replies to bot's ticket messages in groups"""
        try:
            message = update.message
            chat = update.effective_chat

            # Only process in groups
            if chat.type not in ["group", "supergroup"]:
                return

            # Check if this is a reply to another message
            if not message.reply_to_message:
                return

            # Check if message has text
            if not message.text:
                return

            # Get the message being replied to
            replied_to = message.reply_to_message

            # Check if it's a bot message (by checking if it contains ticket ID)
            if not replied_to.text or "Ticket ID" not in replied_to.text:
                return

            logger.info(f"Detected reply to ticket message: {replied_to.text[:50]}")

            # Extract ticket ID from the replied message
            ticket_id = None
            if "TKT-" in replied_to.text:
                # Find the ticket ID
                parts = replied_to.text.split("TKT-")
                if len(parts) > 1:
                    # Extract the ticket ID (format: TKT-YYYYMMDDHHmmss)
                    ticket_part = parts[1].split()[0]
                    ticket_id = f"TKT-{ticket_part}"

            if not ticket_id or not ticket_id.startswith("TKT-"):
                logger.warning("Could not extract ticket ID from message")
                return

            logger.info(f"Found ticket ID: {ticket_id}")

            # Verify ticket exists
            ticket = TicketService.get_ticket(ticket_id)
            if not ticket:
                await message.reply_text(
                    f"❌ Ticket {ticket_id} not found.",
                    reply_to_message_id=message.message_id
                )
                return

            # Add reply to ticket
            user_name = message.from_user.full_name or message.from_user.username or "Anonymous"
            success = TicketService.add_reply(
                ticket_id,
                message.text,
                user_name=f"{user_name} (Group)"
            )

            if success:
                await message.reply_text(
                    f"✅ Reply added to {ticket_id}",
                    reply_to_message_id=message.message_id
                )
                logger.info(f"Reply added to ticket {ticket_id}")
            else:
                await message.reply_text(
                    f"❌ Error adding reply to {ticket_id}",
                    reply_to_message_id=message.message_id
                )

        except Exception as e:
            logger.error(f"Error in handle_ticket_reply: {e}", exc_info=True)


def get_group_command_handlers():
    """Get all group command handlers"""
    return [
        CommandHandler("my_tickets", GroupCommandHandlers.my_tickets_command),
        CommandHandler("ticket_status", GroupCommandHandlers.ticket_status_command),
        CommandHandler("ticket_replies", GroupCommandHandlers.ticket_replies_command),
    ]


def get_group_reply_handler():
    """Get handler for replies to ticket messages"""
    return MessageHandler(
        filters.REPLY & filters.TEXT & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
        GroupCommandHandlers.handle_ticket_reply
    )


def get_group_help_handler():
    """Get group help handler (overrides the default /help in main.py in group context)"""
    # This should be registered in main.py for both group and private chats
    # It will intelligently detect the chat type and respond appropriately
    return CommandHandler(
        "help",
        GroupCommandHandlers.group_help_command,
        filters.ChatType.GROUPS | filters.ChatType.PRIVATE
    )
