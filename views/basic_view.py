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
            import asyncio
            from models.contractor import ContractorData
            from scoring.scorer import enrich
            import datetime
            
            company_dict = api_test.fetch_company_data(nip)
            cdata = ContractorData(
                nip=company_dict["nip"],
                status_prawny=company_dict.get("legal_status", "NIEZNANY"),
                data_rozpoczecia=datetime.date.fromisoformat(company_dict["start_date"]) if company_dict.get("start_date") else None,
                status_vat=company_dict.get("vat_status", "NIEZNANY"),
                rachunek_na_bialej_liscie=company_dict.get("account_on_whitelist", False),
                share_capital=100000,
                has_bailiff_proceedings=False
            )
            
            cdata = asyncio.run(enrich(cdata))
            score_data = cdata.scoring
            
            total = score_data['total_score']
            recommendation = score_data['risk_level']
            color = score_data['color_code']

            if color == "green":
                status_color = "success"
            elif color == "yellow":
                status_color = "warning"
            else:
                status_color = "error"
                
            quick_report = f"Firma uzyskała {total}/60 pkt.\nRekomendacja: {recommendation}"
            
            details = "\n".join([f"- {d}" for d in score_data["justifications"]])
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
        if not user_email:
            try:
                email_service = EmailService()
                user_email = email_service.recipient_email
            except Exception:
                user_email = None

        if not user_email or not self.is_email_valid(user_email):
            PopupMessage("Błąd walidacji", "Podano niepoprawny adres email lub brak domyślnego odbiorcy.", status="error")
            return

        nip = self.nip_input.get().strip()
        if not nip:
            PopupMessage("Błąd", "Proszę wpisać identyfikator przed wygenerowaniem raportu.", status="error")
            return

        self.generate_report_btn.configure(state="disabled", text="Generowanie...")
        self.append_result(f"Generowanie raportu i wysyłanie na {user_email}...")
        
        threading.Thread(target=self._async_report, args=(nip, user_email), daemon=True).start()

    def _async_report(self, nip, user_email):
        """
        Pobiera dane podmiotu dla podanego NIP-u, ocenia jego wiarygodność,
        a następnie generuje i wysyła raport w formacie HTML na podany adres e-mail.
        Wszystkie operacje są wykonywane asynchronicznie w tle.
        """
        try:
            import asyncio
            from models.contractor import ContractorData
            from scoring.scorer import enrich
            import datetime
            
            company_dict = api_test.fetch_company_data(nip)
            cdata = ContractorData(
                nip=company_dict["nip"],
                status_prawny=company_dict.get("legal_status", "NIEZNANY"),
                data_rozpoczecia=datetime.date.fromisoformat(company_dict["start_date"]) if company_dict.get("start_date") else None,
                status_vat=company_dict.get("vat_status", "NIEZNANY"),
                rachunek_na_bialej_liscie=company_dict.get("account_on_whitelist", False),
                share_capital=100000,
                has_bailiff_proceedings=False
            )
            cdata = asyncio.run(enrich(cdata))
            score_data = cdata.scoring

            total_score = score_data['total_score']
            recommendation = score_data['risk_level']
            color = score_data['color_code']
            
            if color == "green":
                bg_color = "#e8f5e9"
                border_color = "#c8e6c9"
                text_color = "#2e7d32"
                status_color = "success"
            elif color == "yellow":
                bg_color = "#fff3e0"
                border_color = "#ffe0b2"
                text_color = "#e65100"
                status_color = "warning"
            else:
                bg_color = "#ffebee"
                border_color = "#ffcdd2"
                text_color = "#c62828"
                status_color = "error"

            # Budowanie listy szczegółów oceny w formacie HTML
            details_items = ""
            for detail in score_data["justifications"]:
                details_items += f"<li>{detail}</li>"

            current_year = datetime.date.today().year

            # Szablon wiadomości e-mail w formacie HTML w języku polskim
            html_message = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Raport weryfikacji KYC - {nip}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f6f9;
            color: #333333;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            border: 1px solid #e1e4e8;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #ffffff;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 700;
        }}
        .header p {{
            margin: 5px 0 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px 25px;
        }}
        .score-box {{
            text-align: center;
            padding: 20px;
            background-color: {bg_color};
            border-radius: 6px;
            margin-bottom: 25px;
            border: 1px solid {border_color};
        }}
        .score-val {{
            font-size: 36px;
            font-weight: 700;
            color: {text_color};
            margin: 0;
        }}
        .score-label {{
            font-size: 14px;
            color: #666666;
            margin: 5px 0 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .score-recommendation {{
            font-size: 16px;
            font-weight: 600;
            color: {text_color};
            margin: 10px 0 0;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            border-bottom: 2px solid #e1e4e8;
            padding-bottom: 8px;
            margin-bottom: 15px;
            color: #1e3c72;
        }}
        .details-list {{
            list-style: none;
            padding: 0;
            margin: 0 0 25px 0;
        }}
        .details-list li {{
            padding: 10px 12px;
            border-bottom: 1px solid #f0f2f5;
            font-size: 14px;
            line-height: 1.5;
        }}
        .details-list li:last-child {{
            border-bottom: none;
        }}
        .footer {{
            background-color: #f8fafc;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #888888;
            border-top: 1px solid #e1e4e8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Raport Weryfikacji KYC</h1>
            <p>Identyfikator NIP: {nip}</p>
        </div>
        <div class="content">
            <div class="score-box">
                <p class="score-val">{total_score} / 60</p>
                <p class="score-label">Ocena Kontrahenta</p>
                <p class="score-recommendation">Rekomendacja: {recommendation}</p>
            </div>
            
            <div class="section-title">Szczegóły oceny</div>
            <ul class="details-list">
                {details_items}
            </ul>
        </div>
        <div class="footer">
            Wiadomość wygenerowana automatycznie przez aplikację Vato.<br>
            &copy; {current_year} Vato KYC Tool
        </div>
    </div>
</body>
</html>
"""
            
            email_service = EmailService()
            email_service.send_report(
                recipient_email=user_email,
                subject=f"Raport weryfikacji KYC - {nip}",
                html_content=html_message
            )
            
            # Tekstowy mockup raportu do wyświetlenia w oknie wyników GUI
            gui_text = f"--- WYNIK DLA NIP: {nip} ---\nFirma uzyskała {total_score}/60 pkt.\nRekomendacja: {recommendation}\n\nSzczegóły:\n"
            gui_text += "\n".join([f"- {d}" for d in score_data["justifications"]])

            self.after(0, lambda: PopupMessage("Sukces", f"Raport wygenerowany i wysłany na {user_email}.", status=status_color))
            self.after(0, lambda: self.append_result(f"Raport pomyślnie wysłany na {user_email}.\n\n{gui_text}"))
        except Exception as e:
            self.after(0, lambda: PopupMessage("Błąd wysyłki", f"Nie udało się wysłać raportu: {str(e)}", status="error"))
            self.after(0, lambda: self.append_result(f"Błąd wysyłki raportu: {str(e)}"))
        finally:
            self.after(0, lambda: self.generate_report_btn.configure(state="normal", text="Generuj Raport i Wyślij"))
