import sys
from pathlib import Path


def resource_path(*parts) -> Path:
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            base = Path(sys._MEIPASS)
        else:
            base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent

    return base.joinpath(*parts)