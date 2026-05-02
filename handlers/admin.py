"""Admin and ticket lookup handlers"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters
from utils.logger import get_logger
from services.ticket_service import TicketService
from config.settings import settings

logger = get_logger(__name__)


class AdminState:
    """Admin command states"""
    NONE, AUTH, LOOKUP_EMAIL = range(3)


class AdminHandlers:
    """Handlers for admin and ticket lookup commands"""
    admin_sessions = {}

    # ==================== LOOKUP COMMANDS ====================
    @staticmethod
    async def lookup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User lookup their tickets by email"""
        try:
            user_id = update.effective_user.id
            user_name = update.effective_user.first_name

            await update.message.reply_text(
                f"Hello {user_name}! 👋\n\n"
                f"Enter your company email to lookup your tickets:"
            )
            AdminHandlers.admin_sessions[user_id] = {'type': 'lookup'}
            return AdminState.LOOKUP_EMAIL

        except Exception as e:
            logger.error(f"Error in lookup command: {e}")
            await update.message.reply_text("Error processing request.")
            return ConversationHandler.END

    @staticmethod
    async def lookup_email_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user email lookup"""
        try:
            user_id = update.effective_user.id
            email = update.message.text.strip()

            # Validate email format
            if not settings.is_company_email(email):
                await update.message.reply_text(
                    f"❌ Invalid email. Please use company email (@{settings.company.EMAIL_DOMAIN})"
                )
                return AdminState.LOOKUP_EMAIL

            # Find tickets for this email
            all_tickets = TicketService.list_tickets()
            user_tickets = [t for t in all_tickets if t.get('email', '').lower() == email.lower()]

            if not user_tickets:
                await update.message.reply_text(f"No tickets found for {email}")
                AdminHandlers.admin_sessions.pop(user_id, None)
                return ConversationHandler.END

            # Show tickets
            response = f"📋 Found {len(user_tickets)} ticket(s) for {email}:\n\n"
            for ticket in user_tickets[:10]:
                response += (
                    f"🎫 {ticket.get('ticket_id', 'N/A')}\n"
                    f"   Issue: {ticket.get('issue', 'N/A')[:50]}\n"
                    f"   Priority: {ticket.get('priority', 'N/A')} | Status: {ticket.get('status', 'N/A')}\n"
                    f"   Created: {ticket.get('created_at', 'N/A')[:10]}\n\n"
                )

            await update.message.reply_text(response)
            AdminHandlers.admin_sessions.pop(user_id, None)
            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error in lookup email input: {e}")
            await update.message.reply_text("Error retrieving tickets.")
            AdminHandlers.admin_sessions.pop(user_id, None)
            return ConversationHandler.END

    # ==================== ADMIN LOGIN ====================
    @staticmethod
    async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin login"""
        try:
            user_id = update.effective_user.id

            # Check if already authenticated
            if AdminHandlers._is_authenticated(user_id):
                await AdminHandlers.show_admin_menu(update)
                return ConversationHandler.END

            await update.message.reply_text(
                "🔐 Admin Access\n\n"
                "Enter admin password:"
            )
            AdminHandlers.admin_sessions[user_id] = {'type': 'admin'}
            return AdminState.AUTH

        except Exception as e:
            logger.error(f"Error in admin command: {e}")
            await update.message.reply_text("Error accessing admin panel.")
            return ConversationHandler.END

    @staticmethod
    async def admin_auth_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin password"""
        try:
            user_id = update.effective_user.id
            password = update.message.text.strip()

            if password != settings.app.ADMIN_PASSWORD:
                await update.message.reply_text("❌ Invalid password.")
                AdminHandlers.admin_sessions.pop(user_id, None)
                return ConversationHandler.END

            AdminHandlers.admin_sessions[user_id] = {
                'authenticated': True,
                'type': 'admin'
            }

            await AdminHandlers.show_admin_menu(update)
            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error in admin auth: {e}")
            await update.message.reply_text("Error processing password.")
            AdminHandlers.admin_sessions.pop(user_id, None)
            return ConversationHandler.END

    # ==================== ADMIN COMMANDS ====================
    @staticmethod
    async def show_admin_menu(update: Update):
        """Show admin menu"""
        message = (
            "✅ Authenticated!\n\n"
            "📊 Admin Commands:\n"
            "/list - View all tickets\n"
            "/view {ticket_id} - View ticket details\n"
            "/delete {ticket_id} - Delete ticket\n"
            "/reply {ticket_id} {message} - Add reply\n"
            "/replies {ticket_id} - View replies\n\n"
            "🗓️ Schedule Commands:\n"
            "/schedule - Create a scheduled task\n"
            "/tasks - List scheduled tasks\n"
            "/delete_schedule {task_id} - Delete scheduled task\n"
        )
        await update.message.reply_text(message)

    @staticmethod
    async def delete_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wrapper for ScheduleHandler.delete_task_command with admin check"""
        try:
            user_id = update.effective_user.id
            if not AdminHandlers._is_authenticated(user_id):
                await update.message.reply_text("❌ Access denied. Use /admin to login.")
                return

            from handlers.schedule_handler import ScheduleHandler
            await ScheduleHandler.delete_task_command(update, context)
        except Exception as e:
            logger.error(f"Error in delete_schedule_command: {e}")
            await update.message.reply_text("Error processing delete schedule command.")

    @staticmethod
    async def list_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wrapper for ScheduleHandler.list_tasks_command with admin check"""
        try:
            user_id = update.effective_user.id
            if not AdminHandlers._is_authenticated(user_id):
                await update.message.reply_text("❌ Access denied. Use /admin to login.")
                return

            from handlers.schedule_handler import ScheduleHandler
            await ScheduleHandler.list_tasks_command(update, context)
        except Exception as e:
            logger.error(f"Error in list_tasks_command: {e}")
            await update.message.reply_text("Error processing list tasks command.")

    @staticmethod
    async def list_tickets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all tickets (admin only)"""
        try:
            user_id = update.effective_user.id

            if not AdminHandlers._is_authenticated(user_id):
                await update.message.reply_text("❌ Access denied. Use /admin to login.")
                return

            tickets = TicketService.list_tickets()

            if not tickets:
                await update.message.reply_text("No tickets found.")
                return

            response = f"📋 All Tickets ({len(tickets)} total):\n\n"
            for ticket in tickets[:20]:
                response += (
                    f"🎫 {ticket.get('ticket_id', 'N/A')}\n"
                    f"   {ticket.get('issue', 'N/A')[:30]}\n"
                    f"   {ticket.get('email', 'N/A')} | {ticket.get('priority', 'N/A')}\n\n"
                )

            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error listing tickets: {e}")
            await update.message.reply_text("Error retrieving tickets.")

    @staticmethod
    async def view_ticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View ticket details (admin only)"""
        try:
            user_id = update.effective_user.id

            if not AdminHandlers._is_authenticated(user_id):
                await update.message.reply_text("❌ Access denied. Use /admin to login.")
                return

            if not context.args:
                await update.message.reply_text("Usage: /view {ticket_id}")
                return

            ticket_id = context.args[0]
            ticket = TicketService.get_ticket(ticket_id)

            if not ticket:
                await update.message.reply_text(f"❌ Ticket {ticket_id} not found.")
                return

            response = f"""📋 Ticket Details:

ID: {ticket.get('ticket_id')}
Name: {ticket.get('name')}
Email: {ticket.get('email')}
Department: {ticket.get('department')}
Priority: {ticket.get('priority')}
Status: {ticket.get('status')}
Created: {ticket.get('created_at')}

Issue: {ticket.get('issue')}

Description:
{ticket.get('description', 'N/A')}

Attachments: {len(ticket.get('attachments', []))}
"""
            if ticket.get('attachments'):
                response += "Files:\n"
                for att in ticket['attachments']:
                    response += f"- {att.get('filename')} ({att.get('type')})\n"

            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error viewing ticket: {e}")
            await update.message.reply_text("Error retrieving ticket.")

    @staticmethod
    async def delete_ticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete ticket (admin only)"""
        try:
            user_id = update.effective_user.id

            if not AdminHandlers._is_authenticated(user_id):
                await update.message.reply_text("❌ Access denied. Use /admin to login.")
                return

            if not context.args:
                await update.message.reply_text("Usage: /delete {ticket_id}")
                return

            ticket_id = context.args[0]

            if not TicketService.get_ticket(ticket_id):
                await update.message.reply_text(f"❌ Ticket {ticket_id} not found.")
                return

            TicketService.delete_ticket(ticket_id)
            logger.info(f"Ticket {ticket_id} deleted by admin {user_id}")
            await update.message.reply_text(f"✓ Ticket {ticket_id} deleted.")

        except Exception as e:
            logger.error(f"Error deleting ticket: {e}")
            await update.message.reply_text("Error deleting ticket.")

    @staticmethod
    async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a reply/note to a ticket (admin only)"""
        try:
            user_id = update.effective_user.id

            if not AdminHandlers._is_authenticated(user_id):
                await update.message.reply_text("❌ Access denied. Use /admin to login.")
                return

            if not context.args or len(context.args) < 2:
                await update.message.reply_text("Usage: /reply {ticket_id} {reply_text}")
                return

            ticket_id = context.args[0]
            reply_text = " ".join(context.args[1:])

            if not TicketService.get_ticket(ticket_id):
                await update.message.reply_text(f"❌ Ticket {ticket_id} not found.")
                return

            if TicketService.add_reply(ticket_id, reply_text):
                logger.info(f"Reply added to ticket {ticket_id} by admin {user_id}")
                await update.message.reply_text(f"✓ Reply added to ticket {ticket_id}")
            else:
                await update.message.reply_text("Error adding reply.")

        except Exception as e:
            logger.error(f"Error in reply command: {e}")
            await update.message.reply_text("Error processing reply.")

    @staticmethod
    async def view_replies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View all replies for a ticket"""
        try:
            user_id = update.effective_user.id

            if not AdminHandlers._is_authenticated(user_id):
                await update.message.reply_text("❌ Access denied. Use /admin to login.")
                return

            if not context.args:
                await update.message.reply_text("Usage: /replies {ticket_id}")
                return

            ticket_id = context.args[0]
            ticket = TicketService.get_ticket(ticket_id)

            if not ticket:
                await update.message.reply_text(f"❌ Ticket {ticket_id} not found.")
                return

            replies = ticket.get('replies', [])

            if not replies:
                await update.message.reply_text(f"📋 Ticket {ticket_id}: No replies yet.")
                return

            response = f"📋 Ticket {ticket_id} - Replies:\n\n"
            for idx, reply in enumerate(replies, 1):
                response += (
                    f"{idx}. {reply.get('user', 'Unknown')}\n"
                    f"   Time: {reply.get('timestamp', 'N/A')[:16]}\n"
                    f"   {reply.get('text', 'N/A')}\n\n"
                )

            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error viewing replies: {e}")
            await update.message.reply_text("Error retrieving replies.")

    @staticmethod
    async def group_tickets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show tickets from a specific group (admin only)"""
        try:
            user_id = update.effective_user.id

            if not AdminHandlers._is_authenticated(user_id):
                await update.message.reply_text("❌ Access denied. Use /admin to login.")
                return

            # Get group ID from args or use current chat
            chat = update.effective_chat
            group_id = None

            if context.args:
                try:
                    group_id = int(context.args[0])
                except ValueError:
                    await update.message.reply_text(
                        "Usage: `/group_tickets` (for current group) or `/group_tickets {chat_id}`",
                        parse_mode="Markdown"
                    )
                    return
            else:
                # Use current chat if in a group
                if chat.type in ["group", "supergroup"]:
                    group_id = chat.id
                else:
                    await update.message.reply_text(
                        "Usage: `/group_tickets {chat_id}`\n\n"
                        "Run this command in a group, or provide a group chat ID.",
                        parse_mode="Markdown"
                    )
                    return

            # Get all tickets
            all_tickets = TicketService.list_tickets()

            # Filter tickets from this group
            group_tickets = [
                t for t in all_tickets
                if t.get('group_id') == group_id
            ]

            if not group_tickets:
                await update.message.reply_text(
                    f"📊 No tickets found for group ID {group_id}"
                )
                return

            # Calculate statistics
            status_counts = {
                'open': 0,
                'in_progress': 0,
                'completed': 0
            }

            for ticket in group_tickets:
                status = ticket.get('status', 'open')
                if status in status_counts:
                    status_counts[status] += 1

            # Get group name if available
            group_name = group_tickets[0].get('group_name', f"Group {group_id}")

            # Build response
            response = f"""📊 **Tickets from "{group_name}"**

**Chat ID:** `{group_id}`

**Statistics:**
🔴 Open: {status_counts['open']}
🟡 In Progress: {status_counts['in_progress']}
🟢 Completed: {status_counts['completed']}
📊 Total: {len(group_tickets)}

**Recent Tickets (last 5):**
"""

            for idx, ticket in enumerate(group_tickets[:5], 1):
                status_emoji = {
                    "open": "🔴",
                    "in_progress": "🟡",
                    "completed": "🟢"
                }.get(ticket.get('status', 'open'), "⚪")

                response += (
                    f"\n{idx}. {status_emoji} **{ticket.get('ticket_id')}**\n"
                    f"   Issue: {ticket.get('issue', 'N/A')[:40]}\n"
                    f"   User: {ticket.get('name', 'N/A')} | Priority: {ticket.get('priority', 'N/A')}\n"
                )

            if len(group_tickets) > 5:
                response += f"\n... and {len(group_tickets) - 5} more tickets"

            response += f"\n\nUse `/view {{ticket_id}}` to view details"

            if len(response) > 4000:
                # Truncate if too long
                response = response[:3950] + "...\n\n(message truncated)"

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in group_tickets_command: {e}")
            await update.message.reply_text("Error retrieving group tickets.")

    # ==================== HELPERS ====================
    @staticmethod
    def _is_authenticated(user_id: int) -> bool:
        """Check if user is authenticated as admin"""
        return (
            user_id in AdminHandlers.admin_sessions and
            AdminHandlers.admin_sessions[user_id].get('authenticated') == True
        )

    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel admin operations"""
        user_id = update.effective_user.id
        AdminHandlers.admin_sessions.pop(user_id, None)
        await update.message.reply_text("Cancelled.")
        return ConversationHandler.END


def get_lookup_handler():
    """Create lookup conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("lookup", AdminHandlers.lookup_command)],
        states={
            AdminState.LOOKUP_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, AdminHandlers.lookup_email_input)]
        },
        fallbacks=[CommandHandler("cancel", AdminHandlers.cancel)]
    )


def get_admin_handler():
    """Create admin conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("admin", AdminHandlers.admin_command)],
        states={
            AdminState.AUTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, AdminHandlers.admin_auth_input)]
        },
        fallbacks=[CommandHandler("cancel", AdminHandlers.cancel)]
    )


def get_admin_command_handlers():
    """Create admin command handlers"""
    from handlers.user_manager_handler import get_user_manager_command_handlers
    
    return [
        CommandHandler("list", AdminHandlers.list_tickets_command),
        CommandHandler("view", AdminHandlers.view_ticket_command),
        CommandHandler("delete", AdminHandlers.delete_ticket_command),
        CommandHandler("reply", AdminHandlers.reply_command),
        CommandHandler("replies", AdminHandlers.view_replies_command),
        CommandHandler("tasks", AdminHandlers.list_tasks_command),
        CommandHandler("delete_schedule", AdminHandlers.delete_schedule_command),
        CommandHandler("group_tickets", AdminHandlers.group_tickets_command),
    ] + get_user_manager_command_handlers()
