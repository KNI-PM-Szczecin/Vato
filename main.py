import os
import sys
from dotenv import load_dotenv

if hasattr(sys, '_MEIPASS'):
    # Running as a compiled application (PyInstaller)
    env_path = os.path.join(sys._MEIPASS, '.env')
else:
    # Running directly as a standard Python script in a local IDE
    env_path = '.env'

load_dotenv(dotenv_path=env_path)

from app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()