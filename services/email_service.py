class EmailService:
    def __init__(self):
        # Docelowo tutaj można skonfigurować SMTP, np. smtplib.SMTP_SSL()
        # lub połączyć się z zewnętrznym API do maili np. SendGrid / Resend.
        pass

    def send_report(self, recipient_email: str, subject: str, html_content: str, attachment_path: str = None):
        """
        Symuluje wysyłanie e-maila z ładnym formatowaniem HTML, CSS i ewentualnymi załącznikami.
        Na tym etapie tylko wypisuje w konsoli informacje o wysyłce.
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
