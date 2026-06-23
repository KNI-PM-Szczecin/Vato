import customtkinter as ctk
from gui.basic_view import BasicView
from gui.advanced_view import AdvancedView


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Veto")
        self.geometry("600x550")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.main_tabs = ctk.CTkTabview(self)
        self.main_tabs.pack(padx=20, pady=20, fill="both", expand=True)

        self.main_tabs.add("Widok Podstawowy")
        self.main_tabs.add("Zaawansowane")

        self.basic_view = BasicView(self.main_tabs.tab("Widok Podstawowy"))
        self.basic_view.pack(fill="both", expand=True)

        self.advanced_view = AdvancedView(self.main_tabs.tab("Zaawansowane"))
        self.advanced_view.pack(fill="both", expand=True)