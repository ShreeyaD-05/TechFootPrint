"""
Email service — nodemailer-style SMTP sender using Python's smtplib.
Configure via environment variables (see shared/config.py).
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from shared.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Send transactional emails via SMTP."""

    @staticmethod
    def _build_message(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        return msg

    @staticmethod
    def send(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """Send an email. Returns True on success, False on failure."""
        if not settings.EMAIL_ENABLED:
            logger.info("[Email disabled] Would send '%s' to %s", subject, to_email)
            return True  # Silently succeed in dev mode

        if not settings.SMTP_USER or not settings.SMTP_FROM_EMAIL:
            logger.warning("SMTP credentials not configured — skipping email to %s", to_email)
            return False

        try:
            msg = EmailService._build_message(to_email, subject, html_body, text_body)
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
            logger.info("Email sent to %s: %s", to_email, subject)
            return True
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to_email, exc)
            return False

    # ── Template helpers ──────────────────────────────────────────────────────

    @staticmethod
    def send_welcome_faculty(
        to_email: str,
        full_name: str,
        username: str,
        temp_password: str,
        college_name: str,
        login_url: str = "http://localhost:5173/login",
    ) -> bool:
        subject = f"Welcome to CodeTrack — Your Faculty Account"
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px;border:1px solid #e5e7eb;border-radius:8px;">
          <h2 style="color:#4f46e5;">Welcome to CodeTrack, {full_name}!</h2>
          <p>Your faculty account has been created for <strong>{college_name}</strong>.</p>
          <p>Here are your login credentials:</p>
          <table style="background:#f9fafb;padding:16px;border-radius:6px;width:100%;">
            <tr><td style="padding:4px 0;color:#6b7280;">Username</td><td><strong>{username}</strong></td></tr>
            <tr><td style="padding:4px 0;color:#6b7280;">Temporary Password</td><td><strong>{temp_password}</strong></td></tr>
          </table>
          <p style="margin-top:16px;">Please log in and change your password immediately.</p>
          <a href="{login_url}" style="display:inline-block;margin-top:8px;padding:10px 20px;background:#4f46e5;color:#fff;border-radius:6px;text-decoration:none;">
            Login to CodeTrack
          </a>
          <p style="margin-top:24px;font-size:12px;color:#9ca3af;">
            If you did not expect this email, please contact your college administrator.
          </p>
        </div>
        """
        text = (
            f"Welcome to CodeTrack, {full_name}!\n\n"
            f"College: {college_name}\n"
            f"Username: {username}\n"
            f"Temporary Password: {temp_password}\n\n"
            f"Login at: {login_url}\n"
            f"Please change your password after first login."
        )
        return EmailService.send(to_email, subject, html, text)

    @staticmethod
    def send_welcome_student(
        to_email: str,
        full_name: str,
        username: str,
        temp_password: str,
        college_name: str,
        faculty_name: str,
        login_url: str = "http://localhost:5173/login",
    ) -> bool:
        subject = "Welcome to CodeTrack — Your Student Account"
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px;border:1px solid #e5e7eb;border-radius:8px;">
          <h2 style="color:#4f46e5;">Welcome to CodeTrack, {full_name}!</h2>
          <p>Your student account has been created by <strong>{faculty_name}</strong> at <strong>{college_name}</strong>.</p>
          <p>Here are your login credentials:</p>
          <table style="background:#f9fafb;padding:16px;border-radius:6px;width:100%;">
            <tr><td style="padding:4px 0;color:#6b7280;">Username</td><td><strong>{username}</strong></td></tr>
            <tr><td style="padding:4px 0;color:#6b7280;">Temporary Password</td><td><strong>{temp_password}</strong></td></tr>
          </table>
          <p style="margin-top:16px;">Please log in and change your password immediately.</p>
          <a href="{login_url}" style="display:inline-block;margin-top:8px;padding:10px 20px;background:#4f46e5;color:#fff;border-radius:6px;text-decoration:none;">
            Login to CodeTrack
          </a>
          <p style="margin-top:24px;font-size:12px;color:#9ca3af;">
            If you did not expect this email, please contact your faculty or college administrator.
          </p>
        </div>
        """
        text = (
            f"Welcome to CodeTrack, {full_name}!\n\n"
            f"College: {college_name}\n"
            f"Created by: {faculty_name}\n"
            f"Username: {username}\n"
            f"Temporary Password: {temp_password}\n\n"
            f"Login at: {login_url}\n"
            f"Please change your password after first login."
        )
        return EmailService.send(to_email, subject, html, text)

    @staticmethod
    def send_password_reset(
        to_email: str,
        full_name: str,
        new_password: str,
        login_url: str = "http://localhost:5173/login",
    ) -> bool:
        subject = "CodeTrack — Your Password Has Been Reset"
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px;border:1px solid #e5e7eb;border-radius:8px;">
          <h2 style="color:#4f46e5;">Password Reset</h2>
          <p>Hi {full_name}, your CodeTrack password has been reset by an administrator.</p>
          <table style="background:#f9fafb;padding:16px;border-radius:6px;width:100%;">
            <tr><td style="padding:4px 0;color:#6b7280;">New Temporary Password</td><td><strong>{new_password}</strong></td></tr>
          </table>
          <p style="margin-top:16px;">Please log in and change your password immediately.</p>
          <a href="{login_url}" style="display:inline-block;margin-top:8px;padding:10px 20px;background:#4f46e5;color:#fff;border-radius:6px;text-decoration:none;">
            Login to CodeTrack
          </a>
        </div>
        """
        text = (
            f"Hi {full_name},\n\n"
            f"Your CodeTrack password has been reset.\n"
            f"New Temporary Password: {new_password}\n\n"
            f"Login at: {login_url}\n"
            f"Please change your password after first login."
        )
        return EmailService.send(to_email, subject, html, text)
