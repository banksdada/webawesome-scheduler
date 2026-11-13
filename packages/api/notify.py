"""Email and text messages to technicians. Missing SMTP_* or TWILIO_* settings only log, and never crash a request."""

import base64
import logging
import os
import smtplib
import urllib.parse
import urllib.request
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


def normalise_phone(raw: str | None) -> str | None:
    """Turn a number like 07700 900111 into +447700900111 (the form Twilio needs)."""
    if not raw:
        return None
    number = "".join(ch for ch in raw if ch.isdigit() or ch == "+")
    if number.startswith("+"):
        digits = number[1:]
    elif number.startswith("00"):
        digits = number[2:]
    elif number.startswith("0"):
        digits = os.getenv("DEFAULT_COUNTRY_CODE", "44") + number[1:]
    else:
        digits = number
    digits = "".join(ch for ch in digits if ch.isdigit())
    return "+" + digits if 8 <= len(digits) <= 15 else None


def send_sms(to: str | None, body: str) -> bool:
    sid, token, sender = os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"), os.getenv("TWILIO_FROM")
    if not (sid and token and sender):
        log.info("Text not sent (TWILIO_* settings not set)")
        return False
    number = normalise_phone(to)
    if not number:
        log.info("Text not sent (technician has no usable phone number)")
        return False
    fields = {"To": number, "Body": body}
    fields["MessagingServiceSid" if sender.startswith("MG") else "From"] = sender
    request = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        data=urllib.parse.urlencode(fields).encode(),
        headers={"Authorization": "Basic " + base64.b64encode(f"{sid}:{token}".encode()).decode()},
    )
    try:
        with urllib.request.urlopen(request, timeout=15):
            return True
    except Exception as err:  # never let a text problem break scheduling
        log.warning("Text to %s failed: %s", number, err)
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
    site = os.getenv("SITE_URL", "").rstrip("/")
    text = f"New job: {info['title']}, {_local_time(info['scheduled_start'])}."
    if site:
        text += f" Open it: {site}/my-jobs"
    send_sms(info.get("tech_phone"), text)
