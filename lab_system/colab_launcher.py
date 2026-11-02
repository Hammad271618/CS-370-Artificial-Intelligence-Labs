"""
Launcher to open any local .ipynb file directly in Google Colab in the default web browser.
"""

import sys
import webbrowser
from pathlib import Path

REPO_OWNER = "Hammad271618"
REPO_NAME = "CS-370-Artificial-Intelligence-Labs"
BASE_DIR = Path(__file__).resolve().parent.parent


def open_in_colab(filepath: str | Path):
    path = Path(filepath).resolve()
    try:
        rel = path.relative_to(BASE_DIR).as_posix()
        url = f"https://colab.research.google.com/github/{REPO_OWNER}/{REPO_NAME}/blob/main/{rel}"
    except ValueError:
        # Fallback if outside repo
        url = "https://colab.research.google.com/#upload"

    print(f"Opening in Google Colab: {url}")
    webbrowser.open(url)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else str(BASE_DIR / "reports" / "Lab_07_Minimax_Tic_Tac_Toe" / "Lab_07_Minimax_Tic_Tac_Toe.ipynb")
    open_in_colab(target)
