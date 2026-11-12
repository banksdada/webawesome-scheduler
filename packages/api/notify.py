"""Email to technicians. If SMTP_* settings are missing, it only logs (and never crashes a request)."""

import logging
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

log = logging.getLogger("scheduler.notify")


def send_email(to: str, subject: str, body: str) -> bool:
    host = os.getenv("SMTP_HOST")
    if not host:
        log.info("Email not sent (SMTP_HOST not set): to=%s subject=%s", to, subject)
        return False
    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "scheduler@localhost"))
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        port = int(os.getenv("SMTP_PORT", "587"))
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            if os.getenv("SMTP_TLS", "1") == "1":
                smtp.starttls()
            if os.getenv("SMTP_USER"):
                smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
            smtp.send_message(msg)
        return True
    except Exception as err:  # never let a mail problem break scheduling
        log.warning("Email to %s failed: %s", to, err)
        return False


def _local_time(utc_naive: datetime | None) -> str:
    if utc_naive is None:
        return "not scheduled yet"
    tz = ZoneInfo(os.getenv("TIMEZONE", "Europe/London"))
    local = utc_naive.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
    return local.strftime("%A %d %B %Y, %H:%M")


def job_assigned(info: dict) -> None:
    """info is a plain dict built when the request was handled."""
    body = (
        f"Hi {info['tech_name']},\n\n"
        f"You have been assigned a job.\n\n"
        f"Job: {info['title']}\n"
        f"When: {_local_time(info['scheduled_start'])} ({info['duration_minutes']} minutes)\n"
        f"Customer: {info['customer_name']}\n"
        f"Address: {info.get('address') or 'not given'}\n"
        f"Phone: {info.get('customer_phone') or 'not given'}\n"
        f"Notes: {info.get('notes') or '-'}\n\n"
        f"Open the scheduler on your phone to start and complete the job."
    )
    send_email(info["tech_email"], f"New job: {info['title']}", body)
