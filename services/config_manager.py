import os
import json
import sys

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._init_paths()
        return cls._instance
        
    def _init_paths(self):
        app_name = "Vato"
        if sys.platform.startswith('win'):
            base_dir = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or os.path.expanduser('~')
            self.data_dir = os.path.join(base_dir, app_name)
        elif sys.platform == 'darwin':
            self.data_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
        else:
            self.data_dir = os.path.join(os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share')), app_name)
            
        os.makedirs(self.data_dir, exist_ok=True)
        self.config_file = os.path.join(self.data_dir, "settings.json")
        self.config = self._load()
        
    def _load(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
            
    def _save(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def get(self, key, default=None):
        return self.config.get(key, default)
        
    def set(self, key, value):
        self.config[key] = value
        self._save()

