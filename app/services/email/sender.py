import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def send_email_with_attachment(subject: str, body: str, attachment_path: str = None, to_list: list = None):
    if to_list is None:
        to_list = settings.mail_to_list()
    if not to_list:
        logger.warning("No recipients configured")
        return False
    if settings.MAIL_DRY_RUN:
        logger.info(f"[DRY RUN] Would send email to {to_list}: subject='{subject}', attachment={attachment_path}")
        return True
    msg = MIMEMultipart()
    msg['From'] = settings.MAIL_FROM
    msg['To'] = ", ".join(to_list)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    if attachment_path and os.path.exists(attachment_path):
        part = MIMEBase('application', 'octet-stream')
        with open(attachment_path, 'rb') as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
        msg.attach(part)
    try:
        if settings.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        if settings.SMTP_USE_TLS and not settings.SMTP_USE_SSL:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.MAIL_FROM, to_list, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise


async def send_email(subject: str, body: str, to_list: list = None, attachment_path: str = None):
    return await send_email_with_attachment(subject, body, attachment_path, to_list)
