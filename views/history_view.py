import customtkinter as ctk
from services.i18n import t
from services.history_manager import HistoryManager
from views.popup import PopupMessage

class HistoryView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.history_mgr = HistoryManager()
        
        # Header Card
        self.header_card = ctk.CTkFrame(self, corner_radius=10)
        self.header_card.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.header_card.grid_columnconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(self.header_card, text=t("history.title"), font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 15))
        
        self.refresh_btn = ctk.CTkButton(self.header_card, text=t("history.refresh_btn"), width=100, command=self.load_history)
        self.refresh_btn.grid(row=0, column=1, padx=(0, 10), pady=(15, 15))
        
        self.clear_btn = ctk.CTkButton(self.header_card, text=t("history.clear_btn"), width=120, fg_color="#C62828", hover_color="#B71C1C", command=self.clear_history)
        self.clear_btn.grid(row=0, column=2, padx=(0, 20), pady=(15, 15))
        
        # Scrollable Area for History Cards
        self.scroll_area = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.scroll_area.grid(row=1, column=0, sticky="nsew")
        self.scroll_area.grid_columnconfigure(0, weight=1)
        
        self.cards = []
        self.load_history()
        
    def update_texts(self):
        self.title_label.configure(text=t("history.title"))
        self.refresh_btn.configure(text=t("history.refresh_btn"))
        self.clear_btn.configure(text=t("history.clear_btn"))
        self.load_history()
        
    def clear_history(self):
        self.history_mgr.clear_history()
        self.load_history()
        PopupMessage(t("popup.success"), t("history.cleared_msg"), status="success")
        
    def load_history(self):
        # Cancel any ongoing load tasks if we hit refresh rapidly
        if hasattr(self, "_load_task") and self._load_task:
            self.after_cancel(self._load_task)
            self._load_task = None

        # Remove existing cards
        for card in self.cards:
            card.destroy()
        self.cards.clear()
        
        entries = self.history_mgr.get_history()
        
        if not entries:
            empty_lbl = ctk.CTkLabel(self.scroll_area, text=t("history.empty"), text_color="gray")
            empty_lbl.grid(row=0, column=0, pady=40)
            self.cards.append(empty_lbl)
            return
            
        self._render_entry_step(entries, 0)

    def _render_entry_step(self, entries, index):
        if not self.winfo_exists() or index >= len(entries):
            self._load_task = None
            return
            
        entry = entries[index]
        etype = entry.get("type", "UNKNOWN")
        value = entry.get("value", "")
        timestamp = entry.get("timestamp", "")
        
        # Translate type
        if etype == "NIP":
            type_str = t("history.type_nip")
        elif etype == "BATCH":
            type_str = t("history.type_batch")
        else:
            type_str = etype
            
        card = ctk.CTkFrame(self.scroll_area, corner_radius=8, fg_color=("gray85", "gray25"))
        card.grid(row=index, column=0, sticky="ew", padx=10, pady=(10, 0))
        card.grid_columnconfigure(1, weight=1)
        
        time_lbl = ctk.CTkLabel(card, text=timestamp, font=ctk.CTkFont(size=12, weight="bold"), text_color=("gray30", "gray70"))
        time_lbl.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        import os
        display_value = os.path.basename(value) if etype == "BATCH" else value
        val_lbl = ctk.CTkLabel(card, text=f"{type_str}: {display_value}", font=ctk.CTkFont(size=14))
        val_lbl.grid(row=0, column=1, padx=15, pady=10, sticky="w")
        
        reuse_btn = ctk.CTkButton(card, text=t("history.reuse_btn"), width=80, height=28, command=lambda e=etype, v=value: self.reuse_entry(e, v))
        reuse_btn.grid(row=0, column=2, padx=15, pady=10, sticky="e")
        
        self.cards.append(card)
        
        # load next card after 20ms to make it sequential and smooth
        self._load_task = self.after(20, lambda: self._render_entry_step(entries, index + 1))

    def reuse_entry(self, etype, value):
        app = self.winfo_toplevel()
        try:
            if etype == "NIP":
                tab_name = app.main_tabs._name_list[0]
                if tab_name in app.main_tabs._segmented_button._buttons_dict:
                    app.main_tabs._segmented_button._buttons_dict[tab_name].invoke()
                else:
                    app.main_tabs.set(tab_name)
                
                app.basic_view.nip_input.delete(0, "end")
                app.basic_view.nip_input.insert(0, value)
                app.basic_view.method_selector.set("NIP")
            elif etype == "BATCH":
                tab_name = app.main_tabs._name_list[1]
                if tab_name in app.main_tabs._segmented_button._buttons_dict:
                    app.main_tabs._segmented_button._buttons_dict[tab_name].invoke()
                else:
                    app.main_tabs.set(tab_name)
                    
                app.advanced_view.load_input.delete(0, "end")
                app.advanced_view.load_input.insert(0, value)
        except Exception as e:
            PopupMessage("Error", f"Could not switch view: {e}", status="error")
