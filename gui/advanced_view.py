import customtkinter as ctk
import re
from tkinter import filedialog
from gui.popup import PopupMessage


class AdvancedView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.load_container = ctk.CTkFrame(self, fg_color="transparent")
        self.load_container.pack(pady=15)
        self.load_input = ctk.CTkEntry(self.load_container, placeholder_text="Wybór pliku excel", width=220)
        self.load_input.pack(side="left", padx=10)
        self.load_btn = ctk.CTkButton(self.load_container, text="Wybierz", width=80, command=self.handle_file_load)
        self.load_btn.pack(side="left", padx=10)

        self.save_container = ctk.CTkFrame(self, fg_color="transparent")
        self.save_container.pack(pady=15)
        self.save_input = ctk.CTkEntry(self.save_container, placeholder_text="Miejsce zapisu nowego pliku", width=220)
        self.save_input.pack(side="left", padx=10)
        self.save_btn = ctk.CTkButton(self.save_container, text="Wybierz", width=80, command=self.handle_file_save)
        self.save_btn.pack(side="left", padx=10)

        self.quick_validate_btn = ctk.CTkButton(self, text="Szybka walidacja podmiotu", width=320,
                                                command=self.execute_quick_validation)
        self.quick_validate_btn.pack(pady=15)

        self.email_input = ctk.CTkEntry(self, placeholder_text="user@example.com", width=320)
        self.email_input.pack(pady=15)

        self.generate_report_btn = ctk.CTkButton(self, text="Wygeneruj raport i prześlij email", width=320,
                                                 command=self.execute_report_generation)
        self.generate_report_btn.pack(pady=15)

    def handle_file_load(self):
        selected_file = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if selected_file:
            self.load_input.delete(0, 'end')
            self.load_input.insert(0, selected_file)
            print(f"[ADVANCED] Zaladowano plik: {selected_file}")

    def handle_file_save(self):
        target_file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if target_file:
            self.save_input.delete(0, 'end')
            self.save_input.insert(0, target_file)
            print(f"[ADVANCED] Ustawiono miejsce zapisu na: {target_file}")

    def execute_quick_validation(self):
        print("[ADVANCED] Szybka walidacja podmiotu na podstawie pliku zrodlowego.")

    def is_email_valid(self, email):
        regex_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(regex_pattern, email) is not None

    def execute_report_generation(self):
        user_email = self.email_input.get()
        if not self.is_email_valid(user_email):
            print("[ADVANCED] Blad: Podano nieprawidlowy adres email.")
            PopupMessage("Błąd walidacji", "Podano niepoprawny adres email.", status="error")
            return

        source_path = self.load_input.get()
        dest_path = self.save_input.get()
        print(f"[ADVANCED] Przetwarzanie z pliku: {source_path}")
        print(f"[ADVANCED] Zapis do pliku: {dest_path}")
        print(f"[ADVANCED] Wysylanie raportu na adres: {user_email}")