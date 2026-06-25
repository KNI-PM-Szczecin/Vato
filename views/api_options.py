import customtkinter as ctk
from services.i18n import t

class ApiOptionsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.bind("<Configure>", self._rearrange_checkboxes)
        
        self.api_vars = {
            "VAT": ctk.BooleanVar(value=True),
            "KRS": ctk.BooleanVar(value=True),
            "CEIDG": ctk.BooleanVar(value=True),
            "VIES": ctk.BooleanVar(value=True),
            "KSEF": ctk.BooleanVar(value=False),
            "WEB": ctk.BooleanVar(value=True),
            "NEWS": ctk.BooleanVar(value=True)
        }
        
        self._checkbox_widgets = []
        self._create_checkboxes()
        
    def _create_checkboxes(self):
        # Clear existing
        for cb in self._checkbox_widgets:
            cb.destroy()
        self._checkbox_widgets.clear()
        
        unavail_text = t("basic.unavailable") if hasattr(t, "__call__") else "Niedostępne"
        
        checkboxes_def = [
            ("VAT", "Biała Lista VAT"), 
            ("KRS", "KRS"), 
            ("CEIDG", "CEIDG"), 
            ("VIES", "VIES [EU]"), 
            ("KSEF", f"KSeF ({unavail_text})"), 
            ("WEB", "Weryfikacja cyfrowa"), 
            ("NEWS", "Wiadomości prasowe")
        ]
        
        for code, label_str in checkboxes_def:
            is_unavail = code == "KSEF"
            cb = ctk.CTkCheckBox(
                self, 
                text=label_str, 
                variable=self.api_vars[code],
                checkbox_width=18, 
                checkbox_height=18, 
                border_width=2,
                font=ctk.CTkFont(size=12),
                state="disabled" if is_unavail else "normal",
                text_color="gray50" if is_unavail else None
            )
            # Make sure it picks up the theme color dynamically
            # (If _update_theme_manager was called before this, it will)
            self._checkbox_widgets.append(cb)
            
        self._rearrange_checkboxes(None)
        
    def _rearrange_checkboxes(self, event):
        if not self._checkbox_widgets:
            return
            
        width = self.winfo_width()
        if width < 100:
            width = self.master.winfo_width() - 40
            
        cols = max(1, width // 160)
            
        for i, cb in enumerate(self._checkbox_widgets):
            r = i // cols
            c = i % cols
            cb.grid(row=r, column=c, sticky="w", padx=(0, 15), pady=4)
            
    def get_config(self):
        return {k: v.get() for k, v in self.api_vars.items()}
        
    def update_texts(self):
        unavail_text = t("basic.unavailable") if hasattr(t, "__call__") else "Niedostępne"
        for cb in self._checkbox_widgets:
            if "KSeF" in cb.cget("text"):
                cb.configure(text=f"KSeF ({unavail_text})")
