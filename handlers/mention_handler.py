"""Simplified, robust group mention handler - DIRECT ticket creation with media & similar issues support"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReactionType
from telegram.ext import ContextTypes, MessageHandler, filters, CallbackQueryHandler
from typing import Optional, List, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

from utils.logger import get_logger
from config.settings import settings
from services.username_service import UsernameService

logger = get_logger(__name__)

# Thread pool for blocking operations
_thread_pool = ThreadPoolExecutor(max_workers=2)

# Store pending confirmations for similar issues flow
_pending_confirmations = {}


class GroupMentionHandler:
    """Handle bot mentions in groups to create tickets directly"""

    @staticmethod
    def _verify_button_permission(user_id: int, callback_key: str) -> tuple:
        """
        Verify user has permission to click confirmation button.

        Args:
            user_id: The user clicking the button
            callback_key: The key for the pending confirmation

        Returns:
            (is_authorized: bool, error_message: str)
        """
        if callback_key not in _pending_confirmations:
            return False, "❌ This button has expired. Please try again."

        ctx = _pending_confirmations[callback_key]
        if ctx.get('user_id') != user_id:
            logger.warning(
                f"SECURITY: Unauthorized button click - "
                f"User {user_id} attempted to act on confirmation for user {ctx.get('user_id')} "
                f"in chat {ctx.get('chat_id')}"
            )
            return False, "❌ This button was created for someone else. You can start your own ticket with /start or mention me again."

        return True, ""

    @staticmethod
    async def handle_member_status_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle when bot is added to a group"""
        try:
            if not update.my_chat_member:
                return

            chat = update.effective_chat
            my_chat_member = update.my_chat_member

            # Check if bot was added to group
            if my_chat_member.new_chat_member.status == "member":
                if chat.type in ["group", "supergroup"]:
                    # Get bot username safely
                    bot_info = await context.bot.get_me()
                    bot_username = bot_info.username or "bot"

                    welcome_msg = f"""👋 Welcome! I'm the IT Help Desk Bot, proudly created by the IT Department to assist you. My main goal is to help you submit support tickets quickly and efficiently, ensuring your issues are addressed as soon as possible.

For direct support, you can also reach our team at help@marquismaintenance.on.spiceworks.com. Thank you for contacting the IT Help Desk!"""

                    await context.bot.send_message(
                        chat_id=chat.id,
                        text=welcome_msg,
                        parse_mode="HTML"
                    )
                    logger.info(f"Welcome message sent to group {chat.id}")
        except Exception as e:
            logger.error(f"Error in handle_member_status_update: {e}", exc_info=True)

    @staticmethod
    async def handle_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle bot mentions in groups - creates ticket directly
        Supports text, photos, documents, and similar issue detection
        """
        try:
            logger.info("=" * 60)
            logger.info("MENTION HANDLER TRIGGERED")
            logger.info("=" * 60)

            if not update or not update.message:
                logger.warning("No message in update")
                return

            message = update.message
            chat = update.effective_chat

            logger.info(f"Message from chat: {chat.type} (ID: {chat.id})")
            logger.info(f"Message text: {message.text[:100] if message.text else 'EMPTY'}")
            logger.info(f"Has photo: {bool(message.photo)}, Has document: {bool(message.document)}")

            # Only process in groups
            if chat.type not in ["group", "supergroup"]:
                logger.info(f"Ignoring - not a group (type: {chat.type})")
                return

            # Get bot username
            bot_info = await context.bot.get_me()
            bot_username = bot_info.username
            logger.info(f"Bot username: @{bot_username}")

            # Check for mention
            mention_pattern = f"@{bot_username}"
            text = message.text or ""
            logger.info(f"Looking for mention pattern: {mention_pattern}")

            if mention_pattern not in text:
                logger.info(f"No {mention_pattern} found in message")
                return

            logger.info(f"DETECTED BOT MENTION! Processing...")

            # Get user info immediately
            user_id = message.from_user.id
            user_name = message.from_user.full_name or "User"
            logger.info(f"User: {user_name} (ID: {user_id})")

            # Check for multiple user mentions (bulk mention support)
            other_mentions = GroupMentionHandler._extract_mentioned_users(text, bot_username)

            # Extract issue text (removing all mentions)
            all_mentions = other_mentions + [bot_username]
            issue_text = GroupMentionHandler._extract_issue_text_from_bulk_mention(text, all_mentions)

            if not issue_text or not issue_text.strip():
                logger.warning("Issue text is empty after removing mention")
                await message.reply_text(
                    f"Please mention an issue:\n\n@{bot_username} your issue here",
                    reply_to_message_id=message.message_id
                )
                return

            # Handle bulk mentions (multiple users)
            if other_mentions:
                logger.info(f"Detected bulk mention with {len(other_mentions)} additional users: {other_mentions}")
                await GroupMentionHandler._handle_bulk_mention(
                    update, context, message, chat, bot_username, issue_text,
                    user_id, user_name, other_mentions
                )
                return

            logger.info(f"Issue extracted: {issue_text[:50]}")

            # Send "processing" message
            proc_msg = await message.reply_text(
                "⏳ Checking for similar issues...",
                reply_to_message_id=message.message_id
            )
            logger.info(f"Processing message sent: {proc_msg.message_id}")

            # Check for similar issues
            from services.ticket_service import TicketService
            similar_tickets = TicketService.find_similar_tickets(issue_text, max_results=3)

            if similar_tickets:
                logger.info(f"Found {len(similar_tickets)} similar tickets")
                await GroupMentionHandler._show_similar_tickets_confirmation(
                    update, context, proc_msg, issue_text, user_id, user_name,
                    chat.id, chat.title, chat.type, message
                )
                return

            # No similar issues, proceed with ticket creation
            logger.info("No similar tickets found, proceeding with creation...")

            # Download attachments if present
            attachments_list = await GroupMentionHandler._download_attachments(
                message, update.effective_user.id
            )

            # Create ticket in thread pool
            logger.info("Starting ticket creation in thread pool...")
            ticket_id = await asyncio.get_event_loop().run_in_executor(
                _thread_pool,
                lambda: GroupMentionHandler._create_ticket_sync(
                    user_id, user_name, issue_text, chat.id, chat.title, chat.type,
                    message.message_id, attachments_list
                )
            )

            logger.info(f"Ticket creation returned: {ticket_id}")

            if ticket_id:
                logger.info(f"SUCCESS! Ticket: {ticket_id}")

                # Get current date and time for display
                from datetime import datetime
                created_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")

                # Update with success message
                success_msg = f"""✅ **Ticket Created!**

**Ticket ID:** `{ticket_id}`
**Created:** {created_date}\n
**Issue:** {issue_text}

Your Tech Support team will handle this shortly."""

                await proc_msg.edit_text(
                    success_msg,
                    parse_mode="Markdown"
                )

                # Store bot message ID for thread replies
                TicketService.save_ticket_source_info(
                    ticket_id, chat.id, chat.title, chat.type,
                    proc_msg.message_id, message.message_id
                )

                # Add emoji reactions for quick feedback (non-blocking)
                try:
                    await GroupMentionHandler._set_message_reactions(
                        context, chat.id, proc_msg.message_id
                    )
                except Exception as e:
                    logger.warning(f"Error setting reactions: {e}")

                logger.info("Success message sent with reactions")
            else:
                logger.error("Ticket creation returned None")
                await proc_msg.edit_text(
                    "❌ Error creating ticket. Please try again or contact support."
                )

        except Exception as e:
            logger.error(f"EXCEPTION in handle_mention: {e}", exc_info=True)
            try:
                await update.message.reply_text(
                    "❌ An error occurred. Please try again.",
                    reply_to_message_id=update.message.message_id
                )
            except:
                logger.error("Could not send error message")

    @staticmethod
    async def _show_similar_tickets_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                                  proc_msg, issue_text: str, user_id: int,
                                                  user_name: str, chat_id: int, chat_name: str,
                                                  chat_type: str, original_message):
        """Show similar tickets and ask user for confirmation"""
        try:
            from services.ticket_service import TicketService
            similar_tickets = TicketService.find_similar_tickets(issue_text, max_results=3)

            if not similar_tickets:
                return

            # Format similar tickets
            similar_text = "Found similar open tickets:\n\n"
            for ticket in similar_tickets[:3]:
                similar_text += (
                    f"🎫 {ticket.get('ticket_id')}: {ticket.get('issue', 'N/A')[:50]}\n"
                    f"   Priority: {ticket.get('priority')} | dept: {ticket.get('department')}\n\n"
                )

            similar_text += "Would you still like to create a new ticket?"

            # Create inline keyboard with buttons
            keyboard = [
                [
                    InlineKeyboardButton("✅ Create anyway", callback_data=f"create_ticket_{user_id}_{chat_id}"),
                    InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_ticket_{user_id}_{chat_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await proc_msg.edit_text(similar_text, reply_markup=reply_markup)

            # Store the confirmation context for the callback
            callback_key = f"{user_id}_{chat_id}"
            _pending_confirmations[callback_key] = {
                "issue_text": issue_text,
                "user_id": user_id,
                "user_name": user_name,
                "chat_id": chat_id,
                "chat_name": chat_name,
                "chat_type": chat_type,
                "message_id": original_message.message_id,
                "message": original_message,
                "proc_msg": proc_msg
            }

            logger.info(f"Stored confirmation context for {callback_key}")

        except Exception as e:
            logger.error(f"Error showing similar tickets confirmation: {e}", exc_info=True)

    @staticmethod
    async def handle_confirmation_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button press for similar tickets confirmation"""
        try:
            query = update.callback_query
            clicker_user_id = query.from_user.id
            data = query.data
            logger.info(f"Button pressed by user {clicker_user_id}: {data}")

            # Parse the button action
            if data.startswith("create_ticket_"):
                # Extract user_id and chat_id from callback data
                parts = data.split("_")
                if len(parts) >= 4:
                    user_id = int(parts[2])
                    chat_id = int(parts[3])
                    callback_key = f"{user_id}_{chat_id}"

                    # Permission verification
                    is_authorized, error_msg = GroupMentionHandler._verify_button_permission(
                        clicker_user_id, callback_key
                    )
                    if not is_authorized:
                        await query.answer(error_msg, show_alert=True)
                        return

                    await query.answer()

                    if callback_key in _pending_confirmations:
                        ctx = _pending_confirmations[callback_key]

                        # Download attachments if present
                        attachments_list = await GroupMentionHandler._download_attachments(
                            ctx["message"], user_id
                        )

                        # Create ticket
                        from services.ticket_service import TicketService
                        ticket_id = await asyncio.get_event_loop().run_in_executor(
                            _thread_pool,
                            lambda: GroupMentionHandler._create_ticket_sync(
                                ctx["user_id"], ctx["user_name"], ctx["issue_text"],
                                ctx["chat_id"], ctx["chat_name"], ctx["chat_type"],
                                ctx["message_id"], attachments_list
                            )
                        )

                        if ticket_id:
                            from datetime import datetime
                            created_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")

                            await query.edit_message_text(
                                f"✅ **Ticket Created!**\n\n"
                                f"**Ticket ID:** `{ticket_id}`\n"
                                f"**Created:** {created_date}\n\n"
                                f"**Issue:** {ctx['issue_text']}\n\n"
                                f"Your Tech Support team will handle this shortly.",
                                parse_mode="Markdown"
                            )

                            # Store source info
                            TicketService.save_ticket_source_info(
                                ticket_id, ctx["chat_id"], ctx["chat_name"], ctx["chat_type"],
                                ctx["proc_msg"].message_id, ctx["message_id"]
                            )

                            # Add emoji reactions (non-blocking)
                            try:
                                await GroupMentionHandler._set_message_reactions(
                                    context, query.message.chat_id, query.message.message_id
                                )
                            except Exception as e:
                                logger.warning(f"Error setting reactions: {e}")
                        else:
                            await query.edit_message_text(
                                "❌ Error creating ticket. Please try again."
                            )

                        del _pending_confirmations[callback_key]

            elif data.startswith("cancel_ticket_"):
                # Extract user_id and chat_id from cancel button data
                parts = data.split("_")
                if len(parts) >= 4:
                    user_id = int(parts[2])
                    chat_id = int(parts[3])
                    callback_key = f"{user_id}_{chat_id}"

                    # Permission verification for cancel
                    is_authorized, error_msg = GroupMentionHandler._verify_button_permission(
                        clicker_user_id, callback_key
                    )
                    if not is_authorized:
                        await query.answer(error_msg, show_alert=True)
                        return

                    await query.answer()
                    await query.edit_message_text("❌ Ticket creation cancelled.")

                    if callback_key in _pending_confirmations:
                        del _pending_confirmations[callback_key]
                else:
                    await query.answer("❌ Invalid button data.", show_alert=True)

        except Exception as e:
            logger.error(f"Error handling confirmation button: {e}", exc_info=True)
            try:
                await query.answer("Error processing your request.", show_alert=True)
            except:
                logger.error("Could not send error response")

    @staticmethod
    async def _download_attachments(message, user_id: int) -> List[dict]:
        """
        Download attachments (photo or document) from message

        Returns:
            List of attachment info dicts with filename, path, and type
        """
        attachments = []
        try:
            # Check for photos
            if message.photo:
                logger.info(f"Message has {len(message.photo)} photo(s)")
                # Get the largest photo
                photo = message.photo[-1]
                file_info = await photo.get_file()

                # Validate size
                if GroupMentionHandler._validate_file_size(file_info.file_size):
                    # Download and save
                    filename = f"photo_{user_id}_{len(attachments)}.jpg"
                    file_content = await file_info.download_as_bytearray()

                    from services.ticket_service import TicketService
                    file_path = TicketService.save_attachment(None, filename, bytes(file_content))

                    attachments.append({
                        "filename": filename,
                        "type": "photo",
                        "local_path": file_path
                    })
                    logger.info(f"Downloaded photo: {filename}")
                else:
                    logger.warning(f"Photo too large: {file_info.file_size} bytes")

            # Check for documents
            if message.document:
                logger.info(f"Message has document")
                doc = message.document

                # Validate file type and size
                if GroupMentionHandler._validate_file_type(doc.file_name or ""):
                    file_info = await doc.get_file()

                    if GroupMentionHandler._validate_file_size(file_info.file_size):
                        # Download and save
                        filename = doc.file_name or f"document_{user_id}_{len(attachments)}"
                        file_content = await file_info.download_as_bytearray()

                        from services.ticket_service import TicketService
                        file_path = TicketService.save_attachment(None, filename, bytes(file_content))

                        attachments.append({
                            "filename": filename,
                            "type": "document",
                            "local_path": file_path
                        })
                        logger.info(f"Downloaded document: {filename}")
                    else:
                        logger.warning(f"Document too large: {file_info.file_size} bytes")
                else:
                    logger.warning(f"Unsupported file type: {doc.file_name}")

        except Exception as e:
            logger.error(f"Error downloading attachments: {e}", exc_info=True)

        return attachments

    @staticmethod
    def _validate_file_size(file_size: int) -> bool:
        """Check if file size is within limits"""
        max_bytes = settings.app.MAX_FILE_SIZE_MB * 1024 * 1024
        return file_size <= max_bytes

    @staticmethod
    def _validate_file_type(filename: str) -> bool:
        """Check if file type is supported"""
        supported_types = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt', '.xlsx', '.xls'}
        ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ""
        return ext in supported_types

    @staticmethod
    async def _handle_bulk_mention(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    message, chat, bot_username: str, issue_text: str,
                                    author_id: int, author_name: str, mentioned_usernames: list):
        """
        Handle bulk mention - create separate tickets for each mentioned user

        Args:
            mentioned_usernames: List of @mentioned usernames (without @)
        """
        try:
            logger.info(f"Handling bulk mention for {len(mentioned_usernames)} users")

            # Send initial processing message
            proc_msg = await message.reply_text(
                f"⏳ Creating {len(mentioned_usernames)} ticket(s) for {', '.join(f'@{u}' for u in mentioned_usernames[:5])}{'...' if len(mentioned_usernames) > 5 else ''}",
                reply_to_message_id=message.message_id
            )

            created_tickets = []
            failed_mentions = []

            # Create ticket for each mentioned user
            from services.employee_service import EmployeeService

            for username in mentioned_usernames:
                try:
                    # Try to get user_id from username service
                    mentioned_user_id = UsernameService.get_user_id_by_username(username)

                    if not mentioned_user_id:
                        logger.warning(f"Could not resolve @{username} to user_id")
                        failed_mentions.append(username)
                        continue

                    # Get email for mentioned user
                    mentioned_email = UsernameService.get_email_by_username(username)
                    if not mentioned_email:
                        mentioned_email = EmployeeService.get_employee_email(mentioned_user_id)
                    if not mentioned_email:
                        mentioned_email = f"user.{mentioned_user_id}@{settings.company.EMAIL_DOMAIN}"

                    logger.info(f"Creating ticket for @{username} ({mentioned_user_id}): {mentioned_email}")

                    # Download attachments
                    attachments_list = await GroupMentionHandler._download_attachments(
                        message, mentioned_user_id
                    )

                    # Create ticket
                    ticket_id = await asyncio.get_event_loop().run_in_executor(
                        _thread_pool,
                        lambda uid=mentioned_user_id, un=username: GroupMentionHandler._create_ticket_sync(
                            uid, un, issue_text, chat.id, chat.title, chat.type,
                            message.message_id, attachments_list
                        )
                    )

                    if ticket_id:
                        created_tickets.append((username, ticket_id))
                        logger.info(f"Ticket created for @{username}: {ticket_id}")
                    else:
                        failed_mentions.append(username)
                        logger.error(f"Failed to create ticket for @{username}")

                except Exception as e:
                    logger.error(f"Error creating ticket for @{username}: {e}")
                    failed_mentions.append(username)

            # Update processing message with results
            if created_tickets:
                from datetime import datetime
                created_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")

                result_text = f"✅ **Created {len(created_tickets)} Ticket(s)**\n**Date:** {created_date}\n\n"
                for username, ticket_id in created_tickets:
                    result_text += f"🎫 **@{username}** → `{ticket_id}`\n"

                if failed_mentions:
                    result_text += f"\n⚠️ Could not create for: {', '.join(f'@{u}' for u in failed_mentions)}"
                    result_text += "\n(Make sure they've interacted with the bot before)"

                result_text += f"\n\n**Issue:** {issue_text}"
            else:
                result_text = f"❌ Could not create tickets for: {', '.join(f'@{u}' for u in failed_mentions)}\n\nMake sure mentioned users have interacted with the bot first."

            await proc_msg.edit_text(result_text, parse_mode="Markdown")

            # Add reactions
            try:
                await GroupMentionHandler._set_message_reactions(
                    context, chat.id, proc_msg.message_id
                )
            except Exception as e:
                logger.warning(f"Error setting reactions: {e}")

        except Exception as e:
            logger.error(f"Error in bulk mention handler: {e}", exc_info=True)
            try:
                await message.reply_text(
                    "❌ Error processing bulk mention. Please try again.",
                    reply_to_message_id=message.message_id
                )
            except:
                logger.error("Could not send error message")

    @staticmethod
    async def _set_message_reactions(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int) -> bool:
        """
        Add reaction emojis to a message for quick feedback

        Returns True if successful, False if failed (non-blocking failure)
        """
        try:
            # Reactions: ✅ (Done), ❌ (Issue), 🔄 (Reassign)
            reactions = ["✅", "❌", "🔄"]

            for reaction in reactions:
                try:
                    # Use emoji string directly
                    await context.bot.set_message_reaction(
                        chat_id=chat_id,
                        message_id=message_id,
                        reaction=[ReactionType(emoji=reaction)],
                        is_big=False
                    )
                    # Add slight delay between reactions to avoid rate limiting
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.warning(f"Could not set reaction {reaction}: {e}")
                    # Continue with next reaction even if one fails

            logger.info(f"Reactions set on message {message_id} in chat {chat_id}")
            return True

        except Exception as e:
            logger.warning(f"Could not set reactions on message: {e}")
            # Non-blocking failure - reactions are optional UX enhancement
            return False

    @staticmethod
    def _create_ticket_sync(user_id: int, user_name: str, issue_text: str, chat_id: int,
                            chat_name: str, chat_type: str, source_message_id: int,
                            attachments_list: List[dict] = None) -> Optional[str]:
        """
        Create ticket synchronously (for thread pool execution)
        """
        try:
            logger.info("-" * 60)
            logger.info("TICKET CREATION STARTED")
            logger.info("-" * 60)

            from services.ticket_service import TicketService
            from services.spiceworks_service import SpiceworksService
            from services.employee_service import EmployeeService

            logger.info(f"User: {user_name} (ID: {user_id})")
            logger.info(f"Issue: {issue_text[:60]}")
            logger.info(f"Group: {chat_name} (ID: {chat_id})")
            logger.info(f"Attachments: {len(attachments_list) if attachments_list else 0}")

            # Extract department
            department = GroupMentionHandler._extract_department(issue_text)
            logger.info(f"Department: {department}")

            # Get email
            registered_email = EmployeeService.get_employee_email(user_id)
            if registered_email:
                user_email = registered_email
                logger.info(f"Using registered email: {user_email}")
            else:
                user_email = f"user.{user_id}@{settings.company.EMAIL_DOMAIN}"
                logger.info(f"Using generated email: {user_email}")

            # Prepare ticket data with group tracking
            ticket_data = {
                "name": user_name,
                "email": user_email,
                "department": department,
                "issue": issue_text[:200],
                "description": issue_text,
                "priority": "Normal",
                "source": "telegram_group_mention",
                "group_id": chat_id,
                "group_name": chat_name,
                "group_type": chat_type,
                "source_message_id": source_message_id,
                "attachments": []
            }

            # Add attachments if present
            if attachments_list:
                ticket_data["attachments"] = attachments_list

            logger.info(f"Ticket data prepared with {len(attachments_list or [])} attachments")

            # Create local ticket
            logger.info("Creating local ticket...")
            ticket_id = TicketService.create_ticket(ticket_data)
            logger.info(f"Local ticket created: {ticket_id}")

            # Move attachments from temp to ticket directory
            if attachments_list:
                import shutil
                for att_info in attachments_list:
                    try:
                        old_path = att_info.get('local_path', '')
                        new_path = TicketService.get_attachment_path(ticket_id, att_info['filename'])
                        if old_path and new_path:
                            shutil.move(old_path, str(new_path))
                            logger.info(f"Moved attachment: {att_info['filename']}")
                    except Exception as e:
                        logger.error(f"Error moving attachment: {e}")

            # Send to Spiceworks
            logger.info("Sending to Spiceworks...")
            spiceworks_result = SpiceworksService.send_ticket_to_spiceworks(
                ticket_data,
                ticket_id
            )
            logger.info(f"Spiceworks result: {spiceworks_result}")

            if not spiceworks_result:
                logger.warning(f"Spiceworks send failed for {ticket_id}, but continuing...")

            # Send confirmation email
            logger.info(f"Sending confirmation email to {user_email}...")
            try:
                email_result = SpiceworksService.send_ticket_confirmation(
                    user_email,
                    ticket_id,
                    ticket_data
                )
                logger.info(f"Confirmation email result: {email_result}")
            except Exception as email_error:
                logger.error(f"Email error: {email_error}")

            logger.info(f"TICKET CREATION COMPLETE: {ticket_id}")
            logger.info("-" * 60)

            return ticket_id

        except Exception as e:
            logger.error(f"TICKET CREATION FAILED: {e}", exc_info=True)
            logger.error("-" * 60)
            return None

    @staticmethod
    def _extract_department(text: str) -> str:
        """Extract department from issue text"""
        text_lower = text.lower()

        departments = {
            "IT": ["wifi", "internet", "network", "computer", "email", "vpn", "password", "server", "tech", "laptop", "desktop", "printer", "software", "hardware","reset password"],
            "Maintenance": ["broken", "leak", "hvac", "temperature", "heat", "light", "bulb", "ac", "ac"],
            "Facilities": ["kitchen", "bathroom", "fridge", "coffee", "cleaning", "supplies", "chair", "desk"],
            "HR": ["benefits", "payroll", "vacation", "leave", "contract", "hr"],
            "Security": ["lock", "access", "badge", "door", "safe"],
        }

        for dept, keywords in departments.items():
            if any(kw in text_lower for kw in keywords):
                return dept.capitalize()

        return "General Support"

    @staticmethod
    def _extract_mentioned_users(text: str, bot_username: str) -> list:
        """
        Extract all @mentioned usernames from text (excluding bot mention)

        Args:
            text: Message text to parse
            bot_username: Bot's username to exclude

        Returns:
            List of usernames (without @) mentioned in text
        """
        import re

        # Find all @mentions
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, text)

        # Filter out bot mention and duplicates
        bot_username_lower = bot_username.lower()
        unique_mentions = []
        seen = set()

        for mention in mentions:
            mention_lower = mention.lower()
            if mention_lower != bot_username_lower and mention_lower not in seen:
                unique_mentions.append(mention)
                seen.add(mention_lower)

        return unique_mentions

    @staticmethod
    def _extract_issue_text_from_bulk_mention(text: str, all_mentions: list) -> str:
        """
        Extract issue text by removing all @mentions from message

        Args:
            text: Original message text
            all_mentions: All @mentions to remove

        Returns:
            Cleaned issue text
        """
        import re

        issue_text = text
        for mention in all_mentions:
            # Remove @mention with various whitespace handling
            issue_text = re.sub(f'@{mention}\\s*', '', issue_text, flags=re.IGNORECASE)

        return issue_text.strip()

    @staticmethod
    def get_mention_handler():
        """Get mention handler"""
        async def debug_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Debug wrapper to log all messages"""
            if update.message and update.effective_chat:
                logger.info(f"[MENTION_HANDLER_WRAPPER_CALLED] Chat: {update.effective_chat.type}, Text: {update.message.text[:100] if update.message.text else 'NO TEXT'}")
            else:
                logger.info(f"[MENTION_HANDLER_WRAPPER] Update has no message: {type(update)}")
            await GroupMentionHandler.handle_mention(update, context)

        logger.info("Creating mention handler with support for TEXT and MEDIA (photos, documents)")
        return MessageHandler(
            filters.TEXT & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
            debug_wrapper
        )

    @staticmethod
    def get_media_mention_handler():
        """Get media mention handler for photos and documents with mentions"""
        async def media_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Handle media mentions"""
            if not update.message:
                return

            # Check if message has mention text
            message_text = update.message.caption or ""
            if not message_text:
                return

            bot_info = await context.bot.get_me()
            mention_pattern = f"@{bot_info.username}"

            if mention_pattern not in message_text:
                return

            # Process as mention
            await GroupMentionHandler.handle_mention(update, context)

        logger.info("Creating media mention handler for photos and documents")
        return MessageHandler(
            (filters.PHOTO | filters.Document.ALL) & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
            media_wrapper
        )

    @staticmethod
    def get_welcome_handler():
        """Get welcome handler"""
        from telegram.ext import ChatMemberHandler
        return ChatMemberHandler(
            GroupMentionHandler.handle_member_status_update,
            ChatMemberHandler.MY_CHAT_MEMBER
        )

    @staticmethod
    def get_confirmation_handler():
        """Get button confirmation handler"""
        return CallbackQueryHandler(
            GroupMentionHandler.handle_confirmation_button,
            pattern="^(create_ticket_|cancel_ticket_)"
        )

