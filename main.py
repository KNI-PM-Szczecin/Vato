import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from views.main_window import MainWindow


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
