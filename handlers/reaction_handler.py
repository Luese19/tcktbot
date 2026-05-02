"""Handle message reactions to create tickets directly - IT team feature"""
from telegram import Update, Message, Chat
from telegram.ext import ContextTypes, MessageReactionHandler, BaseHandler
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from utils.logger import get_logger
from config.settings import settings
from services.spiceworks_service import SpiceworksService
from config.departments import get_auto_routed_priority

logger = get_logger(__name__)

# Thread pool for blocking operations (email sending)
_thread_pool = ThreadPoolExecutor(max_workers=2)


class ReactionTicketHandler:
    """Handle message reactions from IT team to create support tickets"""

    @staticmethod
    def get_reaction_handler() -> MessageReactionHandler:
        """Get the message reaction handler"""
        async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.info("[REACTION HANDLER] ============ CALLBACK TRIGGERED ============")
            await ReactionTicketHandler.handle_message_reaction(update, context)

        logger.info("[INIT] Creating MessageReactionHandler")
        # Don't filter by user_id in handler - do it in callback instead
        # This avoids the "can not filter for users and include anonymous reactions" error
        handler = MessageReactionHandler(handle_reaction)
        logger.info("[INIT] MessageReactionHandler created successfully")
        return handler

    @staticmethod
    def _is_it_team_member(user_id: int) -> bool:
        """Check if user is an IT team member"""
        it_team_ids = settings.app.get_it_team_user_ids()
        if not it_team_ids:
            logger.warning("IT_TEAM_USER_IDS not configured")
            return False
        return user_id in it_team_ids

    @staticmethod
    def _should_trigger_ticket(reaction_emoji: str) -> bool:
        """Check if the reaction should trigger ticket creation"""
        if not settings.app.TICKET_REACTION_TRIGGERS:
            # If no triggers configured, all reactions trigger
            return True
        return reaction_emoji in settings.app.TICKET_REACTION_TRIGGERS

    @staticmethod
    async def handle_message_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle message reactions to create tickets directly.
        Only IT team members' reactions trigger ticket creation.
        """
        try:
            # Log every update received by this handler
            logger.info("=" * 60)
            logger.info("[REACTION HANDLER] Reaction update received")
            logger.info(f"[REACTION HANDLER] Message ID: {update.message_reaction.message_id if update.message_reaction else 'N/A'}")
            logger.info("=" * 60)

            if not update.message_reaction:
                logger.debug("[REACTION] No message_reaction in update")
                return

            reaction = update.message_reaction
            user_id = reaction.user.id if reaction.user else None

            logger.info("=" * 60)
            logger.info("[REACTION HANDLER] Reaction detected")
            logger.info("=" * 60)

            if not user_id:
                logger.warning("[REACTION] Could not get user ID from reaction")
                return

            # Get date and time from reaction
            from datetime import datetime
            import pytz
            
            # Use UTC time from the update and convert to Philippine Time (GMT+8)
            utc_time = reaction.date if reaction.date else datetime.now(pytz.utc)
            ph_timezone = pytz.timezone('Asia/Manila')
            ph_time = utc_time.astimezone(ph_timezone)
            formatted_time = ph_time.strftime("%Y-%m-%d %I:%M:%S %p PHT")
            logger.info(f"[REACTION] Reaction time: {formatted_time}")

            # Check if user is IT team member
            if not ReactionTicketHandler._is_it_team_member(user_id):
                logger.debug(f"[REACTION] User {user_id} is not an IT team member")
                return

            logger.info(f"[REACTION] IT team member {user_id} reacted")

            # Get the reaction type
            if not reaction.new_reaction:
                logger.debug("[REACTION] New reaction is empty (reaction removed)")
                return

            reaction_emoji = reaction.new_reaction[0].emoji if reaction.new_reaction else None
            if not reaction_emoji:
                logger.debug("[REACTION] Could not extract emoji")
                return

            logger.info(f"[REACTION] Reaction emoji: {reaction_emoji}")

            # Check if this reaction should trigger ticket creation
            if not ReactionTicketHandler._should_trigger_ticket(reaction_emoji):
                logger.debug(f"[REACTION] Reaction {reaction_emoji} doesn't trigger tickets")
                return

            # Get chat and message info - use reaction.chat for group messages
            chat_id = reaction.chat.id if reaction.chat else None
            if not chat_id:
                logger.error("[REACTION] Could not determine chat_id from reaction.chat")
                return
            
            message_id = reaction.message_id
            sender_name = reaction.user.first_name if reaction.user else "Unknown User"
            sender_username = reaction.user.username if reaction.user else None
            sender_id = reaction.user.id

            logger.info(f"[REACTION] Chat ID: {chat_id}, Message ID: {message_id}")
            logger.info(f"[REACTION] From: {sender_name} (ID: {sender_id})")

            # Try to get the original message from cache
            from services.message_cache_service import MessageCacheService
            cached_message = MessageCacheService.get_message(chat_id, message_id)

            logger.info(f"[REACTION] Looking for cached message - Chat: {chat_id}, Message ID: {message_id}")

            if cached_message and cached_message.strip():
                message_text = cached_message
                logger.info(f"[REACTION] Found cached message: {message_text[:100]}")
            else:
                # Fallback message if not in cache
                message_text = f"Support request on message #{message_id}"
                logger.warning(f"[REACTION] Message NOT found in cache, using fallback. Cache stats: {MessageCacheService.get_cache_stats()}")

            logger.info(f"[REACTION] Final message_text: {message_text[:100]}")

            # Extract issue and description
            issue_text = message_text
            if "@" in issue_text:
                # Remove bot mentions and usernames
                parts = []
                for word in issue_text.split():
                    if not (word.startswith("@") or word.startswith("#")):
                        parts.append(word)
                issue_text = " ".join(parts).strip()

            # Auto-detect department from reaction emoji and context
            reaction_emoji = reaction.new_reaction[0].emoji if reaction.new_reaction else ""
            department = ReactionTicketHandler._detect_department(issue_text)
            logger.info(f"[REACTION] Detected department: {department}")

            # Prepare ticket data for Spiceworks
            ticket_data = {
                "name": sender_name,
                "email": f"{sender_username}@{settings.company.EMAIL_DOMAIN}" if sender_username else f"user_{sender_id}@{settings.company.EMAIL_DOMAIN}",
                "department": department,
                "issue": f"[Reaction Ticket] {issue_text[:150]}",  # Add indicator that it's from reaction
                "description": f"Ticket created via reaction from IT team member: {sender_name}\n\nOriginal Message:\n{issue_text}",
                "priority": get_auto_routed_priority(department, issue_text)
            }

            logger.info(f"[REACTION] Ticket data: {ticket_data}")

            # Generate ticket ID
            ticket_id = f"RTK-{chat_id}-{message_id}"

            # Send to Spiceworks in thread pool
            loop = asyncio.get_event_loop()
            try:
                success = await loop.run_in_executor(
                    _thread_pool,
                    SpiceworksService.send_ticket_to_spiceworks,
                    ticket_data,
                    ticket_id,
                    None  # No attachments from reactions
                ) # type: ignore

                if success:
                    logger.info(f"[REACTION] Ticket created successfully: {ticket_id}")

                    # Notify IT team member
                    notification = f"""✅ <b>Ticket Created Successfully!</b>

📌 <b>Ticket ID:</b> <code>{ticket_id}</code>
👤 <b>Reported By:</b> {sender_name}
🕐 <b>Time:</b> {formatted_time}
📂 <b>Department:</b> {department}
⚡ <b>Priority:</b> {ticket_data['priority']}

📝 <b>Issue Summary:</b>
<code>{issue_text[:300]}</code>

✉️ Email notification has been sent to Spiceworks."""

                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=notification,
                            parse_mode="HTML"
                        )
                        logger.info(f"[REACTION] Notification sent to IT member {user_id}")
                    except Exception as e:
                        logger.warning(f"[REACTION] Could not notify IT member: {e}")

                    # If message is in a group, notify the employee too
                    if update.effective_chat.type in ["group", "supergroup"]:
                        employee_notification = f"""🎫 <b>Your Issue Has Been Registered!</b>

📌 <b>Ticket ID:</b> <code>{ticket_id}</code>
🕐 <b>Date & Time:</b> {formatted_time}

📝 <b>Issue:</b>
<code>{issue_text[:300]}</code>

✅ Your issue has been assigned to our IT team and a support ticket has been created in Spiceworks. You will receive an email confirmation shortly.

📧 The IT team will contact you soon. Please monitor your email for updates."""

                        try:
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=employee_notification,
                                parse_mode="HTML",
                                reply_to_message_id=message_id
                            )
                            logger.info(f"[REACTION] Notification sent in group")
                        except Exception as e:
                            logger.warning(f"[REACTION] Could not reply in group: {e}")

                else:
                    logger.error("[REACTION] Failed to create ticket in Spiceworks")
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text="❌ Failed to create ticket. Please try again or contact admin. Error: Spiceworks submission failed"
                        )
                    except Exception as e:
                        logger.warning(f"[REACTION] Could not send error notification: {e}")

            except Exception as e:
                logger.error(f"[REACTION] Error during ticket creation: {e}", exc_info=True)
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"❌ Error creating ticket: {str(e)[:100]}"
                    )
                except Exception as notify_error:
                    logger.warning(f"[REACTION] Could not send error notification: {notify_error}")

        except Exception as e:
            logger.error(f"[REACTION] Unexpected error in reaction handler: {e}", exc_info=True)

    @staticmethod
    def _detect_department(text: str) -> str:
        """Auto-detect department from message keywords"""
        text_lower = text.lower()

        # Department keywords mapping
        keywords = {
            "IT": ["computer", "laptop", "printer", "network", "internet", "wifi", "server", "password",
                   "software", "hardware", "email", "access", "vpn", "offline", "down", "broken", "error", "PC", "mac", "windows", "urgent", "asap"],
                   
        }

        for department, dept_keywords in keywords.items():
            for keyword in dept_keywords:
                if keyword in text_lower:
                    return department

        return "IT"  # Default to IT


__all__ = ['ReactionTicketHandler']
