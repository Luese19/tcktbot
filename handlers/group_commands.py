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

            # Status emoji mapping
            status_emoji = {
                "open": "🔴",
                "in_progress": "🟡",
                "waiting": "⏳",
                "completed": "🟢",
                "closed": "🟢"
            }

            # Check if in group and update any closed/waiting tickets in group messages
            chat = update.effective_chat
            if chat.type in ["group", "supergroup"]:
                for ticket in user_tickets:
                    ticket_status = ticket.get('status', 'open')

                    # Check if ticket is closed or waiting and has group tracking info
                    if ticket_status in ['closed', 'waiting']:
                        source_info = TicketService.get_ticket_source_info(ticket.get('ticket_id'))

                        if source_info and source_info.get('group_id') and source_info.get('bot_message_id'):
                            try:
                                # Build updated message with new status
                                ticket_id = ticket.get('ticket_id')
                                created_date = ticket.get('created_at', 'N/A')[:10]

                                updated_msg = f"""✅ **Ticket Created!**

**Ticket ID:** `{ticket_id}`
**Created:** {created_date}
**Status:** {ticket_status.upper()}
**Issue:** {ticket.get('issue', 'N/A')[:100]}

Your team will handle this shortly."""

                                # Update the original message in the group
                                await context.bot.edit_message_text(
                                    chat_id=source_info['group_id'],
                                    message_id=source_info['bot_message_id'],
                                    text=updated_msg,
                                    parse_mode="Markdown"
                                )
                                logger.info(f"Updated ticket {ticket_id} status in group {source_info['group_id']}")

                            except Exception as e:
                                logger.warning(f"Could not update ticket message in group: {e}")
                                # Continue processing other tickets even if one update fails

            # Show last 5 tickets
            response = f"🎫 Your Tickets ({len(user_tickets)} total, showing last 5):\n\n"
            for ticket in user_tickets[:5]:
                ticket_status = ticket.get('status', 'open')
                emoji = status_emoji.get(ticket_status, "⚪")

                created_date = ticket.get('created_at', 'N/A')[:10]

                response += (
                    f"{emoji} **{ticket.get('ticket_id')}**\n"
                    f"   Issue: {ticket.get('issue', 'N/A')[:40]}\n"
                    f"   Status: {ticket_status.capitalize()} | "
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

                msg = f"""👋 <b>Help Desk Bot - Group Commands</b>

<b>📢 Create Ticket:</b>
Mention me in any message:
<code>{bot_mention} my issue here</code>

Attachments supported (photos, documents)

<b>📋 View Your Tickets:</b>
<code>/my_tickets</code> - See all your open tickets

<b>🔍 Check Ticket Status:</b>
<code>/ticket_status TICKET_ID</code>
Example: <code>/ticket_status TKT-20260410225504</code>

<b>💬 View Ticket Updates:</b>
<code>/ticket_replies TICKET_ID</code> - See all comments and updates

<b>Quick Tips:</b>
• Reply to my ticket message to add updates
• Include attachments when mentioning me
• Check similar issues before creating new tickets
• Use /register_email to link your company email

Need help? Use <code>/help</code> for full command list."""

                await update.message.reply_text(msg, parse_mode="HTML")
            else:
                # In DM, show standard help
                bot_info = await context.bot.get_me()
                bot_mention = f"@{bot_info.username}" if bot_info.username else "@bot_name"

                msg = f"""📋 <b>Help Desk Bot Commands</b>

<b>📧 User Commands:</b>
<code>/start</code> - Create a new support ticket (DM only)
<code>/register_email</code> - Register your company email
<code>/my_email</code> - Check your registered email
<code>/lookup</code> - Find your tickets by email
<code>/cancel</code> - Cancel current ticket

<b>📢 Group Mentions:</b>
Mention the bot in a group:
<code>{bot_mention} your issue here</code>
Example: <code>{bot_mention} office internet down</code>
Tickets created instantly!

<b>📋 Ticket Management:</b>
<code>/my_tickets</code> - View your open tickets
<code>/ticket_status TICKET_ID</code> - Get ticket details
<code>/ticket_replies TICKET_ID</code> - View ticket updates

<b>📊 Queue Commands (if enabled):</b>
<code>/my_position</code> - Check your position in queue
<code>/queue_status</code> - View queue statistics (admin)

<b>🔐 Admin Panel Commands:</b>
<code>/admin</code> - Login to admin panel
<code>/list</code> - View all tickets
<code>/view TICKET_ID</code> - View ticket details
<code>/delete TICKET_ID</code> - Delete a ticket
<code>/reply TICKET_ID MESSAGE</code> - Add reply to ticket
<code>/replies TICKET_ID</code> - View ticket replies
<code>/group_tickets</code> - Show tickets from current group
<code>/status</code> - Check bot status

<b>⏰ Task Scheduling (admin only):</b>
<code>/schedule</code> - Create scheduled tasks
<code>/tasks</code> - List all scheduled tasks

<b>👥 User Management (super admin only):</b>
<code>/add_admin USER_ID</code> - Add admin user
<code>/remove_admin USER_ID</code> - Remove admin user
<code>/list_admins</code> - View all admins
<code>/add_it_member USER_ID</code> - Add IT team member
<code>/remove_it_member USER_ID</code> - Remove IT team member
<code>/list_it_members</code> - View all IT members

<b>✨ Features:</b>
• Email registration for employees
• Automatic confirmation emails
• File uploads (JPG, PNG, PDF, DOCX)
• Auto-priority routing
• Instant ticket creation
• Message reaction tickets (IT team)
• Task scheduling & automation
• Dynamic user management

Company: {settings.company.NAME}
Support: {settings.email.SPICEWORKS_EMAIL}"""

                await update.message.reply_text(msg, parse_mode="HTML")

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
