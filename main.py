import os
import sys
from dotenv import load_dotenv

try:
    import env_vars  
except ImportError:
    pass             

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

load_dotenv(dotenv_path=os.path.join(base_path, '.env')) 

from app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()