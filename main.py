import os
import sys
from dotenv import load_dotenv

if hasattr(sys, '_MEIPASS'):
    # Uruchomienie jako skompilowana aplikacja (PyInstaller)
    env_path = os.path.join(sys._MEIPASS, '.env')
else:
    # Uruchomienie bezpośrednio jako zwykły skrypt pythona w lokalnym IDE
    env_path = '.env'

load_dotenv(dotenv_path=env_path)

from app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()