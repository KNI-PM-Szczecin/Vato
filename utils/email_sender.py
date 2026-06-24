"""
Sends report as email attachment via SMTP.
Required .env keys: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
"""
import os
import smtplib
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from models.contractor import ScoreResult


def send_report(
    recipient: str,
    subject: str,
    results: list[ScoreResult],
    fmt: str = "Excel",
) -> None:
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    if not smtp_host or not smtp_user:
        raise ValueError("Missing SMTP configuration in .env (SMTP_HOST, SMTP_USER, SMTP_PASSWORD).")

    # Generate attachment in temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{'xlsx' if fmt == 'Excel' else 'pdf'}") as tmp:
        tmp_path = tmp.name

    try:
        if fmt == "Excel":
            from utils.excel_export import export_results
            export_results(results, tmp_path)
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "contractor_report.xlsx"
        else:
            from utils.pdf_export import export_results_pdf
            export_results_pdf(results, tmp_path)
            mime_type = "application/pdf"
            filename = "contractor_report.pdf"

        # Build email
        msg = MIMEMultipart()
        msg["From"] = smtp_from
        msg["To"] = recipient
        msg["Subject"] = subject

        nip_list = ", ".join(r.nip for r in results)
        body = f"Please find attached the contractor verification report ({nip_list}).\n\nVato — Contractor Verification Tool"
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with open(tmp_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, recipient, msg.as_string())
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
