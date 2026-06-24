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
from views.settings_view import SettingsView
from views.history_view import HistoryView
from services.i18n import t, on_language_change

class App(ctk.CTk):
    def __init__(self):
        super().__init__(className="Vato")

        self.title(t("app.title"))
        self.geometry("1000x900")
        self.minsize(900, 800)
        
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
                
                canvas_size = int(pil_img.width * 1.35)
                canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
                offset = ((canvas_size - pil_img.width) // 2, (canvas_size - pil_img.height) // 2)
                canvas.paste(pil_img, offset)
                
                self._dock_icon = ImageTk.PhotoImage(canvas)
                self.iconphoto(True, self._dock_icon)
        except Exception as e:
            print(f"Failed to load window icon: {e}")

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
            print(f"Failed to load logo: {e}")
            self.title_label = ctk.CTkLabel(
                self.header_frame, 
                text="Vato 📊", 
                font=ctk.CTkFont(size=28, weight="bold")
            )

        self.title_label.grid(row=0, column=0, sticky="w")

        # Top Right Main Frame
        self.top_right_main_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.top_right_main_frame.grid(row=0, column=1, sticky="e")

        # Top Right Settings Frame (hidden by default)
        self.top_right_settings_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        
        self.close_settings_btn = ctk.CTkButton(
            self.top_right_settings_frame,
            text="✕",
            font=ctk.CTkFont(size=20, weight="bold"),
            width=40,
            height=40,
            corner_radius=20,
            fg_color="transparent",
            text_color=("black", "white"),
            hover_color=("gray70", "gray30"),
            command=self.close_settings
        )
        self.close_settings_btn.pack()

        from services.config_manager import ConfigManager
        self.config_manager = ConfigManager()
        
        # Load language setting before rendering anything
        saved_lang = self.config_manager.get("language", "pl")
        from services.i18n import set_language
        set_language(saved_lang)

        self.accent_color = self.config_manager.get("accent_color", "#3B8ED0")
        
        try:
            self.sun_image = ctk.CTkImage(Image.open(os.path.join(base_path, "static", "sun.png")), size=(24, 24))
            self.moon_image = ctk.CTkImage(Image.open(os.path.join(base_path, "static", "moon.png")), size=(24, 24))
            self.settings_image = ctk.CTkImage(Image.open(os.path.join(base_path, "static", "settings.png")), size=(24, 24))
            self.speaker_on_image = ctk.CTkImage(Image.open(os.path.join(base_path, "static", "speaker.png")), size=(24, 24))
            self.speaker_off_image = ctk.CTkImage(Image.open(os.path.join(base_path, "static", "speaker_muted.png")), size=(24, 24))
        except Exception as e:
            print(f"Failed to load icons: {e}")
            self.sun_image = None
            self.moon_image = None
            self.settings_image = None
            self.speaker_on_image = None
            self.speaker_off_image = None

        self.is_dark_mode = ctk.get_appearance_mode() == "Dark"
        self.is_muted = self.config_manager.get("is_muted", False)
        
        self.speaker_btn = ctk.CTkButton(
            self.top_right_main_frame,
            text="",
            image=self.speaker_off_image if self.is_muted else self.speaker_on_image,
            width=40,
            height=40,
            corner_radius=20,
            fg_color="transparent",
            hover_color="gray30" if self.is_dark_mode else "gray70",
            command=self.toggle_speaker
        )
        self.speaker_btn.grid(row=0, column=0, padx=5)
        
        self.theme_btn = ctk.CTkButton(
            self.top_right_main_frame,
            text="",
            image=self.sun_image if self.is_dark_mode else self.moon_image,
            width=40,
            height=40,
            corner_radius=20,
            fg_color="transparent",
            hover_color="gray30" if self.is_dark_mode else "gray70",
            command=self.toggle_theme
        )
        self.theme_btn.grid(row=0, column=1, padx=5)

        self.settings_btn = ctk.CTkButton(
            self.top_right_main_frame,
            text="",
            image=self.settings_image,
            width=40,
            height=40,
            corner_radius=20,
            fg_color="transparent",
            hover_color="gray30" if self.is_dark_mode else "gray70",
            command=self.open_settings
        )
        self.settings_btn.grid(row=0, column=2, padx=(5, 0))

        # Tabview
        self.main_tabs = ctk.CTkTabview(self, corner_radius=10)
        self.main_tabs.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))

        self.main_tabs.add(t("tabs.basic"))
        self.main_tabs.add(t("tabs.advanced"))
        self.main_tabs.add(t("tabs.history"))
        
        self._tab_name_basic = t("tabs.basic")
        self._tab_name_advanced = t("tabs.advanced")
        self._tab_name_history = t("tabs.history")

        self.basic_view = BasicView(self.main_tabs.tab(self._tab_name_basic))
        self.basic_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.advanced_view = AdvancedView(self.main_tabs.tab(self._tab_name_advanced))
        self.advanced_view.pack(fill="both", expand=True, padx=10, pady=10)

        self.history_view = HistoryView(self.main_tabs.tab(self._tab_name_history))
        self.history_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.settings_view = SettingsView(self)
        
        # Aplikuj domyślny kolor akcentu na start
        self.apply_accent_color(self.accent_color)
        
        on_language_change(self.update_texts)

    def update_texts(self):
        self.title(t("app.title"))
        
        new_basic = t("tabs.basic")
        new_advanced = t("tabs.advanced")
        new_history = t("tabs.history")
        
        if new_basic != self._tab_name_basic:
            self.main_tabs.rename(self._tab_name_basic, new_basic)
            self._tab_name_basic = new_basic
            
        if new_advanced != self._tab_name_advanced:
            self.main_tabs.rename(self._tab_name_advanced, new_advanced)
            self._tab_name_advanced = new_advanced
            
        if new_history != self._tab_name_history:
            self.main_tabs.rename(self._tab_name_history, new_history)
            self._tab_name_history = new_history
        
        self.basic_view.update_texts()
        self.advanced_view.update_texts()
        self.history_view.update_texts()
        self.settings_view.update_texts()

    def toggle_speaker(self):
        self.is_muted = not self.is_muted
        self.speaker_btn.configure(image=self.speaker_off_image if self.is_muted else self.speaker_on_image)
        self.config_manager.set("is_muted", self.is_muted)
        state = "Muted" if self.is_muted else "On"
        print(f"Audio: {state}")

    def open_settings(self):
        self.top_right_main_frame.grid_remove()
        self.top_right_settings_frame.grid(row=0, column=1, sticky="e")
        self.main_tabs.grid_remove()
        self.settings_view.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))

    def close_settings(self):
        self.top_right_settings_frame.grid_remove()
        self.top_right_main_frame.grid(row=0, column=1, sticky="e")
        self.settings_view.grid_remove()
        self.main_tabs.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))

    def toggle_theme(self):
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
            
        self.update()

    def apply_accent_color(self, hex_color):
        self.accent_color = hex_color
        self.config_manager.set("accent_color", hex_color)
        
        import os
        from PIL import Image
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        def colorize_icon(img_path, color):
            img = Image.open(img_path).convert("RGBA")
            alpha = img.split()[3]
            color_img = Image.new("RGBA", img.size, color)
            color_img.putalpha(alpha)
            return color_img

        try:
            self.settings_image = ctk.CTkImage(colorize_icon(os.path.join(base_path, "static", "settings.png"), hex_color), size=(24, 24))
            self.speaker_on_image = ctk.CTkImage(colorize_icon(os.path.join(base_path, "static", "speaker.png"), hex_color), size=(24, 24))
        except Exception as e:
            print(f"Błąd kolorowania ikon: {e}")

        self.settings_btn.configure(image=self.settings_image)
        self.speaker_btn.configure(image=self.speaker_off_image if self.is_muted else self.speaker_on_image)

        self._update_widget_colors(self, hex_color)

    def _update_widget_colors(self, widget, hex_color):
        import customtkinter as ctk
        
        if hasattr(widget, "is_color_preset_btn") and widget.is_color_preset_btn:
            pass
        elif isinstance(widget, ctk.CTkButton):
            current_color = widget.cget("fg_color")
            if current_color != "transparent" and current_color != ["transparent", "transparent"]:
                def darken(hex_c, factor):
                    hex_c = hex_c.lstrip('#')
                    if len(hex_c) == 6:
                        r, g, b = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
                        return f"#{max(0, int(r * factor)):02x}{max(0, int(g * factor)):02x}{max(0, int(b * factor)):02x}"
                    return "#" + hex_c

                if hasattr(widget, "is_action_btn") and widget.is_action_btn:
                    widget.configure(fg_color=darken(hex_color, 0.75), hover_color=darken(hex_color, 0.55))
                else:
                    widget.configure(fg_color=hex_color, hover_color=darken(hex_color, 0.85))
                
        elif isinstance(widget, ctk.CTkProgressBar):
            widget.configure(progress_color=hex_color)
            
        elif isinstance(widget, ctk.CTkCheckBox):
            widget.configure(fg_color=hex_color, hover_color=hex_color)
            
        elif isinstance(widget, ctk.CTkTabview):
            widget.configure(segmented_button_selected_color=hex_color, segmented_button_selected_hover_color=hex_color)
            
        for child in widget.winfo_children():
            self._update_widget_colors(child, hex_color)

if __name__ == "__main__":
    app = App()
    app.mainloop()