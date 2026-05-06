"""
Hybrid Rocket Simulation - Main Entry Point

Run this file to start the application.
"""

import tkinter as tk
from gui.main_window import HybridRocketGUI


def main():
    """Main entry point for the application"""
    root = tk.Tk()
    app = HybridRocketGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
