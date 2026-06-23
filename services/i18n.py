import json
import os

class I18n:
    _instance = None
    _translations = {}
    _current_lang = "pl"
    _listeners = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(I18n, cls).__new__(cls)
            cls._instance.load_lang("pl")
        return cls._instance

    def load_lang(self, lang="pl"):
        self._current_lang = lang
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        lang_path = os.path.join(base_dir, "languages", f"{lang}.json")
        try:
            with open(lang_path, "r", encoding="utf-8") as f:
                self._translations = json.load(f)
            self._notify_listeners()
        except Exception as e:
            print(f"Failed to load language {lang}: {e}")
            self._translations = {}

    def get(self, key, default=None):
        keys = key.split('.')
        val = self._translations
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default or key
        return val

    def add_listener(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def _notify_listeners(self):
        for callback in self._listeners:
            try:
                callback()
            except Exception as e:
                print(f"Error in translation listener: {e}")

def t(key, **kwargs):
    i18n = I18n()
    text = i18n.get(key)
    if kwargs and isinstance(text, str):
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text

def set_language(lang):
    I18n().load_lang(lang)
    
def get_language():
    return I18n()._current_lang

def on_language_change(callback):
    I18n().add_listener(callback)
