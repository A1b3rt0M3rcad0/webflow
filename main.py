from dotenv import load_dotenv
load_dotenv()

import tkinter as tk
from tkinter import ttk

from src.ui.app import App


def main():
    root = tk.Tk()
    root.title("WebFlow - Gerenciador de Workflows")
    root.geometry("900x700")
    root.minsize(600, 400)

    style = ttk.Style()
    style.theme_use("clam")

    app = App(root)
    app.pack(fill="both", expand=True, padx=5, pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
