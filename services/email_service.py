class EmailService:
    def __init__(self):
        # Ideally SMTP can be configured here, e.g. smtplib.SMTP_SSL()
        # or connect to an external email API e.g. SendGrid / Resend.
        pass

    def send_report(self, recipient_email: str, subject: str, html_content: str, attachment_path: str = None):
        """
        Simulates sending an email with nice HTML formatting, CSS, and potential attachments.
        At this stage it only prints the sending info to the console.
        """
        print("\n" + "="*60)
        print(">>> ROZPOCZĘCIE SYMULACJI WYSYŁKI E-MAILA <<<")
        print("="*60)
        print(f"Odbiorca:  {recipient_email}")
        print(f"Temat:     {subject}")
        if attachment_path:
            print(f"Załącznik: {attachment_path}")
        else:
            print("Załącznik: BRAK")
        print("-" * 60)
        print("Treść e-maila (mockup):")
        print(html_content)
        print("="*60)
        print(">>> WYSYŁKA ZAKOŃCZONA SUKCESEM <<<")
        print("="*60 + "\n")
