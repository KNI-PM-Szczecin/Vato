import customtkinter as ctk

class PopupMessage(ctk.CTkToplevel):
    def __init__(self, title, message, status="default", **kwargs):
        super().__init__()

        self.title(title)
        self.geometry("450x220")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        colors = {
            "success": ("#4CAF50", "#2E7D32"),
            "error":   ("#F44336", "#C62828"),
            "warning": ("#FF9800", "#EF6C00"),
            "default": ("gray70",  "gray30"),
        }
        color_pair = colors.get(status, colors["default"])

        # Load Icon
        import os
        import sys
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        try:
            if sys.platform.startswith("win"):
                self.iconbitmap(os.path.join(base_path, "static", "vato_v_white.ico"))
            else:
                from PIL import Image, ImageTk
                pil_img = Image.open(os.path.join(base_path, "static", "vato_v_white.png")).convert("RGBA")
                canvas_size = int(pil_img.width * 1.35)
                canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
                offset = ((canvas_size - pil_img.width) // 2, (canvas_size - pil_img.height) // 2)
                canvas.paste(pil_img, offset)
                self._dock_icon = ImageTk.PhotoImage(canvas)
                self.iconphoto(True, self._dock_icon)
        except Exception:
            pass

        self.main_frame = ctk.CTkFrame(self, corner_radius=15, border_width=2, border_color=color_pair)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.label = ctk.CTkLabel(
            self.main_frame,
            text=message,
            wraplength=380,
            justify="center",
            font=ctk.CTkFont(size=14),
        )
        self.label.pack(pady=(30, 20), padx=20, fill="both", expand=True)

        from services.i18n import t
        
        if kwargs.get("tts_progress", False):
            self.progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            self.progress_frame.pack(fill="x", padx=40, pady=(0, 10))
            
            self.progress = ctk.CTkProgressBar(self.progress_frame, mode="indeterminate", height=6)
            self.progress.pack(fill="x", pady=(0, 5))
            self.progress.start()
            
            self.tts_label = ctk.CTkLabel(self.progress_frame, text=t("popup.tts_loading", default="Ładowanie modułu mowy (ElevenLabs)..."), font=ctk.CTkFont(size=11), text_color="gray")
            self.tts_label.pack()

        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(pady=(0, 20))

        if status == "error":
            self.copy_btn = ctk.CTkButton(
                self.button_frame, 
                text=t("popup.copy_error"), 
                command=lambda: self._copy_error(message),
                width=120,
                fg_color="transparent",
                border_width=1,
                border_color=color_pair[0],
                text_color=color_pair[0],
                hover_color=color_pair[1]
            )
            self.copy_btn.pack(side="left", padx=(0, 10))

        self.button = ctk.CTkButton(
            self.button_frame, 
            text=t("popup.ok_btn"), 
            command=self._close_popup,
            width=120,
            fg_color=color_pair,
            hover_color=color_pair[1],
        )
        self.button.pack(side="left")

        # Na Linuxie (X11) grab_set() wywołany przed MapNotify powoduje
        # że widgety wewnątrz okna nie są rysowane. Opóźnienie 50ms
        # daje czas na zmapowanie okna przez serwer X przed grab.
        self.after(50, self._activate)

    def _copy_error(self, message):
        self.clipboard_clear()
        self.clipboard_append(message)
        from services.i18n import t
        self.copy_btn.configure(text=t("popup.copied_title"))
        self.after(2000, lambda: self.copy_btn.configure(text=t("popup.copy_error")))

    def stop_tts_progress(self):
        try:
            if hasattr(self, "progress"):
                self.progress.stop()
            if hasattr(self, "progress_frame"):
                self.progress_frame.destroy()
        except Exception:
            pass

    def _close_popup(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _activate(self):
        self.lift()
        self.focus_force()
        self.grab_set()
