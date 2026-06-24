import os
import sys
from dotenv import load_dotenv
try:
    import env_vars  
except ImportError:
    pass             

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    # Look for .env next to the .exe first, then inside the bundle
    exe_dir = os.path.dirname(sys.executable)
    env_path = os.path.join(exe_dir, '.env')
    if not os.path.exists(env_path):
        env_path = os.path.join(base_path, '.env')
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_path, '.env')

load_dotenv(dotenv_path=env_path)

from app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()