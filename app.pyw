from __future__ import annotations

import sys
from pathlib import Path
from tkinter import messagebox, Tk

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vitaguide.ui import main  # noqa: E402


if __name__ == "__main__":
    dataset = ROOT / "data" / "dataset.json"
    if not dataset.exists():
        root = Tk()
        root.withdraw()
        messagebox.showerror(
            "VitaGuide",
            "Nao foi encontrado data/dataset.json. Execute scripts/build_dataset.py primeiro.",
        )
        root.destroy()
        raise SystemExit(1)
    main(dataset)
