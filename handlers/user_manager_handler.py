"""User management handlers for admins - add/remove admins and IT team members"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.logger import get_logger
from services.user_manager_service import UserManagerService
from config.settings import settings

logger = get_logger(__name__)


class UserManagerHandlers:
    """Handlers for user management commands (admins only)"""

    @staticmethod
    def _is_super_admin(user_id: int) -> bool:
        """Check if user is a super admin (from .env ADMIN_USER_IDS)"""
        return user_id in settings.app.SUPER_ADMIN_USER_IDS

    @staticmethod
    async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a user to the admin list - /add_admin <user_id>"""
        try:
            if not update.message:
                logger.error("Add admin command: update.message is None")
                return
            
            user_id = update.effective_user.id

            # Check if user is super admin
            if not UserManagerHandlers._is_super_admin(user_id):
                await update.message.reply_text("❌ Permission denied. Only super admins can manage user roles.")
                logger.warning(f"User {user_id} attempted to add admin without permission")
                return

            # Parse user_id from command
            if not context.args:
                await update.message.reply_text(
                    "Usage: `/add_admin <user_id>`\n"
                    "Example: `/add_admin 123456789`",
                    parse_mode="Markdown"
                )
                return

            try:
                target_user_id = int(context.args[0])
                if target_user_id <= 0:
                    await update.message.reply_text(
                        "❌ Invalid user ID. User IDs must be positive numbers."
                    )
                    return
            except ValueError:
                await update.message.reply_text(
                    f"❌ Invalid user ID: '{context.args[0]}'. Please provide a valid numeric user ID."
                )
                return

            # Check if user is already a super admin
            if target_user_id in settings.app.SUPER_ADMIN_USER_IDS:
                await update.message.reply_text(
                    f"ℹ️ User {target_user_id} is already a super admin"
                )
                return

            # Add the user
            if UserManagerService.add_admin_user(target_user_id):
                await update.message.reply_text(
                    f"✅ Successfully added user {target_user_id} to admin list.\n"
                    f"They can now use admin commands: `/list`, `/view`, `/delete`, `/reply`, etc.",
                    parse_mode="Markdown"
                )
                logger.info(f"Admin {user_id} added user {target_user_id} to admin list")
            else:
                await update.message.reply_text(
                    f"ℹ️ User {target_user_id} is already in the admin list."
                )

        except Exception as e:
            logger.error(f"Error in add_admin_command: {e}")
            await update.message.reply_text("❌ Error processing command.")

    @staticmethod
    async def remove_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove a user from the admin list - /remove_admin <user_id>"""
        try:
            if not update.message:
                logger.error("Remove admin command: update.message is None")
                return
            
            user_id = update.effective_user.id

            # Check if user is super admin
            if not UserManagerHandlers._is_super_admin(user_id):
                await update.message.reply_text("❌ Permission denied. Only super admins can manage user roles.")
                logger.warning(f"User {user_id} attempted to remove admin without permission")
                return

            # Parse user_id from command
            if not context.args:
                await update.message.reply_text(
                    "Usage: `/remove_admin <user_id>`\n"
                    "Example: `/remove_admin 123456789`",
                    parse_mode="Markdown"
                )
                return

            try:
                target_user_id = int(context.args[0])
                if target_user_id <= 0:
                    await update.message.reply_text(
                        "❌ Invalid user ID. User IDs must be positive numbers."
                    )
                    return
            except ValueError:
                await update.message.reply_text(
                    f"❌ Invalid user ID: '{context.args[0]}'. Please provide a valid numeric user ID."
                )
                return

            # Check if user is a super admin (cannot remove)
            if target_user_id in settings.app.SUPER_ADMIN_USER_IDS:
                await update.message.reply_text(
                    f"❌ Cannot remove user {target_user_id} - they are a super admin (defined in .env)."
                )
                return

            # Remove the user
            if UserManagerService.remove_admin_user(target_user_id):
                await update.message.reply_text(
                    f"✅ Successfully removed user {target_user_id} from admin list.\n"
                    f"They can no longer use admin commands."
                )
                logger.info(f"Admin {user_id} removed user {target_user_id} from admin list")
            else:
                await update.message.reply_text(
                    f"ℹ️ User {target_user_id} is not in the admin list."
                )

        except Exception as e:
            logger.error(f"Error in remove_admin_command: {e}")
            await update.message.reply_text("❌ Error processing command.")

    @staticmethod
    async def add_it_member_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a user to the IT team - /add_it_member <user_id>"""
        try:
            if not update.message:
                logger.error("Add IT member command: update.message is None")
                return
            
            user_id = update.effective_user.id

            # Check if user is super admin
            if not UserManagerHandlers._is_super_admin(user_id):
                await update.message.reply_text("❌ Permission denied. Only super admins can manage user roles.")
                logger.warning(f"User {user_id} attempted to add IT member without permission")
                return

            # Parse user_id from command
            if not context.args:
                await update.message.reply_text(
                    "Usage: `/add_it_member <user_id>`\n"
                    "Example: `/add_it_member 123456789`",
                    parse_mode="Markdown"
                )
                return

            try:
                target_user_id = int(context.args[0])
                if target_user_id <= 0:
                    await update.message.reply_text(
                        "❌ Invalid user ID. User IDs must be positive numbers."
                    )
                    return
            except ValueError:
                await update.message.reply_text(
                    f"❌ Invalid user ID: '{context.args[0]}'. Please provide a valid numeric user ID."
                )
                return

            # Check if user is already a super IT member
            if target_user_id in settings.app.SUPER_IT_TEAM_USER_IDS:
                await update.message.reply_text(
                    f"ℹ️ User {target_user_id} is already a super IT team member (defined in .env)."
                )
                return

            # Add the user
            if UserManagerService.add_it_user(target_user_id):
                await update.message.reply_text(
                    f"✅ Successfully added user {target_user_id} to IT team.\n"
                    f"They can now create tickets via reactions.",
                    parse_mode="Markdown"
                )
                logger.info(f"Admin {user_id} added user {target_user_id} to IT team")
            else:
                await update.message.reply_text(
                    f"ℹ️ User {target_user_id} is already in the IT team."
                )

        except Exception as e:
            logger.error(f"Error in add_it_member_command: {e}")
            await update.message.reply_text("❌ Error processing command.")

    @staticmethod
    async def remove_it_member_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove a user from the IT team - /remove_it_member <user_id>"""
        try:
            if not update.message:
                logger.error("Remove IT member command: update.message is None")
                return
            
            user_id = update.effective_user.id

            # Check if user is super admin
            if not UserManagerHandlers._is_super_admin(user_id):
                await update.message.reply_text("❌ Permission denied. Only super admins can manage user roles.")
                logger.warning(f"User {user_id} attempted to remove IT member without permission")
                return

            # Parse user_id from command
            if not context.args:
                await update.message.reply_text(
                    "Usage: `/remove_it_member <user_id>`\n"
                    "Example: `/remove_it_member 123456789`",
                    parse_mode="Markdown"
                )
                return

            try:
                target_user_id = int(context.args[0])
                if target_user_id <= 0:
                    await update.message.reply_text(
                        "❌ Invalid user ID. User IDs must be positive numbers."
                    )
                    return
            except ValueError:
                await update.message.reply_text(
                    f"❌ Invalid user ID: '{context.args[0]}'. Please provide a valid numeric user ID."
                )
                return

            # Check if user is a super IT member (cannot remove)
            if target_user_id in settings.app.SUPER_IT_TEAM_USER_IDS:
                await update.message.reply_text(
                    f"❌ Cannot remove user {target_user_id} - they are a super IT team member (defined in .env)."
                )
                return

            # Remove the user
            if UserManagerService.remove_it_user(target_user_id):
                await update.message.reply_text(
                    f"✅ Successfully removed user {target_user_id} from IT team.\n"
                    f"They can no longer create tickets via reactions."
                )
                logger.info(f"Admin {user_id} removed user {target_user_id} from IT team")
            else:
                await update.message.reply_text(
                    f"ℹ️ User {target_user_id} is not in the IT team."
                )

        except Exception as e:
            logger.error(f"Error in remove_it_member_command: {e}")
            await update.message.reply_text("❌ Error processing command.")

    @staticmethod
    async def list_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all admin users - /list_admins"""
        try:
            if not update.message:
                logger.error("List admins command: update.message is None")
                return
            
            user_id = update.effective_user.id

            # Check if user is super admin
            if not UserManagerHandlers._is_super_admin(user_id):
                await update.message.reply_text("❌ Permission denied. Only super admins can view user lists.")
                logger.warning(f"User {user_id} attempted to list admins without permission")
                return

            # Get all admins
            all_admins = settings.app.get_admin_user_ids()

            if not all_admins:
                await update.message.reply_text("📋 No admin users configured.")
                return

            response = "👨‍💼 **Admin Users:**\n\n"

            # Separate super admins and dynamic admins
            super_admins = set(settings.app.SUPER_ADMIN_USER_IDS)
            dynamic_admins = all_admins - super_admins

            if super_admins:
                response += "🔒 **Super Admins (from .env - cannot be removed):**\n"
                for admin_id in sorted(super_admins):
                    response += f"  • {admin_id}\n"

            if dynamic_admins:
                response += "\n👤 **Dynamic Admins (can be removed):**\n"
                for admin_id in sorted(dynamic_admins):
                    response += f"  • {admin_id}\n"

            response += f"\n**Total: {len(all_admins)} admin(s)**"

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in list_admins_command: {e}")
            await update.message.reply_text("❌ Error retrieving admin list.")

    @staticmethod
    async def list_it_members_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all IT team members - /list_it_members"""
        try:
            if not update.message:
                logger.error("List IT members command: update.message is None")
                return
            
            user_id = update.effective_user.id

            # Check if user is super admin
            if not UserManagerHandlers._is_super_admin(user_id):
                await update.message.reply_text("❌ Permission denied. Only super admins can view user lists.")
                logger.warning(f"User {user_id} attempted to list IT members without permission")
                return

            # Get all IT team members
            all_it_members = settings.app.get_it_team_user_ids()

            if not all_it_members:
                await update.message.reply_text("📋 No IT team members configured.")
                return

            response = "👨‍💻 **IT Team Members:**\n\n"

            # Separate super IT members and dynamic members
            super_it_members = set(settings.app.SUPER_IT_TEAM_USER_IDS)
            dynamic_it_members = all_it_members - super_it_members

            if super_it_members:
                response += "🔒 **Super IT Members (from .env - cannot be removed):**\n"
                for member_id in sorted(super_it_members):
                    response += f"  • {member_id}\n"

            if dynamic_it_members:
                response += "\n👤 **Dynamic IT Members (can be removed):**\n"
                for member_id in sorted(dynamic_it_members):
                    response += f"  • {member_id}\n"

            response += f"\n**Total: {len(all_it_members)} IT member(s)**"

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in list_it_members_command: {e}")
            await update.message.reply_text("❌ Error retrieving IT team list.")


def get_user_manager_command_handlers():
    """Create user management command handlers"""
    return [
        CommandHandler("add_admin", UserManagerHandlers.add_admin_command),
        CommandHandler("remove_admin", UserManagerHandlers.remove_admin_command),
        CommandHandler("add_it_member", UserManagerHandlers.add_it_member_command),
        CommandHandler("remove_it_member", UserManagerHandlers.remove_it_member_command),
        CommandHandler("list_admins", UserManagerHandlers.list_admins_command),
        CommandHandler("list_it_members", UserManagerHandlers.list_it_members_command),
    ]
