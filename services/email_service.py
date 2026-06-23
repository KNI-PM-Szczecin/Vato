import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

# Load environment variables from the .env file in the project root directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)


class EmailService:
    """
    Service for sending email reports via SMTP.
    """
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_username)
        self.recipient_email = os.getenv("SMTP_RECIPIENT")

    def send_report(
        self,
        recipient_email: str | None = None,
        subject: str = "Raport KYC",
        html_content: str = "",
        attachment_path: str | None = None,
        attachment_name: str | None = None,
    ) -> bool:
        """
        Sends an email report to the specified recipient, optionally with an attachment.
        Raises an exception if SMTP configuration is missing or if sending fails,
        so that the calling controller/view can capture and handle the error.
        """
        if not recipient_email:
            recipient_email = self.recipient_email

        if not recipient_email:
            raise ValueError("No recipient email specified and no default SMTP_RECIPIENT found in configuration.")

        if not self.smtp_host or not self.smtp_username or not self.smtp_password:
            raise ValueError("Missing SMTP configuration (SMTP_HOST, SMTP_USER, SMTP_PASSWORD) in .env.")

        try:
            msg = MIMEMultipart()
            msg["From"] = self.smtp_from
            msg["To"] = recipient_email
            msg["Subject"] = subject
            
            # Use 'html' subtype if content looks like HTML, otherwise fallback to 'plain'
            is_html = html_content.strip().startswith("<") or "<html>" in html_content
            msg.attach(MIMEText(html_content, "html" if is_html else "plain", "utf-8"))

            if attachment_path:
                att_name = attachment_name or os.path.basename(attachment_path)
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=att_name)
                    part["Content-Disposition"] = (
                        f'attachment; filename="{att_name}"'
                    )
                    msg.attach(part)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            print(f"Email sent successfully to {recipient_email}")
            return True

        except Exception as e:
            print(f"Failed to send email: {e}")
            raise e
