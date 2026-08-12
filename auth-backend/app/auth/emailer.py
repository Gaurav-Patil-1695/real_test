from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config.settings import settings


def _build_reset_link(raw_token: str) -> str:
    """Build the password-reset URL from APP_BASE_URL and the raw token."""
    base = settings.APP_BASE_URL.rstrip("/")
    return f"{base}/reset-password?token={raw_token}"


def _build_plain_text_body(reset_link: str) -> str:
    return (
        "You requested a password reset.\n\n"
        "Click the link below to reset your password:\n"
        f"{reset_link}\n\n"
        "This link will expire in "
        f"{settings.RESET_TOKEN_EXPIRE_MINUTES} minutes.\n\n"
        "If you did not request a password reset, you can safely ignore this email."
    )


def _build_html_body(reset_link: str) -> str:
    expire_minutes = settings.RESET_TOKEN_EXPIRE_MINUTES
    return (
        "<!DOCTYPE html>"
        "<html lang=\"en\">"
        "<head><meta charset=\"UTF-8\"></head>"
        "<body style=\"font-family:sans-serif;color:#111827;\">"
        "<p>You requested a password reset.</p>"
        "<p>Click the button below to reset your password:</p>"
        f"<p><a href=\"{reset_link}\" "
        "style=\"display:inline-block;padding:10px 20px;"
        "background-color:#4f46e5;color:#ffffff;"
        "text-decoration:none;border-radius:6px;\""
        ">Reset Password</a></p>"
        f"<p>This link will expire in {expire_minutes} minutes.</p>"
        "<p>If you did not request a password reset, you can safely ignore this email.</p>"
        "</body></html>"
    )


def send_password_reset_email(recipient_email: str, raw_token: str) -> None:
    """Send a password-reset email to *recipient_email* containing the reset link.

    The reset link is constructed as::

        {APP_BASE_URL}/reset-password?token={raw_token}

    The email is sent via SMTP using the SMTP_* settings from the application
    configuration.  Both a plain-text and an HTML alternative are included.

    Args:
        recipient_email: The email address of the user requesting the reset.
        raw_token:       The plaintext (un-hashed) reset token to embed in the link.
    """
    reset_link = _build_reset_link(raw_token)

    message = MIMEMultipart("alternative")
    message["Subject"] = "Reset your password"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = recipient_email

    plain_part = MIMEText(_build_plain_text_body(reset_link), "plain", "utf-8")
    html_part = MIMEText(_build_html_body(reset_link), "html", "utf-8")

    # Per RFC 2046 the last attached part is preferred by mail clients.
    message.attach(plain_part)
    message.attach(html_part)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_TLS:
            server.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(
            settings.SMTP_FROM_EMAIL,
            recipient_email,
            message.as_string(),
        )
