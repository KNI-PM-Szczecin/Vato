import base64
import os
import customtkinter as ctk
import re
from views.popup import PopupMessage
import api_test
from services.email_service import EmailService
import threading

_LOGO_B64 = ""
_LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "vato_black.png")
try:
    with open(_LOGO_PATH, "rb") as _f:
        _LOGO_B64 = base64.b64encode(_f.read()).decode("ascii")
except OSError:
    pass

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
            
            def _show_validate_result():
                self.append_result(full_report)
                self.update_idletasks()
                PopupMessage("Walidacja zakończona", quick_report, status=status_color)

            self.after(0, _show_validate_result)
        except Exception as e:
            captured = str(e)
            def _show_error():
                self.append_result(f"Błąd krytyczny: {captured}")
                self.update_idletasks()
                PopupMessage("Błąd API", f"Wystąpił błąd podczas walidacji: {captured}", status="error")
            self.after(0, _show_error)
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
            import datetime
            company_name = api_test.fetch_company_name(nip)
            company_data = api_test.fetch_company_data(nip)
            result = api_test.evaluate_contractor(company_data)

            # Określenie rekomendacji i kolorów raportu na podstawie punktacji
            total_score = result["total"]
            if total_score >= 20:
                recommendation = "Akceptacja (niskie ryzyko)"
                bg_color = "#e8f5e9"
                border_color = "#c8e6c9"
                text_color = "#2e7d32"
                status_color = "success"
            elif total_score >= 0:
                recommendation = "Wymagana dodatkowa weryfikacja"
                bg_color = "#fff3e0"
                border_color = "#ffe0b2"
                text_color = "#e65100"
                status_color = "warning"
            else:
                recommendation = "Odrzucenie (wysokie ryzyko!)"
                bg_color = "#ffebee"
                border_color = "#ffcdd2"
                text_color = "#c62828"
                status_color = "error"

            current_year = datetime.date.today().year

            # Tytuł firmy — title case dla czytelności (API zwraca CAPS)
            company_display = company_name.title() if company_name != "---" else "—"

            # Tabela kryteriów z image.png — dynamiczne zaznaczenie "5 lat działalności"
            years_in_biz = result.get("2_experience", 0)

            def criterion_badge(met: bool | None) -> str:
                if met is None:
                    return '<span style="background:#f0f0f0;color:#aaa;padding:3px 10px;border-radius:20px;font-size:11px;">brak danych</span>'
                if met:
                    return '<span style="background:#e6f4ea;color:#1e7e34;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">&#10003; Spełnione</span>'
                return '<span style="background:#fdecea;color:#c0392b;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">&#10007; Niespełnione</span>'

            criteria_rows = [
                ("Ma więcej niż 100 sprawnych pojazdów", "+10 pkt", None),
                ("Mniej niż 15% floty jest w serwisie", "−5 pkt", None),
                ("Kapitał zakładowy przynajmniej 20% obrotów", "+5 pkt", None),
                ("Brak komornika na głowie", "+5 pkt", None),
                ("5 lat działalności", "+10 pkt", years_in_biz == 10),
                ("10 lat działalności", "0 pkt", None),
            ]
            criteria_html = ""
            for i, (lbl, pts, met) in enumerate(criteria_rows):
                row_bg = "#f9fafc" if i % 2 == 0 else "#ffffff"
                criteria_html += (
                    f'<tr style="background:{row_bg};">'
                    f'<td style="padding:10px 14px;font-size:13px;color:#333;border-bottom:1px solid #eef0f4;">{lbl}</td>'
                    f'<td style="padding:10px 14px;font-size:12px;font-weight:700;color:#555;text-align:center;border-bottom:1px solid #eef0f4;white-space:nowrap;">{pts}</td>'
                    f'<td style="padding:10px 14px;text-align:center;border-bottom:1px solid #eef0f4;">{criterion_badge(met)}</td>'
                    f'</tr>'
                )

            # Tabela wyników weryfikacji — zastępuje terminal, czytelna dla nietech. użytkowników
            category_map = [
                ("1_legal_status", "Status prawny",   "Rejestracja i aktywność gospodarcza"),
                ("2_experience",   "Doświadczenie",   "Staż firmy na rynku"),
                ("3_vat_taxes",    "Podatki / VAT",   "Status VAT i Biała Lista MF"),
                ("4_stability",    "Stabilność",      "Zmiany zarządu i adresu siedziby"),
            ]
            import re as _re
            results_rows_html = ""
            for i, (key, cat_name, cat_desc) in enumerate(category_map):
                score_val = result.get(key, 0)
                detail_str = result["details"][i] if i < len(result["details"]) else ""
                desc = _re.sub(r'^[^:]+:\s*', '', detail_str).rstrip(".")

                if score_val > 0:
                    s_color, s_bg, s_str = "#1e7e34", "#e6f4ea", f"+{score_val}"
                elif score_val < 0:
                    s_color, s_bg, s_str = "#c0392b", "#fdecea", str(score_val)
                else:
                    s_color, s_bg, s_str = "#666", "#f5f5f5", "0"

                row_bg = "#f9fafc" if i % 2 == 0 else "#ffffff"
                results_rows_html += (
                    f'<tr style="background:{row_bg};">'
                    f'<td style="padding:12px 14px;border-bottom:1px solid #eef0f4;width:130px;">'
                    f'  <p style="margin:0;font-size:13px;font-weight:700;color:#1e3c72;">{cat_name}</p>'
                    f'  <p style="margin:2px 0 0;font-size:11px;color:#aaa;">{cat_desc}</p>'
                    f'</td>'
                    f'<td style="padding:12px 14px;font-size:13px;color:#444;border-bottom:1px solid #eef0f4;line-height:1.45;">{desc}</td>'
                    f'<td style="padding:12px 14px;text-align:center;border-bottom:1px solid #eef0f4;white-space:nowrap;">'
                    f'  <span style="background:{s_bg};color:{s_color};padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;">{s_str} pkt</span>'
                    f'</td>'
                    f'</tr>'
                )

            logo_img = (
                f'<img src="data:image/png;base64,{_LOGO_B64}" alt="Vato" '
                f'style="max-width:160px;height:auto;display:block;margin:0 auto;">'
                if _LOGO_B64 else
                '<p style="font-size:22px;font-weight:700;text-align:center;color:#111;">VATO</p>'
            )

            html_message = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Raport weryfikacji KYC — {nip}</title>
</head>
<body style="margin:0;padding:0;background:#eef1f6;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;color:#2c2c3a;">

  <div style="max-width:600px;margin:28px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 6px 24px rgba(0,0,0,0.09);border:1px solid #dde1ea;">

    <!-- LOGO -->
    <div style="padding:24px 24px 16px;text-align:center;background:#fff;border-bottom:1px solid #eaecf0;">
      {logo_img}
      <p style="margin:10px 0 4px;font-size:10px;color:#bbb;letter-spacing:2px;text-transform:uppercase;font-weight:600;">Raport Weryfikacji Kontrahenta</p>
      <p style="margin:0;font-size:11px;color:#ccc;">Wygenerowany {datetime.datetime.now().strftime('%d.%m.%Y')} o {datetime.datetime.now().strftime('%H:%M')} przez Vato KYC Tool</p>
    </div>

    <div style="padding:22px 26px 20px;">

      <!-- WYNIK SCORINGOWY -->
      <div style="display:table;width:100%;padding:16px 20px;background:{bg_color};border-radius:10px;border:1px solid {border_color};margin-bottom:22px;box-sizing:border-box;">
        <div style="display:table-cell;text-align:center;padding-right:18px;border-right:1px solid {border_color};width:90px;vertical-align:middle;">
          <p style="margin:0;font-size:36px;font-weight:800;color:{text_color};line-height:1;">{total_score}</p>
          <p style="margin:3px 0 0;font-size:10px;color:#aaa;letter-spacing:1px;text-transform:uppercase;">/ 40 pkt</p>
        </div>
        <div style="display:table-cell;padding-left:18px;vertical-align:middle;">
          <p style="margin:0;font-size:15px;font-weight:700;color:{text_color};">{recommendation}</p>
          <p style="margin:5px 0 2px;font-size:14px;font-weight:600;color:#333;">{company_display}</p>
          <p style="margin:0;font-size:11px;color:#aaa;">NIP:&nbsp;{nip}&nbsp;&nbsp;·&nbsp;&nbsp;{datetime.date.today().strftime('%d.%m.%Y')}</p>
        </div>
      </div>

      <!-- TABELA KRYTERIÓW OCENY -->
      <p style="font-size:11px;font-weight:700;color:#1e3c72;text-transform:uppercase;letter-spacing:1.2px;border-bottom:2px solid #e8eaf0;padding-bottom:7px;margin:0 0 10px;">Kryteria oceny</p>
      <table style="width:100%;border-collapse:collapse;margin-bottom:4px;border-radius:8px;overflow:hidden;border:1px solid #e8eaf0;">
        <thead>
          <tr style="background:#1e3c72;color:#fff;">
            <th style="padding:9px 13px;text-align:left;font-size:12px;font-weight:600;">Kryterium</th>
            <th style="padding:9px 13px;text-align:center;font-size:12px;font-weight:600;width:60px;">Pkt</th>
            <th style="padding:9px 13px;text-align:center;font-size:12px;font-weight:600;width:130px;">Status</th>
          </tr>
        </thead>
        <tbody>{criteria_html}</tbody>
      </table>
      <p style="font-size:10px;color:#ccc;margin:4px 0 22px;">* Kryteria "brak danych" wymagają weryfikacji z zewnętrznych źródeł (dane flotowe, kapitałowe).</p>

      <!-- WYNIKI WERYFIKACJI — czytelna tabelka dla nietech. użytkowników -->
      <p style="font-size:11px;font-weight:700;color:#1e3c72;text-transform:uppercase;letter-spacing:1.2px;border-bottom:2px solid #e8eaf0;padding-bottom:7px;margin:0 0 10px;">Wyniki weryfikacji</p>
      <table style="width:100%;border-collapse:collapse;border:1px solid #e8eaf0;border-radius:8px;overflow:hidden;">
        <thead>
          <tr style="background:#1e3c72;color:#fff;">
            <th style="padding:9px 13px;text-align:left;font-size:12px;font-weight:600;width:130px;">Obszar</th>
            <th style="padding:9px 13px;text-align:left;font-size:12px;font-weight:600;">Opis</th>
            <th style="padding:9px 13px;text-align:center;font-size:12px;font-weight:600;width:80px;">Wynik</th>
          </tr>
        </thead>
        <tbody>{results_rows_html}</tbody>
      </table>

    </div>

    <!-- FOOTER -->
    <div style="background:#f5f7fb;padding:14px 20px;text-align:center;font-size:10px;color:#bbb;border-top:1px solid #e8eaf0;letter-spacing:0.3px;">
      Wygenerowano automatycznie przez <strong style="color:#999;">Vato KYC Tool</strong> &nbsp;·&nbsp; &copy; {current_year}
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
            gui_text = f"--- WYNIK DLA NIP: {nip} ---\nFirma uzyskała {total_score}/40 pkt.\nRekomendacja: {recommendation}\n\nSzczegóły:\n"
            gui_text += "\n".join([f"- {d}" for d in result["details"]])

            success_msg = f"Raport pomyślnie wysłany na {user_email}.\n\n{gui_text}"
            popup_msg = f"Raport wygenerowany i wysłany na {user_email}."

            def _show_report_result():
                self.append_result(success_msg)
                self.update_idletasks()
                PopupMessage("Sukces", popup_msg, status=status_color)

            self.after(0, _show_report_result)
        except Exception as e:
            captured = str(e)
            def _show_report_error():
                self.append_result(f"Błąd wysyłki raportu: {captured}")
                self.update_idletasks()
                PopupMessage("Błąd wysyłki", f"Nie udało się wysłać raportu: {captured}", status="error")
            self.after(0, _show_report_error)
        finally:
            self.after(0, lambda: self.generate_report_btn.configure(state="normal", text="Generuj Raport i Wyślij"))
