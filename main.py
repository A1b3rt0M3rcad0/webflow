from dotenv import load_dotenv
load_dotenv()

import subprocess
import sys
import tkinter as tk
from tkinter import ttk

from src.ui.app import App


def _ensure_playwright_browsers():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
    except Exception:
        print("Playwright browsers não instalados, instalando...")
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=False,
        )
        print("Playwright browsers instalados")


def main():
    print("Iniciando WebFlow...")
    _ensure_playwright_browsers()
    print("WebFlow iniciado")
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
