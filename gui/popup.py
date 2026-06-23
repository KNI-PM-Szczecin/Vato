import customtkinter as ctk

class PopupMessage(ctk.CTkToplevel):
    def __init__(self, title, message, status="default"):
        super().__init__()
        
        self.title(title)
        self.geometry("400x200")

        self.attributes("-topmost", True)
        self.grab_set()

        colors = {
            "success": "#2E7D32",   # green
            "error": "#D32F2F",     # red
            "warning": "#F57C00",   # yellow
            "default": "transparent"
        }
        border_color = colors.get(status, "transparent")
        border_width = 3 if status != "default" else 0

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent", border_color=border_color, border_width=border_width)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.label = ctk.CTkLabel(self.main_frame, text=message, wraplength=350, justify="center")
        self.label.pack(pady=(40, 20), padx=20, fill="both", expand=True)

        self.button = ctk.CTkButton(self.main_frame, text="OK", command=self.destroy, width=100)
        self.button.pack(pady=(0, 20))
