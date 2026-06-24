import asyncio
import customtkinter as ctk
import re
from tkinter import filedialog
from views.popup import PopupMessage
import threading
from services.i18n import t

class AdvancedView(ctk.CTkFrame):
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
        self.save_btn.grid(row=2, column=2, sticky="e", padx=(0, 20), pady=(0, 20))

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
        self.open_file_checkbox.grid(row=0, column=0, sticky="w", padx=(0, 20))

        self.attach_orig_var = ctk.StringVar(value="off")
        self.attach_orig_checkbox = ctk.CTkCheckBox(self.checkbox_frame, text=t("advanced.attach_orig"), variable=self.attach_orig_var, onvalue="on", offvalue="off")
        self.attach_orig_checkbox.grid(row=0, column=1, sticky="w")

        self.mock_mode_var = ctk.StringVar(value="off")
        self.mock_mode_checkbox = ctk.CTkCheckBox(
            self.checkbox_frame, text=t("advanced.mock_mode"),
            variable=self.mock_mode_var, onvalue="on", offvalue="off",
            text_color=("#E65100", "#FFA040"),
        )
        self.mock_mode_checkbox.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.quick_validate_btn = ctk.CTkButton(
            self.actions_card, text=t("advanced.validate_save"), height=35,
            command=self.execute_quick_validation
        )
        self.quick_validate_btn.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.generate_report_btn = ctk.CTkButton(
            self.actions_card, text=t("advanced.validate_save_send"), height=35, fg_color="#2E7D32", hover_color="#1B5E20",
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

        self.log_text = ctk.CTkTextbox(self.status_card, wrap="word", corner_radius=8, height=500)
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
        HistoryManager().add_entry("BATCH", os.path.basename(src))

        threading.Thread(target=self._simulate_processing, args=(dest, mock), daemon=True).start()

    def _simulate_processing(self, dest_path=None, mock_mode=False):
        import os
        import platform
        import subprocess
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

        results_dict = {}
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
                        cdata = loop.run_until_complete(verify_contractor(nip))
                    finally:
                        loop.close()

                score_data = cdata.scoring
                score = score_data['total_score']
                rec = score_data['risk_level']
                score_text = f"{score}/100 - {rec}"
                results_dict[nip] = score_text
                self.after(0, lambda n=nip, s=score_text: self.append_log(t("advanced.checked_nip", nip=n, score=s)))
            except Exception as e:
                results_dict[nip] = t("advanced.api_error")
                self.after(0, lambda n=nip, err=str(e): self.append_log(t("advanced.nip_error", nip=n, err=err)))
                
        try:
            shutil.copy2(src_path, dest_path)
            wb = openpyxl.load_workbook(dest_path)
            sheet = wb.active
            
            initial_max_col = sheet.max_column
            
            for row in sheet.iter_rows():
                nip_cell = None
                matched_nip = None
                for cell in row:
                    val = str(cell.value).replace(" ", "").replace("-", "") if cell.value else ""
                    if val.endswith(".0"): val = val[:-2]
                    if val in results_dict:
                        nip_cell = cell
                        matched_nip = val
                        break
                        
                if nip_cell:
                    target_col = None
                    for c in range(nip_cell.column - 1, 0, -1):
                        if sheet.cell(row=nip_cell.row, column=c).value is None:
                            target_col = c
                            break
                    
                    if target_col is None:
                        target_col = initial_max_col + 1
                        
                    sheet.cell(row=nip_cell.row, column=target_col).value = results_dict[matched_nip]
                    
            wb.save(dest_path)
            
            def finish():
                PopupMessage(t("popup.info"), t("advanced.success"), status="success")
                self.append_log(t("advanced.success"))
                
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
        except Exception as e:
            self.after(0, lambda err=str(e): PopupMessage(t("popup.error"), t("advanced.write_error", err=err), status="error"))
            self.after(0, lambda err=str(e): self.append_log(t("advanced.write_error", err=err)))

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

        threading.Thread(target=self._simulate_processing, args=(dest, mock), daemon=True).start()
