"""Runtime configuration. All credentials are read from the environment (server-side only)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv(ROOT / ".env")

DATA = Path(os.getenv("WASL_DATA_DIR", ROOT / "data"))
for _d in ("uploads", "reports", "evidence", "audit"):
    (DATA / _d).mkdir(parents=True, exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
SIGNING_KEY = os.getenv("JUDGE_SIGNING_KEY", "dev-only-signing-key-change-me")
SIGNING_KEY_ID = "judge-key-" + __import__("hashlib").sha256(SIGNING_KEY.encode()).hexdigest()[:8]
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "200"))
