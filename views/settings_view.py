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
            values=["Polski", "English", "Deutsch"],
            command=self.change_language
        )
        current_lang = get_language()
        current = "English" if current_lang == "en" else ("Deutsch" if current_lang == "de" else "Polski")
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

        # --- Card: Głos TTS ---
        self.voice_card = ctk.CTkFrame(self, corner_radius=10)
        self.voice_card.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 15))
        self.voice_card.grid_columnconfigure(0, weight=1)
        
        self.voice_title = ctk.CTkLabel(self.voice_card, text=t("settings.tts_voice"), font=ctk.CTkFont(size=16, weight="bold"))
        self.voice_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))
        
        self.voice_inner_frame = ctk.CTkFrame(self.voice_card, fg_color="transparent")
        self.voice_inner_frame.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))

        self.voice_selector = ctk.CTkComboBox(
            self.voice_inner_frame, 
            values=[],
            command=self.change_voice,
            width=300
        )
        self.voice_selector.grid(row=0, column=0, sticky="w")
        
        is_dark = getattr(self.master, "is_dark_mode", True)
        self.test_voice_btn = ctk.CTkButton(
            self.voice_inner_frame,
            text="",
            image=getattr(self.master, "speaker_on_image", None),
            width=40,
            height=40,
            corner_radius=20,
            fg_color="transparent",
            hover_color="gray30" if is_dark else "gray70",
            command=self.test_voice
        )
        self.test_voice_btn.grid(row=0, column=1, sticky="w", padx=(10, 0))
        
        # Volume slider
        app = self.winfo_toplevel()
        default_vol = app.config_manager.get("tts_volume", 0.33) if hasattr(app, "config_manager") else 0.33
        
        self.volume_label = ctk.CTkLabel(self.voice_inner_frame, text=f"{int(default_vol*100)}%")
        self.volume_label.grid(row=0, column=2, sticky="w", padx=(15, 5))
        
        self.volume_slider = ctk.CTkSlider(
            self.voice_inner_frame, 
            from_=0, 
            to=1, 
            width=100,
            command=self._on_volume_change
        )
        self.volume_slider.set(default_vol)
        self.volume_slider.grid(row=0, column=3, sticky="w")
        
        self._voices_pl = ["Adam", "Antoni", "Domi", "Rachel"]
        self._voices_en = ["Rachel", "Drew", "Clyde", "Mimi", "Fin"]
        self._voices_de = ["Rachel", "Drew", "Clyde", "Mimi", "Fin"]
        self._update_voice_options(get_language())
        
        import threading
        threading.Thread(target=self._fetch_voices_async, daemon=True).start()

    def _on_volume_change(self, val):
        self.volume_label.configure(text=f"{int(val*100)}%")
        app = self.winfo_toplevel()
        if hasattr(app, "config_manager"):
            app.config_manager.set("tts_volume", float(val))

    def _fetch_voices_async(self):
        try:
            from elevenlabs_integration.tts import get_available_voices
            from services.i18n import get_language
            voices = get_available_voices()
            if voices and voices.get("pl") and voices.get("en"):
                self._voices_pl = voices["pl"]
                self._voices_en = voices["en"]
                self._voices_de = voices.get("de", self._voices_en)
                # Safe GUI update from thread in customtkinter using after
                self.after(0, lambda: self._update_voice_options(get_language()))
        except Exception as e:
            print(f"Error in background voice fetch: {e}")

    def test_voice(self):
        voice = self.voice_selector.get()
        phrase = t("settings.tts_test", name=voice)
        from elevenlabs_integration.tts import play_text
        play_text(phrase, override_voice=voice, show_errors=True)

    def change_language(self, choice):
        if choice == "English": lang = "en"
        elif choice == "Deutsch": lang = "de"
        else: lang = "pl"
        from services.i18n import set_language
        set_language(lang)
        app = self.winfo_toplevel()
        if hasattr(app, "config_manager"):
            app.config_manager.set("language", lang)
        self._update_voice_options(lang)

    def _update_voice_options(self, lang):
        voices = {
            "pl": self._voices_pl,
            "en": self._voices_en,
            "de": self._voices_de
        }
        available_voices = voices.get(lang, voices["en"])
        self.voice_selector.configure(values=available_voices)
        
        app = self.winfo_toplevel()
        default_voice = available_voices[0] if available_voices else "Rachel"
        saved_voice = default_voice
        if hasattr(app, "config_manager"):
            saved_voice = app.config_manager.get(f"tts_voice_{lang}", default_voice)
        self.voice_selector.set(saved_voice)

    def change_voice(self, choice):
        lang = get_language()
        app = self.winfo_toplevel()
        if hasattr(app, "config_manager"):
            app.config_manager.set(f"tts_voice_{lang}", choice)

    def update_texts(self):
        self.title_label.configure(text=t("settings.title"))
        self.lang_title.configure(text=t("settings.language"))
        self.accent_title.configure(text=t("settings.accent_title"))
        self.custom_color_label.configure(text=t("settings.custom_color"))
        self.apply_color_btn.configure(text=t("settings.apply"))
        self.voice_title.configure(text=t("settings.tts_voice"))

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
