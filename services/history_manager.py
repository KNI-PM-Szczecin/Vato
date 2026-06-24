import os
import json
import sys
import datetime

class HistoryManager:
    """
    Singleton class managing the application's local history.
    Stores user activity (e.g., NIP validation, Batch processing) in a JSON file
    located in the user's OS-specific application data directory.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HistoryManager, cls).__new__(cls)
            cls._instance._init_paths()
        return cls._instance
        
    def _init_paths(self):
        """
        Initializes the cross-platform path to the local data directory
        and ensures the history.json file exists.
        """
        app_name = "Vato"
        if sys.platform.startswith('win'):
            base_dir = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or os.path.expanduser('~')
            self.data_dir = os.path.join(base_dir, app_name)
        elif sys.platform == 'darwin':
            self.data_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
        else:
            self.data_dir = os.path.join(os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share')), app_name)
            
        os.makedirs(self.data_dir, exist_ok=True)
        self.history_file = os.path.join(self.data_dir, "history.json")
        
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
                
    def add_entry(self, entry_type: str, value: str):
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception:
            history = []
            
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": now,
            "type": entry_type,
            "value": value
        }
        
        history.insert(0, entry) # prepend
        
        # limit history to 100 entries to prevent bloat
        history = history[:100]
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
            
    def get_history(self):
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
            
    def clear_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump([], f)

