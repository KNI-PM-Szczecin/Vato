import customtkinter as ctk
import re
from views.popup import PopupMessage
from services.i18n import t, set_language, get_language

class SettingsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text=t("settings.title"), font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # --- Card: Język ---
        self.lang_card = ctk.CTkFrame(self, corner_radius=10)
        self.lang_card.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 15))
        self.lang_card.grid_columnconfigure(0, weight=1)
        
        self.lang_title = ctk.CTkLabel(self.lang_card, text=t("settings.language"), font=ctk.CTkFont(size=16, weight="bold"))
        self.lang_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))
        
        self.lang_selector = ctk.CTkComboBox(
            self.lang_card, 
            values=["Polski", "English"],
            command=self.change_language
        )
        current = "English" if get_language() == "en" else "Polski"
        self.lang_selector.set(current)
        self.lang_selector.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))

        # --- Card: Kolor akcentu ---
        self.accent_card = ctk.CTkFrame(self, corner_radius=10)
        self.accent_card.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        self.accent_card.grid_columnconfigure(0, weight=1)

        self.accent_title = ctk.CTkLabel(self.accent_card, text=t("settings.accent_title"), font=ctk.CTkFont(size=16, weight="bold"))
        self.accent_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        self.presets_frame = ctk.CTkFrame(self.accent_card, fg_color="transparent")
        self.presets_frame.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))

        self.presets = ["#3B8ED0", "#2E7D32", "#E65100", "#673AB7", "#D32F2F", "#E91E63", "#009688"]
        self.preset_buttons = []
        
        for i, color in enumerate(self.presets):
            btn = ctk.CTkButton(
                self.presets_frame,
                text="",
                width=30,
                height=30,
                corner_radius=15,
                fg_color=color,
                hover_color=color,
                command=lambda c=color: self.set_custom_color(c)
            )
            btn.is_color_preset_btn = True
            btn.grid(row=0, column=i, padx=(0, 10))
            self.preset_buttons.append(btn)

        self.custom_color_frame = ctk.CTkFrame(self.accent_card, fg_color="transparent")
        self.custom_color_frame.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 15))
        
        self.custom_color_label = ctk.CTkLabel(self.custom_color_frame, text=t("settings.custom_color"))
        self.custom_color_label.grid(row=0, column=0, padx=(0, 10))
        
        self.custom_color_entry = ctk.CTkEntry(self.custom_color_frame, placeholder_text="#RRGGBB", width=100)
        self.custom_color_entry.grid(row=0, column=1, padx=(0, 10))
        
        self.apply_color_btn = ctk.CTkButton(self.custom_color_frame, text=t("settings.apply"), width=80, command=self.apply_custom_color)
        self.apply_color_btn.grid(row=0, column=2)

    def change_language(self, choice):
        lang = "en" if choice == "English" else "pl"
        set_language(lang)
        # We need to trigger an update, handled by the app

    def update_texts(self):
        self.title_label.configure(text=t("settings.title"))
        self.lang_title.configure(text=t("settings.language"))
        self.accent_title.configure(text=t("settings.accent_title"))
        self.custom_color_label.configure(text=t("settings.custom_color"))
        self.apply_color_btn.configure(text=t("settings.apply"))

    def set_custom_color(self, hex_color):
        self.custom_color_entry.delete(0, 'end')
        self.custom_color_entry.insert(0, hex_color)
        self.apply_custom_color()

    def apply_custom_color(self):
        color = self.custom_color_entry.get().strip().upper()
        if not color.startswith("#"):
            color = "#" + color
            
        if re.match(r"^#[0-9A-Fa-f]{6}$", color):
            self.master.apply_accent_color(color)
        else:
            PopupMessage(t("popup.error"), t("settings.invalid_color"), status="error")
