"""
Notification and Alerting Engine.
Sends operational alerts and daily summaries via Webhook (Discord, Slack, Telegram, or generic JSON)
and optional SMTP email. Fails gracefully without corrupting database states.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class NotificationSender:
    """Manages outbound alerts to keep administrators notified of daily executions."""

    def __init__(self):
        self.webhook_url = settings.NOTIFICATION_WEBHOOK_URL
        self.email_enabled = settings.NOTIFICATION_EMAIL_ENABLED

    def send_alert(self, title: str, message: str, level: str = "INFO", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Sends an alert through configured notification channels.
        Returns True if at least one delivery succeeded or notifications are not configured.
        """
        success = True
        logger.info(f"[{level}] Notification Alert: {title} - {message}")

        if self.webhook_url:
            ok = self._send_webhook(title, message, level, metadata)
            success = success and ok

        if self.email_enabled and settings.NOTIFICATION_EMAIL_RECIPIENT:
            ok = self._send_email(title, message, level)
            success = success and ok

        return success

    def _send_webhook(self, title: str, message: str, level: str, metadata: Optional[Dict[str, Any]]) -> bool:
        """Dispatches notification via HTTP Webhook (compatible with Slack, Discord, or custom)."""
        color = 0x244936  # Forest green
        if level == "WARNING":
            color = 0xB99A59  # Gold
        elif level == "ERROR":
            color = 0xC0392B  # Red

        # Payload formatted to support Discord/Slack style embeds and standard JSON
        payload = {
            "content": f"**[Daily Dhikr] {title}**\n{message}",
            "embeds": [
                {
                    "title": title,
                    "description": message,
                    "color": color,
                    "fields": [
                        {"name": k, "value": str(v), "inline": True}
                        for k, v in (metadata or {}).items()
                    ],
                    "footer": {"text": "Daily Dhikr Automation"}
                }
            ]
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(self.webhook_url, json=payload)
                resp.raise_for_status()
            logger.info("Webhook alert delivered successfully.")
            return True
        except Exception as e:
            logger.warning(f"Failed to deliver webhook alert: {e}")
            return False

    def _send_email(self, title: str, message: str, level: str) -> bool:
        """Dispatches alert via SMTP email."""
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_USER
            msg["To"] = settings.NOTIFICATION_EMAIL_RECIPIENT
            msg["Subject"] = f"[Daily Dhikr - {level}] {title}"

            body = f"""Daily Dhikr Automation Alert

Status: {level}
Title: {title}

Details:
{message}

--
Daily Dhikr Automated System
"""
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                server.starttls()
                if settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info("Email alert sent successfully.")
            return True
        except Exception as e:
            logger.warning(f"Failed to send email alert: {e}")
            return False


notifier = NotificationSender()
