import customtkinter as ctk
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from views.basic_view import BasicView
from views.advanced_view import AdvancedView

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Vato - Weryfikacja Kontrahentów")
        self.geometry("900x750")
        self.minsize(800, 650)
        
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)

        from PIL import Image
        import tkinter as tk
        base_path = os.path.dirname(os.path.abspath(__file__))

        try:
            if sys.platform.startswith("win"):
                self.iconbitmap(os.path.join(base_path, "static", "vato_v_white.ico"))
            else:
                img = tk.PhotoImage(file=os.path.join(base_path, "static", "vato_v_white.png"))
                self.iconphoto(True, img)
        except Exception as e:
            print(f"Nie udało się załadować ikony okna: {e}")

        try:
            self.logo_image = ctk.CTkImage(
                light_image=Image.open(os.path.join(base_path, "static", "vato_black.png")),
                dark_image=Image.open(os.path.join(base_path, "static", "vato_white.png")),
                size=(120, 65)
            )
            self.title_label = ctk.CTkLabel(
                self.header_frame, 
                text="", 
                image=self.logo_image
            )
        except Exception as e:
            print(f"Nie udało się załadować logo: {e}")
            self.title_label = ctk.CTkLabel(
                self.header_frame, 
                text="Vato 📊", 
                font=ctk.CTkFont(size=28, weight="bold")
            )

        self.title_label.grid(row=0, column=0, sticky="w")

        # Theme Switch
        self.theme_switch = ctk.CTkSwitch(
            self.header_frame, 
            text="Tryb Ciemny", 
            command=self.toggle_theme,
            font=ctk.CTkFont(size=14)
        )
        self.theme_switch.grid(row=0, column=1, sticky="e")
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()

        # Tabview
        self.main_tabs = ctk.CTkTabview(self, corner_radius=10)
        self.main_tabs.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))

        self.main_tabs.add("Widok Podstawowy")
        self.main_tabs.add("Weryfikacja Wsadowa (Excel)")

        self.basic_view = BasicView(self.main_tabs.tab("Widok Podstawowy"))
        self.basic_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.advanced_view = AdvancedView(self.main_tabs.tab("Weryfikacja Wsadowa (Excel)"))
        self.advanced_view.pack(fill="both", expand=True, padx=10, pady=10)

    def toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")