import base64
import os
import customtkinter as ctk
import re
import datetime
from views.popup import PopupMessage
import api_test
from services.email_service import EmailService
import threading
from services.i18n import t

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
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- Card 1: Search ---
        self.search_card = ctk.CTkFrame(self, corner_radius=10)
        self.search_card.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.search_card.grid_columnconfigure(1, weight=1)

        self.search_title = ctk.CTkLabel(self.search_card, text=t("basic.title"), font=ctk.CTkFont(size=16, weight="bold"))
        self.search_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))

        self.method_selector = ctk.CTkComboBox(self.search_card, values=["NIP", "REGON", "KRS"], width=120, state="readonly")
        self.method_selector.set("NIP")
        self.method_selector.grid(row=1, column=0, padx=(20, 10), pady=(0, 20), sticky="w")

        self.nip_input = ctk.CTkEntry(self.search_card, placeholder_text=t("basic.placeholder_nip"), height=32)
        self.nip_input.grid(row=1, column=1, padx=(0, 20), pady=(0, 20), sticky="ew")

        self.quick_validate_btn = ctk.CTkButton(
            self.search_card, text=t("basic.quick_validate"), height=35, command=self.execute_quick_validation
        )
        self.quick_validate_btn.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")

        # --- Card 2: Reporting ---
        self.report_card = ctk.CTkFrame(self, corner_radius=10)
        self.report_card.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.report_card.grid_columnconfigure(0, weight=1)

        self.report_title = ctk.CTkLabel(self.report_card, text=t("basic.report_title"), font=ctk.CTkFont(size=16, weight="bold"))
        self.report_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        self.email_input = ctk.CTkEntry(self.report_card, placeholder_text=t("basic.email_placeholder"), height=32)
        self.email_input.grid(row=1, column=0, padx=20, pady=(0, 2), sticky="ew")

        self.email_hint = ctk.CTkLabel(self.report_card, text=t("basic.email_hint"), font=ctk.CTkFont(size=11), text_color="gray")
        self.email_hint.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 15))

        self.generate_report_btn = ctk.CTkButton(
            self.report_card, text=t("basic.generate_report"), height=35, fg_color="#2E7D32", hover_color="#1B5E20",
            command=self.execute_report_generation
        )
        self.generate_report_btn.is_action_btn = True
        self.generate_report_btn.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")

        # --- Card 3: Results ---
        self.result_card = ctk.CTkFrame(self, corner_radius=10)
        self.result_card.grid(row=2, column=0, sticky="nsew")
        self.result_card.grid_columnconfigure(0, weight=1)
        self.result_card.grid_rowconfigure(1, weight=1)

        self.result_title = ctk.CTkLabel(self.result_card, text=t("basic.results_title"), font=ctk.CTkFont(size=16, weight="bold"))
        self.result_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))

        self.result_text = ctk.CTkTextbox(self.result_card, wrap="word", corner_radius=8)
        self.result_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.result_text.insert("0.0", t("basic.waiting_for_data"))
        self.result_text.configure(state="disabled")

    def update_texts(self):
        self.search_title.configure(text=t("basic.title"))
        self.nip_input.configure(placeholder_text=t("basic.placeholder_nip"))
        self.quick_validate_btn.configure(text=t("basic.quick_validate"))
        
        self.report_title.configure(text=t("basic.report_title"))
        self.email_input.configure(placeholder_text=t("basic.email_placeholder"))
        self.email_hint.configure(text=t("basic.email_hint"))
        self.generate_report_btn.configure(text=t("basic.generate_report"))
        
        self.result_title.configure(text=t("basic.results_title"))

    def append_result(self, text):
        self.result_text.configure(state="normal")
        self.result_text.delete("0.0", "end")
        self.result_text.insert("0.0", text)
        self.result_text.configure(state="disabled")

    def execute_quick_validation(self):
        nip = self.nip_input.get().strip()
        method = self.method_selector.get()
        
        if not nip:
            PopupMessage(t("popup.error"), t("basic.error_empty", method=method), status="error")
            return
            
        self.quick_validate_btn.configure(state="disabled", text=t("basic.processing"))
        self.append_result(t("basic.validating", nip=nip))

        threading.Thread(target=self._async_validate, args=(nip, method), daemon=True).start()

    def _async_validate(self, nip, method):
        try:
            import asyncio
            from services.verification_manager import verify_contractor
            
            cdata = asyncio.run(verify_contractor(nip))
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
                
            quick_report = t("basic.result_score", total=total, recommendation=recommendation)
            
            details = "\n".join([f"- {d}" for d in score_data["justifications"]])
            full_report = t("basic.result_details", method=method, nip=nip, report=quick_report, details=details)
            
            def _show_validate_result():
                self.append_result(full_report)
                self.update_idletasks()
                PopupMessage(t("popup.success"), quick_report, status=status_color)

            self.after(0, _show_validate_result)
        except Exception as e:
            captured = str(e)
            def _show_error():
                self.append_result(t("basic.critical_error", err=captured))
                self.update_idletasks()
                PopupMessage(t("popup.api_error"), t("basic.error_api", err=captured), status="error")
            self.after(0, _show_error)
        finally:
            self.after(0, lambda: self.quick_validate_btn.configure(state="normal", text=t("basic.quick_validate")))

    def get_parsed_emails(self, text):
        import re
        text = re.sub(r'[\n\r;,:]', ' ', text)
        return [e.strip() for e in text.split() if e.strip()]

    def is_email_valid(self, email):
        regex_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(regex_pattern, email) is not None

    def execute_report_generation(self):
        user_email_raw = self.email_input.get().strip()
        emails = self.get_parsed_emails(user_email_raw)
        
        if not emails:
            try:
                email_service = EmailService()
                default = email_service.recipient_email
                if default:
                    emails = self.get_parsed_emails(default)
            except Exception:
                pass

        if not emails:
            PopupMessage(t("popup.validation_error"), t("basic.email_error"), status="error")
            return
            
        for email in emails:
            if not self.is_email_valid(email):
                PopupMessage(t("popup.validation_error"), t("basic.invalid_email", email=email), status="error")
                return
                
        user_email = ", ".join(emails)

        nip = self.nip_input.get().strip()
        if not nip:
            PopupMessage(t("popup.error"), t("basic.empty_id"), status="error")
            return

        self.generate_report_btn.configure(state="disabled", text=t("basic.generating"))
        self.append_result(t("basic.generating_log", email=user_email))
        
        threading.Thread(target=self._async_report, args=(nip, user_email), daemon=True).start()

    def _async_report(self, nip, user_email):
        try:
            import asyncio
            from services.verification_manager import verify_contractor

            cdata = asyncio.run(verify_contractor(nip))
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

            current_year = datetime.date.today().year
            report_date = datetime.datetime.now().strftime('%d.%m.%Y')
            report_time = datetime.datetime.now().strftime('%H:%M')
            company_name = cdata.legal_name
            company_display = company_name.title() if company_name != "---" else "—"

            results_rows_html = ""
            for i, cat in enumerate(score_data["categories"]):
                score_val = cat["score"]
                cat_name = cat["category_name"]
                status = cat["status"]
                
                # Assign colors based on points
                if score_val > 0:
                    s_color, s_bg, s_str = "#1e7e34", "#e6f4ea", f"+{score_val}"
                elif score_val < 0:
                    s_color, s_bg, s_str = "#c0392b", "#fdecea", str(score_val)
                else:
                    s_color, s_bg, s_str = "#666", "#f5f5f5", "0"
                    
                row_bg = "#f9fafc" if i % 2 == 0 else "#ffffff"
                results_rows_html += (
                    f'<tr style="background:{row_bg};">'
                    f'<td style="padding:12px 14px;border-bottom:1px solid #eef0f4;width:250px;">'
                    f'<p style="margin:0;font-size:13px;font-weight:700;color:#1e3c72;">{cat_name}</p></td>'
                    f'<td style="padding:12px 14px;font-size:13px;color:#444;border-bottom:1px solid #eef0f4;line-height:1.45;">Status: {status}</td>'
                    f'<td style="padding:12px 14px;text-align:center;border-bottom:1px solid #eef0f4;white-space:nowrap;">'
                    f'<span style="background:{s_bg};color:{s_color};padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;">{s_str} pkt</span></td>'
                    f'</tr>'
                )

            details_items = ""
            for detail in score_data["justifications"]:
                details_items += f'<li style="padding:10px 12px;border-bottom:1px solid #f0f2f5;font-size:14px;line-height:1.5;">{detail}</li>'

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
  <title>{t("email.report_title")} — {nip}</title>
</head>
<body style="margin:0;padding:0;background:#eef1f6;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;color:#2c2c3a;">
  <div style="max-width:600px;margin:28px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 6px 24px rgba(0,0,0,0.09);border:1px solid #dde1ea;">

    <!-- LOGO -->
    <div style="padding:24px 24px 16px;text-align:center;background:#fff;border-bottom:1px solid #eaecf0;">
      {logo_img}
      <p style="margin:10px 0 4px;font-size:10px;color:#bbb;letter-spacing:2px;text-transform:uppercase;font-weight:600;">{t("email.report_title")}</p>
      <p style="margin:0;font-size:11px;color:#ccc;">{t("email.nip", nip=nip)}</p>
    </div>

    <div style="padding:22px 26px 20px;">
      <!-- WYNIK SCORINGOWY -->
      <div style="display:table;width:100%;padding:16px 20px;background:{bg_color};border-radius:10px;border:1px solid {border_color};margin-bottom:22px;box-sizing:border-box;">
        <div style="display:table-cell;text-align:center;padding-right:18px;border-right:1px solid {border_color};width:90px;vertical-align:middle;">
          <p style="margin:0;font-size:36px;font-weight:800;color:{text_color};line-height:1;">{total_score}</p>
          <p style="margin:3px 0 0;font-size:10px;color:#aaa;letter-spacing:1px;text-transform:uppercase;">/ 100 pkt</p>
        </div>
        <div style="display:table-cell;padding-left:18px;vertical-align:middle;">
          <p style="margin:0;font-size:15px;font-weight:700;color:{text_color};">{recommendation}</p>
          <p style="margin:5px 0 2px;font-size:14px;font-weight:600;color:#333;">{company_display}</p>
          <p style="margin:0;font-size:11px;color:#aaa;">NIP:&nbsp;{nip}&nbsp;&nbsp;·&nbsp;&nbsp;{report_date}</p>
        </div>
      </div>

      <!-- WYNIKI WERYFIKACJI -->
      <p style="font-size:11px;font-weight:700;color:#1e3c72;text-transform:uppercase;letter-spacing:1.2px;border-bottom:2px solid #e8eaf0;padding-bottom:7px;margin:0 0 10px;">{t("email.details_title")}</p>
      <table style="width:100%;border-collapse:collapse;border:1px solid #e8eaf0;margin-bottom:20px;">
        <thead>
          <tr style="background:#1e3c72;color:#fff;">
            <th style="padding:9px 13px;text-align:left;font-size:12px;font-weight:600;width:250px;">Kategoria</th>
            <th style="padding:9px 13px;text-align:left;font-size:12px;font-weight:600;">Opis</th>
            <th style="padding:9px 13px;text-align:center;font-size:12px;font-weight:600;width:80px;">Wynik</th>
          </tr>
        </thead>
        <tbody>{results_rows_html}</tbody>
      </table>

      <ul style="list-style:none;padding:0;margin:0 0 25px 0;">
        {details_items}
      </ul>

    </div>

    <!-- FOOTER -->
    <div style="background:#f5f7fb;padding:14px 20px;text-align:center;font-size:10px;color:#bbb;border-top:1px solid #e8eaf0;letter-spacing:0.3px;">
      {t("email.footer")} &nbsp;·&nbsp; &copy; {current_year}
    </div>

  </div>
</body>
</html>
"""

            import tempfile
            from utils.pdf_export import export_results_pdf

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdf_path = tmp.name

            try:
                export_results_pdf([cdata], pdf_path)
                
                email_service = EmailService()
                email_service.send_report(
                    recipient_email=user_email,
                    subject=t("email.subject", nip=nip),
                    html_content=html_message,
                    attachment_path=pdf_path,
                    attachment_name="raport.pdf"
                )
            finally:
                try:
                    import os
                    os.unlink(pdf_path)
                except Exception:
                    pass
            
            quick_report = t("basic.result_score", total=total_score, recommendation=recommendation)
            details = " ".join([f"- {d}" for d in score_data["justifications"]])
            gui_text = t("basic.result_details", method="NIP", nip=nip, report=quick_report, details=details)

            def _show_report_result():
                self.append_result(t("basic.report_sent", email=user_email, text=gui_text))
                self.update_idletasks()
                PopupMessage(t("popup.success"), t("basic.report_sent", email=user_email, text=""), status=status_color)

            self.after(0, _show_report_result)
        except Exception as e:
            captured = str(e)
            def _show_report_error():
                self.append_result(t("basic.email_send_error", err=captured))
                self.update_idletasks()
                PopupMessage(t("popup.send_error"), t("basic.email_send_error", err=captured), status="error")
            self.after(0, _show_report_error)
        finally:
            def _enable_btn():
                self.generate_report_btn.configure(state="normal", text=t("basic.generate_report"))
                self.update_idletasks()
            self.after(0, _enable_btn)
