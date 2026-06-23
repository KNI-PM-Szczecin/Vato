import customtkinter as ctk

class PopupMessage(ctk.CTkToplevel):
    def __init__(self, title, message, status="default"):
        super().__init__()
        
        self.title(title)
        self.geometry("450x220")
        self.resizable(False, False)

        self.attributes("-topmost", True)
        self.grab_set()

        colors = {
            "success": ("#4CAF50", "#2E7D32"),   # Light/Dark green
            "error": ("#F44336", "#C62828"),     # Light/Dark red
            "warning": ("#FF9800", "#EF6C00"),   # Light/Dark orange
            "default": ("gray70", "gray30")
        }
        
        color_pair = colors.get(status, colors["default"])
        
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, border_width=2, border_color=color_pair)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.label = ctk.CTkLabel(
            self.main_frame, 
            text=message, 
            wraplength=380, 
            justify="center",
            font=ctk.CTkFont(size=14)
        )
        self.label.pack(pady=(30, 20), padx=20, fill="both", expand=True)

        self.button = ctk.CTkButton(
            self.main_frame, 
            text="Zrozumiałem", 
            command=self.destroy, 
            width=120,
            fg_color=color_pair,
            hover_color=color_pair[1]
        )
        self.button.pack(pady=(0, 20))
