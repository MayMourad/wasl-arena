"""Stand-alone AI judge (option B in the brief): produce a sealed results report with Python only.

    python -m app.judge_cli football match.mp4 -o report.json [--config cfg.json]

Upload report.json in the app (Live Arena -> "Import AI report"); the app verifies the hash and
HMAC signature before using it, so a modified report is rejected.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from . import integrity
from .main import JUDGES
from .vision import video


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WASL AI Referee (stand-alone judge)")
    ap.add_argument("game", choices=sorted(JUDGES))
    ap.add_argument("video", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--config", type=Path)
    a = ap.parse_args(argv)
    cfg = json.loads(a.config.read_text(encoding="utf-8")) if a.config else {}
    sha = integrity.sha256_file(a.video)
    with tempfile.TemporaryDirectory() as td:
        norm = Path(td) / "norm.mp4"
        if not video.normalize(a.video, norm):
            print("could not decode video", file=sys.stderr)
            return 2
        report = JUDGES[a.game](norm, sha, a.video.name, cfg, lambda s, p, d: print(f"[{s}] {p:.0%} {d}", file=sys.stderr))
    a.out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"report {report['report_id']} sealed: {report['integrity']['report_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
