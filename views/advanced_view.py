import customtkinter as ctk
import re
from tkinter import filedialog
from views.popup import PopupMessage
import threading

class AdvancedView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # --- Card 1: Files ---
        self.files_card = ctk.CTkFrame(self, corner_radius=10)
        self.files_card.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.files_card.grid_columnconfigure(1, weight=1)

        self.files_title = ctk.CTkLabel(self.files_card, text="Konfiguracja Plików (Walidacja Wsadowa)", font=ctk.CTkFont(size=16, weight="bold"))
        self.files_title.grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 10))

        # Source
        self.load_label = ctk.CTkLabel(self.files_card, text="Plik źródłowy:")
        self.load_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=(0, 10))
        
        self.load_input = ctk.CTkEntry(self.files_card, placeholder_text="Ścieżka do pliku z listą podmiotów...", height=32)
        self.load_input.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))
        
        self.load_btn = ctk.CTkButton(self.files_card, text="Wybierz...", width=100, height=32, command=self.handle_file_load)
        self.load_btn.grid(row=1, column=2, sticky="e", padx=(0, 20), pady=(0, 10))

        # Destination
        self.save_label = ctk.CTkLabel(self.files_card, text="Plik docelowy:")
        self.save_label.grid(row=2, column=0, sticky="w", padx=(20, 10), pady=(0, 20))

        self.save_input = ctk.CTkEntry(self.files_card, placeholder_text="Miejsce zapisu (opcjonalnie)...", height=32)
        self.save_input.grid(row=2, column=1, sticky="ew", padx=(0, 10), pady=(0, 20))

        self.save_btn = ctk.CTkButton(self.files_card, text="Wybierz...", width=100, height=32, command=self.handle_file_save)
        self.save_btn.grid(row=2, column=2, sticky="e", padx=(0, 20), pady=(0, 20))

        # --- Card 2: Actions ---
        self.actions_card = ctk.CTkFrame(self, corner_radius=10)
        self.actions_card.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.actions_card.grid_columnconfigure(0, weight=1)

        self.actions_title = ctk.CTkLabel(self.actions_card, text="Eksport i Akcje", font=ctk.CTkFont(size=16, weight="bold"))
        self.actions_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        self.email_input = ctk.CTkEntry(self.actions_card, placeholder_text="Adres e-mail do wysyłki podsumowania", height=32)
        self.email_input.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))

        self.checkbox_frame = ctk.CTkFrame(self.actions_card, fg_color="transparent")
        self.checkbox_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 15))

        self.open_file_var = ctk.StringVar(value="off")
        self.open_file_checkbox = ctk.CTkCheckBox(self.checkbox_frame, text="Otwórz plik po zakończeniu", variable=self.open_file_var, onvalue="on", offvalue="off")
        self.open_file_checkbox.grid(row=0, column=0, sticky="w", padx=(0, 20))

        self.attach_orig_var = ctk.StringVar(value="off")
        self.attach_orig_checkbox = ctk.CTkCheckBox(self.checkbox_frame, text="Załącz oryginał do e-maila", variable=self.attach_orig_var, onvalue="on", offvalue="off")
        self.attach_orig_checkbox.grid(row=0, column=1, sticky="w")

        self.quick_validate_btn = ctk.CTkButton(
            self.actions_card, text="Waliduj i zapisz wyniki", height=35,
            command=self.execute_quick_validation
        )
        self.quick_validate_btn.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.generate_report_btn = ctk.CTkButton(
            self.actions_card, text="Waliduj, zapisz i wyślij E-mail", height=35, fg_color="#2E7D32", hover_color="#1B5E20",
            command=self.execute_report_generation
        )
        self.generate_report_btn.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 20))

        # --- Card 3: Status ---
        self.status_card = ctk.CTkFrame(self, corner_radius=10)
        self.status_card.grid(row=2, column=0, sticky="nsew")
        self.status_card.grid_columnconfigure(0, weight=1)
        self.status_card.grid_rowconfigure(1, weight=1)

        self.log_header_frame = ctk.CTkFrame(self.status_card, fg_color="transparent")
        self.log_header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        self.log_header_frame.grid_columnconfigure(0, weight=1)

        self.status_title = ctk.CTkLabel(self.log_header_frame, text="Dziennik Zdarzeń", font=ctk.CTkFont(size=16, weight="bold"))
        self.status_title.grid(row=0, column=0, sticky="w")

        self.copy_log_btn = ctk.CTkButton(self.log_header_frame, text="Kopiuj", width=80, height=28, command=self.copy_log)
        self.copy_log_btn.grid(row=0, column=1, sticky="e")

        self.log_text = ctk.CTkTextbox(self.status_card, wrap="word", corner_radius=8)
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.log_text.insert("0.0", "Oczekiwanie na wybór plików...")
        self.log_text.configure(state="disabled")

    def append_log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"\n{text}")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def copy_log(self):
        self.clipboard_clear()
        log_content = self.log_text.get("0.0", "end-1c")
        self.clipboard_append(log_content)
        PopupMessage("Skopiowano", "Zawartość dziennika została skopiowana do schowka.", status="success")

    def handle_file_load(self):
        selected_file = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if selected_file:
            self.load_input.delete(0, 'end')
            self.load_input.insert(0, selected_file)
            self.append_log(f"Załadowano plik źródłowy: {selected_file}")

    def handle_file_save(self):
        target_file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if target_file:
            self.save_input.delete(0, 'end')
            self.save_input.insert(0, target_file)
            self.append_log(f"Ustawiono plik docelowy na: {target_file}")

    def execute_quick_validation(self):
        src = self.load_input.get().strip()
        if not src:
            PopupMessage("Brak pliku", "Wybierz plik źródłowy.", status="warning")
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
            
        self.append_log("Rozpoczynanie walidacji wsadowej (działanie w tle)...")
        # Placeholder on thread
        threading.Thread(target=self._simulate_processing, args=(dest,), daemon=True).start()

    def _simulate_processing(self, dest_path=None):
        import os
        import platform
        import subprocess
        from utils.excel_export import read_nips_from_excel
        import api_test
        import openpyxl
        import shutil
        
        src_path = self.load_input.get().strip()
        if not src_path or not os.path.exists(src_path):
            self.after(0, lambda: PopupMessage("Błąd", "Plik źródłowy nie istnieje.", status="error"))
            return
            
        nips = read_nips_from_excel(src_path)
        if not nips:
            self.after(0, lambda: PopupMessage("Błąd", "Nie znaleziono poprawnych numerów NIP w pliku.", status="error"))
            self.after(0, lambda: self.append_log("Błąd: Brak numerów NIP."))
            return
            
        self.after(0, lambda: self.append_log(f"Znaleziono {len(nips)} NIP-ów. Rozpoczynam pobieranie danych..."))
        
        results_dict = {}
        for nip in nips:
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
                
                score = score_data['total_score']
                rec = score_data['risk_level']
                    
                score_text = f"{score}/60 - {rec}"
                results_dict[nip] = score_text
                self.after(0, lambda n=nip, s=score_text: self.append_log(f"Zbadano NIP {n}: {s}"))
            except Exception as e:
                results_dict[nip] = "Błąd API"
                self.after(0, lambda n=nip, err=str(e): self.append_log(f"Błąd NIP {n}: {err}"))
                
        # Zapis do pliku docelowego zachowując strukturę źródłową
        try:
            shutil.copy2(src_path, dest_path)
            wb = openpyxl.load_workbook(dest_path)
            sheet = wb.active
            
            # Wyszukiwanie nipu i wstawianie oceny
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
                    # Szukamy pierwszej wolnej po lewej stronie
                    for c in range(nip_cell.column - 1, 0, -1):
                        if sheet.cell(row=nip_cell.row, column=c).value is None:
                            target_col = c
                            break
                    
                    if target_col is None:
                        # Brak miejsca po lewej (lub kolumna A), dopisujemy na końcu arkusza
                        # Używamy initial_max_col by zapobiec efektowi "schodków"
                        target_col = initial_max_col + 1
                        
                    sheet.cell(row=nip_cell.row, column=target_col).value = results_dict[matched_nip]
                    
            wb.save(dest_path)
            
            def finish():
                PopupMessage("Informacja", "Weryfikacja zakończona pomyślnie. Wyniki zapisane.", status="success")
                self.append_log("Walidacja zakończona pomyślnie.")
                
                if self.open_file_var.get() == "on" and dest_path and os.path.exists(dest_path):
                    self.append_log(f"Otwieranie pliku: {dest_path}")
                    try:
                        if platform.system() == 'Windows':
                            os.startfile(dest_path)
                        elif platform.system() == 'Darwin':
                            subprocess.call(('open', dest_path))
                        else:
                            subprocess.call(('xdg-open', dest_path))
                    except Exception as e:
                        self.append_log(f"Błąd podczas otwierania pliku: {e}")

            self.after(0, finish)
        except Exception as e:
            self.after(0, lambda err=str(e): PopupMessage("Błąd", f"Błąd zapisu do pliku: {err}", status="error"))
            self.after(0, lambda err=str(e): self.append_log(f"Błąd zapisu: {err}"))

    def is_email_valid(self, email):
        regex_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(regex_pattern, email) is not None

    def execute_report_generation(self):
        user_email = self.email_input.get().strip()
        if not self.is_email_valid(user_email):
            PopupMessage("Błąd", "Podano niepoprawny adres email.", status="error")
            return

        src = self.load_input.get().strip()
        if not src:
            PopupMessage("Brak pliku", "Wybierz plik źródłowy.", status="warning")
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

        self.append_log(f"Walidacja wsadowa z raportem na adres: {user_email}...")
        threading.Thread(target=self._simulate_processing, args=(dest,), daemon=True).start()
