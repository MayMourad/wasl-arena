import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures"


@pytest.fixture(scope="session")
def fixtures() -> Path:
    if not (FIX / "falaj_valid.mp4").exists():
        subprocess.run([sys.executable, str(ROOT / "tools" / "make_fixtures.py"), str(FIX)], check=True)
    return FIX


@pytest.fixture(scope="session")
def manifest(fixtures) -> dict:
    return json.loads((fixtures / "manifest.json").read_text(encoding="utf-8"))


def noop(stage, p, detail):
    pass
