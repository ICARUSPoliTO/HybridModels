# main.py

import tkinter as tk
from ui.main_window import HybridRocketGUI


if __name__ == "__main__":
    root = tk.Tk()
    app = HybridRocketGUI(root)
    root.mainloop()