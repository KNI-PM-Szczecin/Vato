import customtkinter as ctk
import re
from views.popup import PopupMessage
import api_test
from services.email_service import EmailService
import threading

class BasicView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # Configure grid layout for responsiveness
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- Card 1: Search ---
        self.search_card = ctk.CTkFrame(self, corner_radius=10)
        self.search_card.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.search_card.grid_columnconfigure(1, weight=1)

        self.search_title = ctk.CTkLabel(self.search_card, text="Pojedyncza Walidacja", font=ctk.CTkFont(size=16, weight="bold"))
        self.search_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        self.method_selector = ctk.CTkComboBox(self.search_card, values=["NIP", "REGON", "KRS"], width=120, state="readonly")
        self.method_selector.set("NIP")
        self.method_selector.grid(row=1, column=0, padx=(20, 10), pady=(0, 20), sticky="w")

        self.nip_input = ctk.CTkEntry(self.search_card, placeholder_text="Wprowadź identyfikator (np. NIP)...", height=32)
        self.nip_input.grid(row=1, column=1, padx=(0, 20), pady=(0, 20), sticky="ew")

        self.quick_validate_btn = ctk.CTkButton(
            self.search_card, text="Szybka walidacja", height=35, command=self.execute_quick_validation
        )
        self.quick_validate_btn.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")

        # --- Card 2: Reporting ---
        self.report_card = ctk.CTkFrame(self, corner_radius=10)
        self.report_card.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.report_card.grid_columnconfigure(0, weight=1)

        self.report_title = ctk.CTkLabel(self.report_card, text="Eksport i Powiadomienia", font=ctk.CTkFont(size=16, weight="bold"))
        self.report_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        self.email_input = ctk.CTkEntry(self.report_card, placeholder_text="Adres e-mail odbiorcy (opcjonalnie)", height=32)
        self.email_input.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")

        self.generate_report_btn = ctk.CTkButton(
            self.report_card, text="Generuj Raport i Wyślij", height=35, fg_color="#2E7D32", hover_color="#1B5E20",
            command=self.execute_report_generation
        )
        self.generate_report_btn.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")

        # --- Card 3: Results ---
        self.result_card = ctk.CTkFrame(self, corner_radius=10)
        self.result_card.grid(row=2, column=0, sticky="nsew")
        self.result_card.grid_columnconfigure(0, weight=1)
        self.result_card.grid_rowconfigure(1, weight=1)

        self.result_title = ctk.CTkLabel(self.result_card, text="Wyniki Analizy", font=ctk.CTkFont(size=16, weight="bold"))
        self.result_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))

        self.result_text = ctk.CTkTextbox(self.result_card, wrap="word", corner_radius=8)
        self.result_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.result_text.insert("0.0", "Czekam na dane...")
        self.result_text.configure(state="disabled")

    def append_result(self, text):
        self.result_text.configure(state="normal")
        self.result_text.delete("0.0", "end")
        self.result_text.insert("0.0", text)
        self.result_text.configure(state="disabled")

    def execute_quick_validation(self):
        nip = self.nip_input.get().strip()
        method = self.method_selector.get()
        
        if not nip:
            PopupMessage("Błąd", f"Proszę wpisać {method}.", status="error")
            return
            
        self.quick_validate_btn.configure(state="disabled", text="Przetwarzanie...")
        self.append_result(f"Trwa weryfikacja podmiotu dla: {nip}...\nProszę czekać.")

        # We use a thread to avoid blocking the GUI (responsivity fix)
        threading.Thread(target=self._async_validate, args=(nip, method), daemon=True).start()

    def _async_validate(self, nip, method):
        try:
            company_data = api_test.fetch_company_data(nip)
            result = api_test.evaluate_contractor(company_data)

            if result["total"] >= 20:
                recommendation = "Akceptacja (niskie ryzyko)."
                status_color = "success"
            elif result["total"] >= 0:
                recommendation = "Wymagana weryfikacja."
                status_color = "warning"
            else:
                recommendation = "Odrzucenie (wysokie ryzyko!)."
                status_color = "error"
                
            quick_report = f"Firma uzyskała {result['total']}/40 pkt.\nRekomendacja: {recommendation}"
            
            details = "\n".join([f"- {d}" for d in result["details"]])
            full_report = f"--- WYNIK DLA {method}: {nip} ---\n{quick_report}\n\nSzczegóły:\n{details}"
            
            self.after(0, lambda: self.append_result(full_report))
            self.after(0, lambda: PopupMessage(f"Walidacja zakończona", quick_report, status=status_color))
        except Exception as e:
            self.after(0, lambda: PopupMessage("Błąd API", f"Wystąpił błąd podczas walidacji: {str(e)}", status="error"))
            self.after(0, lambda: self.append_result(f"Błąd krytyczny: {str(e)}"))
        finally:
            self.after(0, lambda: self.quick_validate_btn.configure(state="normal", text="Szybka walidacja"))

    def is_email_valid(self, email):
        regex_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(regex_pattern, email) is not None

    def execute_report_generation(self):
        user_email = self.email_input.get().strip()
        if not self.is_email_valid(user_email):
            PopupMessage("Błąd walidacji", "Podano niepoprawny adres email.", status="error")
            return

        nip = self.nip_input.get().strip()
        if not nip:
            PopupMessage("Błąd", "Proszę wpisać identyfikator przed wygenerowaniem raportu.", status="error")
            return

        self.generate_report_btn.configure(state="disabled", text="Generowanie...")
        self.append_result(f"Generowanie raportu i wysyłanie na {user_email}...")
        
        threading.Thread(target=self._async_report, args=(nip, user_email), daemon=True).start()

    def _async_report(self, nip, user_email):
        try:
            company_data = api_test.fetch_company_data(nip)
            result = api_test.evaluate_contractor(company_data)

            email_mockup = f"RAPORT KYC DLA PODMIOTU: {nip}\n"
            email_mockup += f"Całkowity wynik: {result['total']} / 40\n"
            email_mockup += "-" * 40 + "\n"
            for detail in result["details"]:
                email_mockup += f"* {detail}\n"
            email_mockup += "-" * 40 + "\n"
            email_mockup += "Wiadomość wygenerowana automatycznie."
            
            email_service = EmailService()
            email_service.send_report(
                recipient_email=user_email,
                subject=f"Raport weryfikacji KYC - {nip}",
                html_content=email_mockup
            )
            
            self.after(0, lambda: PopupMessage("Sukces", f"Raport wygenerowany i wysłany na {user_email}.", status="success"))
            self.after(0, lambda: self.append_result(f"Raport pomyślnie wysłany na {user_email}.\n\n{email_mockup}"))
        except Exception as e:
            self.after(0, lambda: PopupMessage("Błąd wysyłki", f"Nie udało się wysłać raportu: {str(e)}", status="error"))
            self.after(0, lambda: self.append_result(f"Błąd wysyłki raportu: {str(e)}"))
        finally:
            self.after(0, lambda: self.generate_report_btn.configure(state="normal", text="Generuj Raport i Wyślij"))
