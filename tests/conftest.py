import os
from pathlib import Path

# load_json reads HUMANIZER_DATA_DIR at call time; point it at the repo's data/.
os.environ.setdefault(
    "HUMANIZER_DATA_DIR",
    str(Path(__file__).resolve().parent.parent / "data"),
)
