import asyncio
import customtkinter as ctk
import re
from tkinter import filedialog
from views.popup import PopupMessage
import threading
from services.i18n import t
from utils.excel_export import export_results
import os

class AdvancedView(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # --- Card 1: Files ---
        self.files_card = ctk.CTkFrame(self, corner_radius=10)
        self.files_card.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.files_card.grid_columnconfigure(1, weight=1)

        self.files_title = ctk.CTkLabel(self.files_card, text=t("advanced.title"), font=ctk.CTkFont(size=16, weight="bold"))
        self.files_title.grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 10))

        # Source
        self.load_label = ctk.CTkLabel(self.files_card, text=t("advanced.source_file"))
        self.load_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=(0, 10))
        
        self.load_input = ctk.CTkEntry(self.files_card, placeholder_text=t("advanced.source_placeholder"), height=32)
        self.load_input.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))
        
        self.load_btn = ctk.CTkButton(self.files_card, text=t("advanced.choose_btn"), width=100, height=32, command=self.handle_file_load)
        self.load_btn.grid(row=1, column=2, sticky="e", padx=(0, 20), pady=(0, 10))

        # Destination
        self.save_label = ctk.CTkLabel(self.files_card, text=t("advanced.dest_file"))
        self.save_label.grid(row=2, column=0, sticky="w", padx=(20, 10), pady=(0, 20))

        self.save_input = ctk.CTkEntry(self.files_card, placeholder_text=t("advanced.dest_placeholder"), height=32)
        self.save_input.grid(row=2, column=1, sticky="ew", padx=(0, 10), pady=(0, 20))

        self.save_btn = ctk.CTkButton(self.files_card, text=t("advanced.choose_btn"), width=100, height=32, command=self.handle_file_save)
        self.save_btn.grid(row=2, column=2, sticky="e", padx=(0, 20), pady=(0, 15))

        from views.api_options import ApiOptionsFrame
        
        self.api_toggle_btn = ctk.CTkButton(self.files_card, text=t("basic.api_options") if hasattr(t, '__call__') else "Opcje API (rozwiń)", fg_color="transparent", text_color=("blue", "lightblue"), hover_color=("gray80", "gray30"), command=self.toggle_api_options)
        self.api_toggle_btn.grid(row=3, column=0, columnspan=3, sticky="w", padx=15, pady=(0, 5))
        
        self.api_options_frame = ApiOptionsFrame(self.files_card)
        self.api_options_visible = False

        # --- Card 2: Actions ---
        self.actions_card = ctk.CTkFrame(self, corner_radius=10)
        self.actions_card.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.actions_card.grid_columnconfigure(0, weight=1)

        self.actions_title = ctk.CTkLabel(self.actions_card, text=t("advanced.actions_title"), font=ctk.CTkFont(size=16, weight="bold"))
        self.actions_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        self.email_input = ctk.CTkEntry(self.actions_card, placeholder_text=t("advanced.email_placeholder"), height=32)
        self.email_input.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 2))

        self.email_hint = ctk.CTkLabel(self.actions_card, text=t("advanced.email_hint"), font=ctk.CTkFont(size=11), text_color="gray")
        self.email_hint.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 15))

        self.checkbox_frame = ctk.CTkFrame(self.actions_card, fg_color="transparent")
        self.checkbox_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))

        self.open_file_var = ctk.StringVar(value="off")
        self.open_file_checkbox = ctk.CTkCheckBox(self.checkbox_frame, text=t("advanced.open_file"), variable=self.open_file_var, onvalue="on", offvalue="off")
        self.open_file_checkbox.grid(row=0, column=0, sticky="w", padx=(0, 15))

        self.attach_orig_var = ctk.StringVar(value="off")
        self.attach_orig_checkbox = ctk.CTkCheckBox(self.checkbox_frame, text=t("advanced.attach_orig"), variable=self.attach_orig_var, onvalue="on", offvalue="off")
        self.attach_orig_checkbox.grid(row=0, column=1, sticky="w", padx=(0, 15))

        self.mock_mode_var = ctk.StringVar(value="off")
        self.mock_mode_checkbox = ctk.CTkCheckBox(
            self.checkbox_frame, text=t("advanced.mock_mode"),
            variable=self.mock_mode_var, onvalue="on", offvalue="off",
            text_color=("#E65100", "#FFA040"),
        )
        self.mock_mode_checkbox.grid(row=0, column=2, sticky="w")

        self.quick_validate_btn = ctk.CTkButton(
            self.actions_card, text=t("advanced.validate_save"), height=35,
            command=self.execute_quick_validation
        )
        self.quick_validate_btn.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.generate_report_btn = ctk.CTkButton(
            self.actions_card, text=t("advanced.validate_save_send"), height=35,
            command=self.execute_report_generation
        )
        self.generate_report_btn.is_action_btn = True
        self.generate_report_btn.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 20))

        # --- Card 3: Status ---
        self.status_card = ctk.CTkFrame(self, corner_radius=10)
        self.status_card.grid(row=2, column=0, sticky="nsew")
        self.status_card.grid_columnconfigure(0, weight=1)
        self.status_card.grid_rowconfigure(1, weight=1)

        self.log_header_frame = ctk.CTkFrame(self.status_card, fg_color="transparent")
        self.log_header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        self.log_header_frame.grid_columnconfigure(0, weight=1)

        self.status_title = ctk.CTkLabel(self.log_header_frame, text=t("advanced.log_title"), font=ctk.CTkFont(size=16, weight="bold"))
        self.status_title.grid(row=0, column=0, sticky="w")

        self.copy_log_btn = ctk.CTkButton(self.log_header_frame, text=t("advanced.copy_btn"), width=80, height=28, command=self.copy_log)
        self.copy_log_btn.grid(row=0, column=1, sticky="e")

        self.log_text = ctk.CTkTextbox(self.status_card, wrap="word", corner_radius=8, height=150)
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.log_text.insert("0.0", t("advanced.waiting"))
        self.log_text.configure(state="disabled")

    def update_texts(self):
        self.files_title.configure(text=t("advanced.title"))
        self.load_label.configure(text=t("advanced.source_file"))
        self.load_input.configure(placeholder_text=t("advanced.source_placeholder"))
        self.load_btn.configure(text=t("advanced.choose_btn"))
        self.save_label.configure(text=t("advanced.dest_file"))
        self.save_input.configure(placeholder_text=t("advanced.dest_placeholder"))
        self.save_btn.configure(text=t("advanced.choose_btn"))
        
        self.actions_title.configure(text=t("advanced.actions_title"))
        self.email_input.configure(placeholder_text=t("advanced.email_placeholder"))
        self.email_hint.configure(text=t("advanced.email_hint"))
        self.open_file_checkbox.configure(text=t("advanced.open_file"))
        self.attach_orig_checkbox.configure(text=t("advanced.attach_orig"))
        self.mock_mode_checkbox.configure(text=t("advanced.mock_mode"))
        self.quick_validate_btn.configure(text=t("advanced.validate_save"))
        self.generate_report_btn.configure(text=t("advanced.validate_save_send"))
        
        self.status_title.configure(text=t("advanced.log_title"))
        self.copy_log_btn.configure(text=t("advanced.copy_btn"))
        if hasattr(self, 'api_toggle_btn'):
            btn_text = t("basic.api_options_hide") if self.api_options_visible else t("basic.api_options")
            self.api_toggle_btn.configure(text=btn_text)
        if hasattr(self, 'api_options_frame'):
            self.api_options_frame.update_texts()

    def toggle_api_options(self):
        if self.api_options_visible:
            self.api_options_frame.grid_remove()
            self.api_toggle_btn.configure(text=t("basic.api_options") if hasattr(t, '__call__') else "Opcje API (rozwiń)")
            self.api_options_visible = False
        else:
            self.api_options_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=20, pady=(0, 15))
            self.api_toggle_btn.configure(text=t("basic.api_options_hide") if hasattr(t, '__call__') else "Opcje API (zwiń)")
            self.api_options_visible = True

    def append_log(self, text):
        import datetime
        now = datetime.datetime.now().strftime("[%d-%m-%Y %H:%M]")
        self.log_text.configure(state="normal")
        if self.log_text.get("0.0", "end").strip() == t("advanced.waiting"):
            self.log_text.delete("0.0", "end")
        self.log_text.insert("end", f"\n{now} {text}")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def copy_log(self):
        self.clipboard_clear()
        log_content = self.log_text.get("0.0", "end-1c")
        self.clipboard_append(log_content)
        PopupMessage(t("popup.copied_title"), t("advanced.copied"), status="success")

    def handle_file_load(self):
        selected_file = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if selected_file:
            self.load_input.delete(0, 'end')
            self.load_input.insert(0, selected_file)
            self.append_log(t("advanced.loaded_source", file=selected_file))

    def handle_file_save(self):
        target_file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if target_file:
            self.save_input.delete(0, 'end')
            self.save_input.insert(0, target_file)
            self.append_log(t("advanced.set_dest", file=target_file))

    def execute_quick_validation(self):
        src = self.load_input.get().strip()
        if not src:
            PopupMessage(t("popup.warning"), t("advanced.no_source"), status="warning")
            return
            
        from elevenlabs_integration.tts import stop_tts
        stop_tts()
            
        dest = self.save_input.get().strip()
        import os
        import datetime
        if not dest or os.path.abspath(dest) == os.path.abspath(src):
            base, ext = os.path.splitext(src)
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            dest = f"{base}_vato-{timestamp}{ext}"
            self.save_input.delete(0, 'end')
            self.save_input.insert(0, dest)
            
        self.append_log(t("advanced.starting"))
        mock = self.mock_mode_var.get() == "on"
        if mock:
            self.append_log(t("advanced.mock_mode_active"))

        from services.history_manager import HistoryManager
        import os
        HistoryManager().add_entry("BATCH", src)
        
        api_config = self.api_options_frame.get_config()
        threading.Thread(target=self._simulate_processing, args=(dest, mock, None, api_config), daemon=True).start()

    def _simulate_processing(self, dest_path=None, mock_mode=False, user_email=None, api_config=None):
        import os
        import platform
        import subprocess
        import asyncio
        from utils.excel_export import read_nips_from_excel

        import openpyxl
        import shutil
        
        src_path = self.load_input.get().strip()
        if not src_path or not os.path.exists(src_path):
            self.after(0, lambda: PopupMessage(t("popup.error"), t("advanced.source_not_found"), status="error"))
            return

        nips = read_nips_from_excel(src_path)
        if not nips:
            self.after(0, lambda: PopupMessage(t("popup.error"), t("advanced.no_nips"), status="error"))
            self.after(0, lambda: self.append_log(t("advanced.no_nips")))
            return

        self.after(0, lambda: self.append_log(t("advanced.found_nips", count=len(nips))))

        from services.verification_manager import verify_contractor

        cdata_list = []
        for nip in nips:
            try:
                if mock_mode:
                    import datetime
                    from models.contractor import ContractorData
                    from scoring.scorer import enrich as _enrich
                    cdata = ContractorData(
                        nip=nip,
                        legal_name=f"Firma testowa {nip}",
                        country_code="PL",
                        status_prawny="AKTYWNA",
                        status_vat="Czynny",
                        rachunek_na_bialej_liscie=True,
                        share_capital=100000.0,
                        has_bailiff_proceedings=False,
                        on_sanctions_list=False,
                        data_rozpoczecia=datetime.date(2015, 1, 1),
                    )
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        cdata = loop.run_until_complete(_enrich(cdata))
                    finally:
                        loop.close()
                else:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        cdata = loop.run_until_complete(verify_contractor(nip, api_config=api_config))
                    finally:
                        loop.close()

                cdata_list.append(cdata)
                score_data = cdata.scoring if cdata.scoring else {}
                score = score_data.get('total_score', 0)
                rec = score_data.get('risk_level', 'NIEZNANY')
                score_text = f"{score}/100 - {rec}"
                self.after(0, lambda n=nip, s=score_text: self.append_log(t("advanced.checked_nip", nip=n, score=s)))
            except Exception as e:
                self.after(0, lambda n=nip, err=str(e): self.append_log(t("advanced.nip_error", nip=n, err=err)))

        if not cdata_list:
            self.after(0, lambda: PopupMessage(t("popup.error"), t("advanced.api_error"), status="error"))
            return

        try:
            export_results(cdata_list, dest_path)
        except Exception as e:
            self.after(0, lambda err=str(e): PopupMessage(t("popup.error"), t("advanced.write_error", err=err), status="error"))
            self.after(0, lambda err=str(e): self.append_log(t("advanced.write_error", err=err)))
            return

        # Send email if requested
        email_error = None
        if user_email:
            try:
                from services.email_service import EmailService
                html_body = self._build_batch_email_html(cdata_list)
                EmailService().send_report(
                    recipient_email=user_email,
                    subject=f"Vato — raport wsadowy ({len(cdata_list)} podmiotow)",
                    html_content=html_body,
                    attachment_path=dest_path,
                    attachment_name=os.path.basename(dest_path),
                )
                self.after(0, lambda: self.append_log(t("advanced.report_sent")))
            except Exception as e:
                email_error = str(e)
                self.after(0, lambda err=email_error: self.append_log(f"Blad wysylki email: {err}"))

        def finish():
            PopupMessage(t("popup.info"), t("advanced.success"), status="success")
            self.append_log(t("advanced.success"))
            if email_error:
                PopupMessage(t("popup.error"), f"Email nie zostal wyslany:\n{email_error}", status="error")

            app = self.winfo_toplevel()
            if hasattr(app, 'is_muted') and not getattr(app, 'is_muted', True):
                from elevenlabs_integration.tts import play_text
                play_text(t("app.report_generated"))

            if self.open_file_var.get() == "on" and dest_path and os.path.exists(dest_path):
                self.append_log(t("advanced.opening_file", file=dest_path))
                try:
                    if platform.system() == 'Windows':
                        os.startfile(dest_path)
                    elif platform.system() == 'Darwin':
                        subprocess.call(('open', dest_path))
                    else:
                        subprocess.call(('xdg-open', dest_path))
                except Exception as e:
                    self.append_log(t("advanced.open_error", err=str(e)))

        self.after(0, finish)

    def _build_batch_email_html(self, cdata_list: list) -> str:
        COLOR_PRIMARY = "#1A365D"
        COLOR_SECONDARY = "#2B6CB0"
        COLOR_GREEN = "#1E7E34"
        COLOR_YELLOW = "#E65100"
        COLOR_RED = "#C62828"
        COLOR_BG = "#F7FAFC"

        rows_html = ""
        for c in cdata_list:
            scoring = getattr(c, "scoring", {}) or {}
            score = scoring.get("total_score", "?")
            rec = scoring.get("risk_level", "NIEZNANY")
            color_code = scoring.get("color_code", "yellow")
            justifications = scoring.get("justifications", [])
            name = getattr(c, "legal_name", c.nip) or c.nip
            nip = getattr(c, "nip", "")

            score_color = {"green": COLOR_GREEN, "red": COLOR_RED}.get(color_code, COLOR_YELLOW)
            just_html = "".join(
                f'<tr><td style="padding:3px 8px;color:#4A5568;font-size:12px;">&#9656; {j}</td></tr>'
                for j in justifications
            ) if justifications else ""

            rows_html += f"""
            <tr style="border-bottom:1px solid #E2E8F0;">
              <td style="padding:10px 12px;font-weight:600;color:{COLOR_PRIMARY};">{name}</td>
              <td style="padding:10px 12px;color:#4A5568;">{nip}</td>
              <td style="padding:10px 12px;font-weight:700;color:{score_color};text-align:center;">{score}/100</td>
              <td style="padding:10px 12px;font-weight:600;color:{score_color};">{rec}</td>
            </tr>
            {"<tr><td colspan='4' style='padding:0 12px 10px 24px;background:#FAFAFA;'><table style='width:100%;border-collapse:collapse;'>" + just_html + "</table></td></tr>" if just_html else ""}
            """

        return f"""
        <html><body style="font-family:Arial,sans-serif;background:#F0F4F8;margin:0;padding:20px;">
        <div style="max-width:700px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
          <div style="background:{COLOR_PRIMARY};padding:24px 28px;">
            <h1 style="color:#fff;margin:0;font-size:20px;">Vato — Raport Wsadowy</h1>
            <p style="color:#90CDF4;margin:6px 0 0;font-size:13px;">Zweryfikowano {len(cdata_list)} podmiot(ow) | Plik Excel w zalaczeniu</p>
          </div>
          <div style="padding:24px 28px;">
            <table style="width:100%;border-collapse:collapse;">
              <thead>
                <tr style="background:{COLOR_SECONDARY};">
                  <th style="padding:10px 12px;color:#fff;text-align:left;font-size:13px;">Nazwa podmiotu</th>
                  <th style="padding:10px 12px;color:#fff;text-align:left;font-size:13px;">NIP</th>
                  <th style="padding:10px 12px;color:#fff;text-align:center;font-size:13px;">Wynik</th>
                  <th style="padding:10px 12px;color:#fff;text-align:left;font-size:13px;">Rekomendacja</th>
                </tr>
              </thead>
              <tbody style="background:{COLOR_BG};">
                {rows_html}
              </tbody>
            </table>
          </div>
          <div style="background:{COLOR_BG};padding:14px 28px;text-align:center;">
            <p style="color:#718096;font-size:11px;margin:0;">Wiadomosc wygenerowana automatycznie przez aplikacje Vato.</p>
          </div>
        </div>
        </body></html>
        """

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
            PopupMessage(t("popup.error"), t("advanced.no_emails"), status="error")
            return
            
        for email in emails:
            if not self.is_email_valid(email):
                PopupMessage(t("popup.error"), t("advanced.invalid_email_format", email=email), status="error")
                return
                
        user_email = ", ".join(emails)

        src = self.load_input.get().strip()
        if not src:
            PopupMessage(t("popup.warning"), t("advanced.no_source"), status="warning")
            return

        dest = self.save_input.get().strip()
        import os
        import datetime
        if not dest or os.path.abspath(dest) == os.path.abspath(src):
            base, ext = os.path.splitext(src)
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            dest = f"{base}_vato-{timestamp}{ext}"
            self.save_input.delete(0, 'end')
            self.save_input.insert(0, dest)

        self.append_log(t("advanced.sending_to", email=user_email))
        mock = self.mock_mode_var.get() == "on"
        if mock:
            self.append_log(t("advanced.mock_mode_active"))

        from services.history_manager import HistoryManager
        import os
        HistoryManager().add_entry("BATCH", os.path.basename(src))

        api_config = self.api_options_frame.get_config()
        threading.Thread(target=self._simulate_processing, args=(dest, mock, user_email, api_config), daemon=True).start()
