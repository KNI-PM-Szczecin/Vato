import customtkinter as ctk
import sys
import os
import ctypes

myappid = 'Vato.HackathonMorski.1.0'

if sys.platform.startswith("win"):
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception as e:
        print(f"Nie udało się ustawić AppUserModelID: {e}")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from views.basic_view import BasicView
from views.advanced_view import AdvancedView

class App(ctk.CTk):
    def __init__(self):
        super().__init__(className="Vato")

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
                from PIL import ImageTk
                pil_img = Image.open(os.path.join(base_path, "static", "vato_v_white.png")).convert("RGBA")
                
                # Zmniejszamy wizualnie ikonę dodając przezroczysty margines (padding)
                canvas_size = int(pil_img.width * 1.35)
                canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
                offset = ((canvas_size - pil_img.width) // 2, (canvas_size - pil_img.height) // 2)
                canvas.paste(pil_img, offset)
                
                self._dock_icon = ImageTk.PhotoImage(canvas)
                self.iconphoto(True, self._dock_icon)
        except Exception as e:
            print(f"Nie udało się załadować ikony okna: {e}")

        try:
            self.logo_image = ctk.CTkImage(
                light_image=Image.open(os.path.join(base_path, "static", "vato_black.png")),
                dark_image=Image.open(os.path.join(base_path, "static", "vato_white.png")),
                size=(150, 80)
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
        try:
            self.sun_image = ctk.CTkImage(Image.open(os.path.join(base_path, "static", "sun.png")), size=(24, 24))
            self.moon_image = ctk.CTkImage(Image.open(os.path.join(base_path, "static", "moon.png")), size=(24, 24))
        except Exception as e:
            print(f"Nie udało się załadować ikon: {e}")
            self.sun_image = None
            self.moon_image = None

        self.is_dark_mode = ctk.get_appearance_mode() == "Dark"
        
        self.theme_btn = ctk.CTkButton(
            self.header_frame,
            text="",
            image=self.sun_image if self.is_dark_mode else self.moon_image,
            width=40,
            height=40,
            corner_radius=20,
            fg_color="transparent",
            hover_color="gray30" if self.is_dark_mode else "gray70",
            command=self.toggle_theme
        )
        self.theme_btn.grid(row=0, column=1, sticky="e")

        # Tabview
        self.main_tabs = ctk.CTkTabview(self, corner_radius=10)
        self.main_tabs.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))

        self.main_tabs.add("Widok Podstawowy")
        self.main_tabs.add("Weryfikacja Wsadowa")

        self.basic_view = BasicView(self.main_tabs.tab("Widok Podstawowy"))
        self.basic_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.advanced_view = AdvancedView(self.main_tabs.tab("Weryfikacja Wsadowa"))
        self.advanced_view.pack(fill="both", expand=True, padx=10, pady=10)

    def toggle_theme(self):
        # Wymuszamy zakończenie bieżących zadań interfejsu (bufor)
        self.update_idletasks()
        
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            ctk.set_appearance_mode("Dark")
            self.theme_btn.configure(
                image=self.sun_image,
                hover_color="gray30"
            )
        else:
            ctk.set_appearance_mode("Light")
            self.theme_btn.configure(
                image=self.moon_image,
                hover_color="gray70"
            )
            
        # Synchroniczne, jednoczesne odrysowanie całości, by ukryć ewentualne "klatkowanie" elementów
        self.update()