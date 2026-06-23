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
        self.load_label = ctk.CTkLabel(self.files_card, text="Plik źródłowy (.xlsx):")
        self.load_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=(0, 10))
        
        self.load_input = ctk.CTkEntry(self.files_card, placeholder_text="Ścieżka do pliku z listą podmiotów...", height=32)
        self.load_input.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 10))
        
        self.load_btn = ctk.CTkButton(self.files_card, text="Wybierz...", width=100, height=32, command=self.handle_file_load)
        self.load_btn.grid(row=1, column=2, sticky="e", padx=(0, 20), pady=(0, 10))

        # Destination
        self.save_label = ctk.CTkLabel(self.files_card, text="Plik docelowy (.xlsx):")
        self.save_label.grid(row=2, column=0, sticky="w", padx=(20, 10), pady=(0, 20))

        self.save_input = ctk.CTkEntry(self.files_card, placeholder_text="Miejsce zapisu raportu...", height=32)
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

        self.quick_validate_btn = ctk.CTkButton(
            self.actions_card, text="Waliduj i zapisz wyniki", height=35,
            command=self.execute_quick_validation
        )
        self.quick_validate_btn.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.generate_report_btn = ctk.CTkButton(
            self.actions_card, text="Waliduj, zapisz i wyślij E-mail", height=35, fg_color="#2E7D32", hover_color="#1B5E20",
            command=self.execute_report_generation
        )
        self.generate_report_btn.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))

        # --- Card 3: Status ---
        self.status_card = ctk.CTkFrame(self, corner_radius=10)
        self.status_card.grid(row=2, column=0, sticky="nsew")
        self.status_card.grid_columnconfigure(0, weight=1)
        self.status_card.grid_rowconfigure(1, weight=1)

        self.status_title = ctk.CTkLabel(self.status_card, text="Dziennik Zdarzeń", font=ctk.CTkFont(size=16, weight="bold"))
        self.status_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))

        self.log_text = ctk.CTkTextbox(self.status_card, wrap="word", corner_radius=8)
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.log_text.insert("0.0", "Oczekiwanie na wybór plików...")
        self.log_text.configure(state="disabled")

    def append_log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"\n{text}")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

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
        dest = self.save_input.get().strip()
        if not src or not dest:
            PopupMessage("Brak plików", "Wybierz plik źródłowy i docelowy.", status="warning")
            return
            
        self.append_log("Rozpoczynanie walidacji wsadowej (symulacja w tle)...")
        # Placeholder on thread
        threading.Thread(target=self._simulate_processing, daemon=True).start()

    def _simulate_processing(self):
        import time
        time.sleep(2)
        self.after(0, lambda: PopupMessage("Informacja", "Rozpoczęto weryfikację. Wyniki zostaną zapisane w pliku.", status="success"))
        self.after(0, lambda: self.append_log("Walidacja zakończona pomyślnie."))

    def is_email_valid(self, email):
        regex_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(regex_pattern, email) is not None

    def execute_report_generation(self):
        user_email = self.email_input.get().strip()
        if not self.is_email_valid(user_email):
            PopupMessage("Błąd", "Podano niepoprawny adres email.", status="error")
            return

        src = self.load_input.get().strip()
        dest = self.save_input.get().strip()
        if not src or not dest:
            PopupMessage("Brak plików", "Wybierz plik źródłowy i docelowy.", status="warning")
            return

        self.append_log(f"Walidacja wsadowa z raportem na adres: {user_email}...")
        threading.Thread(target=self._simulate_processing, daemon=True).start()
