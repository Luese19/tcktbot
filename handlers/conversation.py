"""Conversation handlers for Help Desk Bot"""
from telegram import Update
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from utils.logger import get_logger

logger = get_logger(__name__)

class ConversationState:
    START, DEPT, NAME, EMAIL, ISSUE, DESCRIPTION, ATTACHMENTS, PRIORITY, CONFIRM = range(9)

class ConvHandlers:
    ticket_data = {}

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        ConvHandlers.ticket_data[user_id] = {}

        from config.departments import create_department_keyboard
        await update.message.reply_text(
            "Welcome to Help Desk Bot! Please select your department:",
            reply_markup=create_department_keyboard()
        )
        return ConversationState.DEPT

    @staticmethod
    async def dept_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        dept = query.data.replace("dept_", "")

        ConvHandlers.ticket_data[user_id]['department'] = dept
        await query.answer()
        await query.edit_message_text(f"Selected: {dept}\n\nWhat is your name?")
        return ConversationState.NAME

    @staticmethod
    async def name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
        from config.settings import settings
        user_id = update.effective_user.id
        name = update.message.text.strip()

        # Validate name
        if len(name) < settings.app.MIN_NAME_LENGTH:
            await update.message.reply_text(
                f"❌ Name too short! Minimum {settings.app.MIN_NAME_LENGTH} characters."
            )
            return ConversationState.NAME

        if len(name) > settings.app.MAX_NAME_LENGTH:
            await update.message.reply_text(
                f"❌ Name too long! Maximum {settings.app.MAX_NAME_LENGTH} characters."
            )
            return ConversationState.NAME

        ConvHandlers.ticket_data[user_id]['name'] = name
        await update.message.reply_text("Enter your company email:")
        return ConversationState.EMAIL

    @staticmethod
    async def email_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
        from config.settings import settings
        user_id = update.effective_user.id
        email = update.message.text

        if not settings.is_company_email(email):
            await update.message.reply_text(f"Please use your company email (@{settings.company.EMAIL_DOMAIN})")
            return ConversationState.EMAIL

        ConvHandlers.ticket_data[user_id]['email'] = email
        await update.message.reply_text("What is the issue title or summary?")
        return ConversationState.ISSUE

    @staticmethod
    async def issue_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
        from config.settings import settings
        user_id = update.effective_user.id
        issue = update.message.text.strip()

        # Validate issue title
        if len(issue) < settings.app.MIN_ISSUE_LENGTH:
            await update.message.reply_text(
                f"❌ Issue too short! Minimum {settings.app.MIN_ISSUE_LENGTH} characters."
            )
            return ConversationState.ISSUE

        if len(issue) > settings.app.MAX_ISSUE_LENGTH:
            await update.message.reply_text(
                f"❌ Issue too long! Maximum {settings.app.MAX_ISSUE_LENGTH} characters."
            )
            return ConversationState.ISSUE

        ConvHandlers.ticket_data[user_id]['issue'] = issue
        await update.message.reply_text("Describe your issue in detail:")
        return ConversationState.DESCRIPTION

    @staticmethod
    async def description_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
        from config.settings import settings
        user_id = update.effective_user.id
        description = update.message.text.strip()

        # Validate description
        if len(description) < settings.app.MIN_DESCRIPTION_LENGTH:
            await update.message.reply_text(
                f"❌ Description too short! Minimum {settings.app.MIN_DESCRIPTION_LENGTH} characters."
            )
            return ConversationState.DESCRIPTION

        if len(description) > settings.app.MAX_DESCRIPTION_LENGTH:
            await update.message.reply_text(
                f"❌ Description too long! Maximum {settings.app.MAX_DESCRIPTION_LENGTH} characters."
            )
            return ConversationState.DESCRIPTION

        ConvHandlers.ticket_data[user_id]['description'] = description
        ConvHandlers.ticket_data[user_id]['attachments'] = []

        await update.message.reply_text(
            "You can now upload pictures or files to attach to your ticket.\n\n"
            "📷 Supported images: JPG, JPEG, PNG\n"
            "📄 Supported documents: PDF, DOC, DOCX\n\n"
            "Send as many files as needed, then type /done when finished."
        )
        return ConversationState.ATTACHMENTS

    @staticmethod
    async def done_attachments(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /done command to finish attachments"""
        from config.departments import create_priority_keyboard
        await update.message.reply_text(
            "Select priority level:",
            reply_markup=create_priority_keyboard()
        )
        return ConversationState.PRIORITY

    @staticmethod
    async def attachment_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
        from config.settings import settings
        user_id = update.effective_user.id

        # Download and store file
        try:
            file_obj = None
            file_name = None
            file_size = 0

            if update.message.photo:
                # Get the largest photo size
                file_obj = update.message.photo[-1]
                file_size = file_obj.file_size
                file_name = f"photo_{len(ConvHandlers.ticket_data[user_id]['attachments']) + 1}.jpg"
            elif update.message.document:
                file_obj = update.message.document
                file_size = file_obj.file_size
                file_name = file_obj.file_name
            else:
                await update.message.reply_text("Please send a picture or file.")
                return ConversationState.ATTACHMENTS

            # Check file size
            max_size_bytes = settings.app.MAX_FILE_SIZE_MB * 1024 * 1024
            if file_size > max_size_bytes:
                await update.message.reply_text(
                    f"❌ File too large! Maximum size is {settings.app.MAX_FILE_SIZE_MB}MB. "
                    f"Your file is {file_size / (1024*1024):.1f}MB."
                )
                return ConversationState.ATTACHMENTS

            # Check attachment limit
            if len(ConvHandlers.ticket_data[user_id]['attachments']) >= settings.app.MAX_ATTACHMENTS_PER_TICKET:
                await update.message.reply_text(
                    f"❌ Maximum {settings.app.MAX_ATTACHMENTS_PER_TICKET} attachments per ticket. "
                    f"Type /done to finish."
                )
                return ConversationState.ATTACHMENTS

            # Download file
            file_to_download = await file_obj.get_file()
            file_content = await file_to_download.download_as_bytearray()

            # Save file temporarily
            from services.ticket_service import TicketService
            file_path = TicketService.save_attachment(
                ticket_id=None,  # Temporary save without ticket_id
                filename=file_name,
                file_content=bytes(file_content)
            )

            # Store file reference
            ConvHandlers.ticket_data[user_id]['attachments'].append({
                'filename': file_name,
                'file_id': file_obj.file_id,
                'local_path': file_path,
                'type': 'photo' if update.message.photo else 'document'
            })

            current_count = len(ConvHandlers.ticket_data[user_id]['attachments'])
            remaining = settings.app.MAX_ATTACHMENTS_PER_TICKET - current_count
            await update.message.reply_text(
                f"✓ File uploaded ({current_count}/{settings.app.MAX_ATTACHMENTS_PER_TICKET}). "
                f"Send more or type /done to continue."
            )
            return ConversationState.ATTACHMENTS

        except Exception as e:
            logger.error(f"Error handling attachment: {e}")
            await update.message.reply_text("Error uploading file. Please try again.")
            return ConversationState.ATTACHMENTS

    @staticmethod
    async def priority_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        priority = query.data.replace("priority_", "")

        ConvHandlers.ticket_data[user_id]['priority'] = priority
        data = ConvHandlers.ticket_data[user_id]

        # Auto-route priority based on department and keywords
        from config.departments import get_auto_routed_priority
        auto_priority = get_auto_routed_priority(
            data.get('department', ''),
            data.get('issue', ''),
            data.get('description', '')
        )

        # Use auto-routed priority if different from user selection
        if auto_priority != priority:
            priority_msg = f"\n💡 Auto-routed to {auto_priority} based on issue type."
            priority = auto_priority
        else:
            priority_msg = ""

        ConvHandlers.ticket_data[user_id]['priority'] = priority

        attachments_summary = ""
        if data.get('attachments'):
            attachments_summary = "\n\nAttachments:"
            for att in data['attachments']:
                file_type = "📷" if att['type'] == 'photo' else "📄"
                attachments_summary += f"\n{file_type} {att['filename']}"

        summary = f"""Ticket Summary:
Name: {data['name']}
Email: {data['email']}
Department: {data['department']}
Priority: {priority}{priority_msg}

Issue: {data['issue']}
Description: {data['description']}{attachments_summary}

Submit this ticket?"""

        from config.departments import create_confirmation_keyboard
        await query.answer()
        await query.edit_message_text(summary, reply_markup=create_confirmation_keyboard())
        return ConversationState.CONFIRM

    @staticmethod
    async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id

        if query.data == "confirm_submit":
            await query.answer()

            # Create and send the ticket
            try:
                from services.ticket_service import TicketService
                from services.spiceworks_service import SpiceworksService
                import shutil
                from pathlib import Path

                ticket_data = ConvHandlers.ticket_data[user_id]

                # Save ticket locally (returns ticket_id)
                ticket_id = TicketService.create_ticket(ticket_data)
                logger.info(f"Ticket {ticket_id} created locally")

                # Move attachments from temp to ticket directory
                if ticket_data.get('attachments'):
                    for attachment_info in ticket_data['attachments']:
                        old_path = attachment_info.get('local_path', '')
                        if old_path and Path(old_path).exists():
                            try:
                                new_path = TicketService.get_attachment_path(ticket_id, attachment_info['filename'])
                                # Ensure parent directory exists
                                new_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.move(old_path, str(new_path))
                                attachment_info['local_path'] = str(new_path)
                            except Exception as e:
                                logger.error(f"Error moving attachment {attachment_info['filename']}: {e}")

                # Update ticket file with final attachment paths
                ticket = TicketService.get_ticket(ticket_id)
                if ticket and ticket_data.get('attachments'):
                    ticket['attachments'] = [
                        {'filename': att.get('filename'), 'type': att.get('type')}
                        for att in ticket_data['attachments']
                    ]
                    import json
                    ticket_file = TicketService.TICKETS_DIR / f"{ticket_id}.json"
                    with open(ticket_file, 'w', encoding='utf-8') as f:
                        json.dump(ticket, f, indent=2, ensure_ascii=False)

                # Send to Spiceworks with attachment paths
                attachment_paths = [
                    att.get('local_path') for att in ticket_data.get('attachments', [])
                    if att.get('local_path') and Path(att.get('local_path', '')).exists()
                ]
                spiceworks_sent = SpiceworksService.send_ticket_to_spiceworks(
                    ticket_data, ticket_id,
                    attachments=attachment_paths if attachment_paths else None
                )
                logger.info(f"Spiceworks send result for {ticket_id}: {spiceworks_sent}")

                # Send confirmation to user
                user_email = ticket_data.get('email')
                confirmation_sent = SpiceworksService.send_ticket_confirmation(user_email, ticket_id, ticket_data)
                logger.info(f"Confirmation send result for {ticket_id}: {confirmation_sent}")

                status_msg = "✓ Ticket submitted successfully!"

                if not spiceworks_sent:
                    status_msg += "\n⚠ Warning: Could not send to Spiceworks"

                await query.edit_message_text(status_msg)

            except Exception as e:
                logger.error(f"Error in confirm handler: {e}", exc_info=True)
                await query.edit_message_text(f"Error creating ticket: {str(e)}")

            ConvHandlers.ticket_data.pop(user_id, None)
            return ConversationHandler.END

        elif query.data == "confirm_cancel":
            await query.answer()
            await query.edit_message_text("Ticket cancelled")
            ConvHandlers.ticket_data.pop(user_id, None)
            return ConversationHandler.END

        return ConversationState.CONFIRM

    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        ConvHandlers.ticket_data.pop(user_id, None)
        await update.message.reply_text("Cancelled")
        return ConversationHandler.END

def get_conversation_handler():
    """Create conversation handler"""
    return ConversationHandler(
        entry_points=[CommandHandler("start", ConvHandlers.start)],
        states={
            ConversationState.DEPT: [CallbackQueryHandler(ConvHandlers.dept_select, pattern="^dept_")],
            ConversationState.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ConvHandlers.name_input)],
            ConversationState.EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ConvHandlers.email_input)],
            ConversationState.ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ConvHandlers.issue_input)],
            ConversationState.DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ConvHandlers.description_input)],
            ConversationState.ATTACHMENTS: [
                CommandHandler("done", ConvHandlers.done_attachments),
                MessageHandler(filters.PHOTO, ConvHandlers.attachment_input),
                MessageHandler(filters.Document.ALL, ConvHandlers.attachment_input),
            ],
            ConversationState.PRIORITY: [CallbackQueryHandler(ConvHandlers.priority_select, pattern="^priority_")],
            ConversationState.CONFIRM: [CallbackQueryHandler(ConvHandlers.confirm, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("cancel", ConvHandlers.cancel)],
        conversation_timeout=30*60,
        per_message=False
    )