from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from vitaguide.converter import write_dataset  # noqa: E402


def main() -> None:
    xlsx = ROOT / "TabelaInterações.xlsx"
    output = ROOT / "data" / "dataset.json"
    write_dataset(xlsx, output)
    print(f"Dataset gerado em: {output}")


if __name__ == "__main__":
    main()
