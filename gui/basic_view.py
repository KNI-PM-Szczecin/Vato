import customtkinter as ctk
import re
import api_test
from email_service import EmailService
from gui.popup import PopupMessage


class BasicView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.nip_container = ctk.CTkFrame(self, fg_color="transparent")
        self.nip_container.pack(pady=20)

        self.nip_input = ctk.CTkEntry(self.nip_container, placeholder_text="NIP", width=200)
        self.nip_input.pack(side="left", padx=10)

        self.search_methods = ["NIP", "REGON", "KRS"]
        self.method_selector = ctk.CTkComboBox(self.nip_container, values=self.search_methods, width=100, state="readonly")
        self.method_selector.set("NIP")
        self.method_selector.pack(side="left", padx=10)

        self.quick_validate_btn = ctk.CTkButton(self, text="Szybka walidacja podmiotu", width=320,
                                                command=self.execute_quick_validation)
        self.quick_validate_btn.pack(pady=10)

        self.email_input = ctk.CTkEntry(self, placeholder_text="user@example.com", width=320)
        self.email_input.pack(pady=20)

        self.generate_report_btn = ctk.CTkButton(self, text="Wygeneruj raport i prześlij email", width=320,
                                                 command=self.execute_report_generation)
        self.generate_report_btn.pack(pady=10)

    def execute_quick_validation(self):
        nip = self.nip_input.get().strip()
        method = self.method_selector.get()
        
        if not nip:
            PopupMessage("Błąd", f"Proszę wpisać {method}.", status="error")
            return
            
        print(f"[BASIC] Szybka walidacja podmiotu dla: {nip} za pomoca: {method}")
        
        company_data = api_test.fetch_company_data(nip)
        result = api_test.evaluate_contractor(company_data)

        if result["total"] >= 20:
            rekomendacja = "Akceptacja (niskie ryzyko)."
            status_kolor = "success"
        elif result["total"] >= 0:
            rekomendacja = "Wymagana weryfikacja."
            status_kolor = "warning"
        else:
            rekomendacja = "Odrzucenie (wysokie ryzyko!)."
            status_kolor = "error"
            
        raport_szybki = f"Firma uzyskała {result['total']}/40 pkt. Rekomendacja: {rekomendacja}"
            
        PopupMessage(f"Szybka walidacja: {nip}", raport_szybki, status=status_kolor)

    def is_email_valid(self, email):
        regex_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(regex_pattern, email) is not None

    def execute_report_generation(self):
        user_email = self.email_input.get().strip()
        if not self.is_email_valid(user_email):
            print("[BASIC] Blad: Podano nieprawidlowy adres email.")
            PopupMessage("Błąd walidacji", "Podano niepoprawny adres email.", status="error")
            return

        nip = self.nip_input.get().strip()
        if not nip:
            PopupMessage("Błąd", "Proszę wpisać identyfikator przed wygenerowaniem raportu.", status="error")
            return

        print(f"[BASIC] Generowanie raportu dla NIP: {nip}")

        company_data = api_test.fetch_company_data(nip)
        result = api_test.evaluate_contractor(company_data)

        email_mockup = f"RAPORT KYC DLA PODMIOTU: {nip}\n"
        email_mockup += f"Całkowity wynik: {result['total']} / 40\n"
        email_mockup += "-" * 40 + "\n"
        for detail in result["szczegoly"]:
            email_mockup += f"* {detail}\n"
        email_mockup += "-" * 40 + "\n"
        email_mockup += "Wiadomość wygenerowana automatycznie."

        email_service = EmailService()
        email_service.send_raport(
            recipient_email=user_email,
            subject=f"Raport weryfikacji KYC - {nip}",
            html_content=email_mockup
        )
        
        PopupMessage("Sukces", f"Raport testowy wygenerowany i 'wysłany' na {user_email} (sprawdź konsolę).", status="success")