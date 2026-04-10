"""Spiceworks integration service for ticket submission"""
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from pathlib import Path
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class SpiceworksService:
    """Service for submitting tickets to Spiceworks via email"""

    SUPPORTED_IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.gif'}
    SUPPORTED_DOC_TYPES = {'.pdf', '.doc', '.docx', '.txt', '.xlsx', '.xls'}

    @classmethod
    def send_ticket_to_spiceworks(cls, ticket_data: dict, ticket_id: str, attachments: list = None) -> bool:
        """
        Send ticket to Spiceworks via email with retry logic

        Args:
            ticket_data: Dict with keys: name, email, department, issue, description, priority
            ticket_id: Unique ticket identifier
            attachments: List of file paths to attach

        Returns:
            bool: True if sent successfully, False otherwise
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Prepare email content
                subject = f"{ticket_data.get('department', 'Support')} - {ticket_data.get('priority', 'Normal')} Priority: {ticket_data.get('issue', 'Support Request')}"

                # Create HTML email body
                html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .header {{ background-color: #2c3e50; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .header h2 {{ margin: 0; }}
        .field {{ margin: 12px 0; padding: 10px; background-color: #f9f9f9; border-left: 3px solid #3498db; }}
        .field strong {{ color: #2c3e50; }}
        .section {{ margin: 15px 0; padding: 12px; border: 1px solid #ecf0f1; border-radius: 4px; }}
        .section-title {{ font-weight: bold; color: #2c3e50; margin-bottom: 8px; }}
        .footer {{ margin-top: 20px; padding-top: 15px; border-top: 1px solid #ecf0f1; font-size: 12px; color: #95a5a6; }}
        .priority-urgent {{ color: #e74c3c; font-weight: bold; }}
        .priority-high {{ color: #f39c12; font-weight: bold; }}
        .priority-normal {{ color: #27ae60; font-weight: bold; }}
        .priority-low {{ color: #3498db; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🎫 New Support Ticket Submitted</h2>
        </div>

        <div class="field">
            <strong>Priority:</strong>
            <span class="priority-{ticket_data.get('priority', 'normal').lower()}">{ticket_data.get('priority', 'Normal')}</span>
        </div>

        <div class="field">
            <strong>Department:</strong> {ticket_data.get('department', 'General Support')}
        </div>

        <div class="field">
            <strong>Submitted by:</strong> {ticket_data.get('name')}
        </div>

        <div class="field">
            <strong>Email:</strong> {ticket_data.get('email')}
        </div>

        <div class="section">
            <div class="section-title">📋 Issue Title:</div>
            <div>{ticket_data.get('issue', 'No title provided')}</div>
        </div>

        <div class="section">
            <div class="section-title">📝 Description:</div>
            <div>{ticket_data.get('description', 'No description provided')}</div>
        </div>

        <div class="footer">
            <p>This ticket was submitted via Telegram Help Desk Bot<br>
            Company: {settings.company.NAME}</p>
        </div>
    </div>
</body>
</html>
"""

                # Plain text fallback
                plain_body = f"""Priority: {ticket_data.get('priority', 'Normal')}
Department: {ticket_data.get('department', 'General Support')}

Submitted by: {ticket_data.get('name')}
Email: {ticket_data.get('email')}

Issue Title:
{ticket_data.get('issue', 'No title provided')}

Description:
{ticket_data.get('description', 'No description provided')}
"""

                # Separate images and documents
                images = []
                documents = []

                if attachments:
                    for file_path in attachments:
                        if file_path and Path(file_path).exists():
                            file_ext = Path(file_path).suffix.lower()
                            if file_ext in cls.SUPPORTED_IMAGE_TYPES:
                                images.append(file_path)
                            else:
                                documents.append(file_path)

                # Create email with multipart structure
                msg = MIMEMultipart('related')
                msg['From'] = settings.email.SMTP_USERNAME
                msg['To'] = settings.email.SPICEWORKS_EMAIL
                msg['Subject'] = subject

                # Add text and HTML parts
                msg_alternative = MIMEMultipart('alternative')
                msg.attach(msg_alternative)

                # Add plain text first
                msg_text = MIMEText(plain_body, 'plain')
                msg_alternative.attach(msg_text)

                # Add HTML part
                msg_html = MIMEText(html_body, 'html')
                msg_alternative.attach(msg_html)

                # Attach inline images
                for idx, img_path in enumerate(images, 1):
                    try:
                        cls._attach_inline_image(msg_alternative, img_path, f"image{idx}")
                    except Exception as e:
                        logger.error(f"Error attaching inline image {img_path}: {e}")

                # Attach documents
                for doc_path in documents:
                    try:
                        cls._attach_file(msg, doc_path)
                    except Exception as e:
                        logger.error(f"Error attaching document {doc_path}: {e}")

                # Send email via SMTP
                with smtplib.SMTP(settings.email.SMTP_SERVER, settings.email.SMTP_PORT) as server:
                    if settings.email.SMTP_USE_TLS:
                        server.starttls()

                    server.login(settings.email.SMTP_USERNAME, settings.email.SMTP_PASSWORD)
                    server.send_message(msg)

                logger.info(f"Ticket {ticket_id} sent to Spiceworks successfully")
                return True

            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP Authentication failed for Spiceworks: {e}. Make sure to use Gmail App Password, not regular password.")
                return False
            except (smtplib.SMTPException, OSError) as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff: 2s, 4s, 8s
                    logger.warning(f"Failed to send ticket {ticket_id} (attempt {retry_count}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to send ticket {ticket_id} after {max_retries} attempts: {e}")
                    return False
            except Exception as e:
                logger.error(f"Error sending ticket to Spiceworks: {e}")
                return False

        return False

    @staticmethod
    def _attach_inline_image(msg: MIMEMultipart, file_path: str, cid: str):
        """Attach an image inline to email message"""
        file_path = Path(file_path)
        with open(file_path, 'rb') as img_file:
            img = MIMEImage(img_file.read())
            img.add_header('Content-ID', f'<{cid}>')
            img.add_header('Content-Disposition', 'inline', filename=file_path.name)
            msg.attach(img)

    @staticmethod
    def _attach_file(msg: MIMEMultipart, file_path: str):
        """Attach a file to email message"""
        file_path = Path(file_path)
        with open(file_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename= {file_path.name}')
        msg.attach(part)

    @classmethod
    def send_ticket_confirmation(cls, user_email: str, ticket_id: str, ticket_data: dict) -> bool:
        """
        Send HTML confirmation email to user

        Args:
            user_email: User's email address
            ticket_id: Unique ticket identifier
            ticket_data: Ticket information

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            subject = "Your Support Ticket Has Been Submitted"

            attachments_note = ""
            if ticket_data.get('attachments'):
                attachments_note = f"<br><strong>Attachments:</strong> {len(ticket_data['attachments'])} file(s) attached"

            # HTML email body
            html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .header {{ background-color: #27ae60; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; text-align: center; }}
        .header h2 {{ margin: 0; }}
        .field {{ margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-left: 3px solid #27ae60; }}
        .field strong {{ color: #2c3e50; }}
        .footer {{ margin-top: 20px; padding-top: 15px; border-top: 1px solid #ecf0f1; font-size: 12px; color: #95a5a6; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>✅ Ticket Submitted Successfully</h2>
        </div>

        <p>Hello {ticket_data.get('name')},</p>

        <p>Your support ticket has been successfully submitted. Our support team will review it and get back to you shortly.</p>

        <div class="field">
            <strong>Priority:</strong> {ticket_data.get('priority', 'Normal')}
        </div>

        <div class="field">
            <strong>Department:</strong> {ticket_data.get('department', 'General Support')}
        </div>

        <div class="field">
            <strong>Issue:</strong> {ticket_data.get('issue')}
        </div>

        <div class="field">
            <strong>Description:</strong> {ticket_data.get('description', '')}{attachments_note}
        </div>

        <div class="footer">
            <p>Best regards,<br>{settings.company.NAME} Support Team</p>
        </div>
    </div>
</body>
</html>
"""

            # Plain text fallback
            plain_body = f"""Hello {ticket_data.get('name')},

Your support ticket has been successfully submitted.

Priority: {ticket_data.get('priority', 'Normal')}
Department: {ticket_data.get('department', 'General Support')}

Issue: {ticket_data.get('issue')}
Description: {ticket_data.get('description', '')}

Our support team will review your ticket and get back to you shortly.

Best regards,
{settings.company.NAME} IT Support Team
"""

            msg = MIMEMultipart('alternative')
            msg['From'] = settings.email.SMTP_USERNAME
            msg['To'] = user_email
            msg['Subject'] = subject

            # Add plain text first, then HTML
            msg.attach(MIMEText(plain_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            with smtplib.SMTP(settings.email.SMTP_SERVER, settings.email.SMTP_PORT) as server:
                if settings.email.SMTP_USE_TLS:
                    server.starttls()

                server.login(settings.email.SMTP_USERNAME, settings.email.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Confirmation email sent for ticket {ticket_id} to {user_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed for user confirmation: {e}. Make sure to use Gmail App Password, not regular password.")
            return False
        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")
            return False
