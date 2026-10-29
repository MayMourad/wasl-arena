"""Generate SYNTHETIC test fixtures with known ground truth.

These are rendered by code (not filmed). They exist to unit-test the judging pipelines with exact
expected outcomes. They are NOT real gameplay and are always labelled synthetic in the app, report
and presentation. Real recorded gameplay is captured separately (see docs/REAL_FOOTAGE.md).

usage: python tools/make_fixtures.py [out_dir]
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import wave
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.rules import falaj as frules  # noqa: E402
from app.vision import markers, video  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "fixtures"
OUT.mkdir(parents=True, exist_ok=True)
FPS = 30


def write_video(path: Path, frames, audio_wav: Path | None = None) -> None:
    tmp = path.with_suffix(".tmp.avi")
    first = frames[0]
    vw = cv2.VideoWriter(str(tmp), cv2.VideoWriter_fourcc(*"MJPG"), FPS, (first.shape[1], first.shape[0]))
    for f in frames:
        vw.write(f)
    vw.release()
    args = [video.FFMPEG, "-hide_banner", "-y", "-i", str(tmp)]
    if audio_wav:
        args += ["-i", str(audio_wav)]
    args += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
    args += ["-c:a", "aac", "-shortest"] if audio_wav else ["-an"]
    args += ["-movflags", "+faststart", str(path)]
    subprocess.run(args, check=True, capture_output=True)
    tmp.unlink()


# ---------------------------------------------------------------- football
W, H = 640, 360
RED, BLUE, BALL = (0, 0, 220), (220, 60, 0), (0, 230, 255)


def football_scene(seconds: float, ball_fn, dribbler_fn, hide=None):
    frames = []
    n = int(seconds * FPS)
    for i in range(n):
        t = i / FPS
        img = np.full((H, W, 3), (44, 130, 52), np.uint8)
        cv2.rectangle(img, (4, 4), (W - 5, H - 5), (235, 235, 235), 2)
        cv2.line(img, (W // 2, 4), (W // 2, H - 5), (235, 235, 235), 2)
        cv2.rectangle(img, (int(0.90 * W), int(0.30 * H)), (W - 2, int(0.70 * H)), (235, 235, 235), 2)
        cv2.rectangle(img, (2, int(0.30 * H)), (int(0.10 * W), int(0.70 * H)), (235, 235, 235), 2)

        def player(cx, cy, col):
            cv2.rectangle(img, (int(cx - 10), int(cy - 18)), (int(cx + 10), int(cy + 18)), col, -1)

        dx, dy = dribbler_fn(t)
        player(dx, dy, RED)  # R1 (the dribbler)
        player(150 + 25 * math.sin(t), 300 + 6 * math.cos(t), RED)
        player(250 + 20 * math.cos(t * 0.8), 70 + 8 * math.sin(t), RED)
        player(420 + 30 * math.sin(t * 0.7), 310, BLUE)
        player(380, 60 + 10 * math.sin(t * 1.1), BLUE)
        player(520 + 15 * math.sin(t), 330, BLUE)
        bx, by = ball_fn(t)
        if not (hide and hide[0] <= t <= hide[1]):
            cv2.circle(img, (int(bx), int(by)), 7, BALL, -1)
        frames.append(img)
    return frames


def dribble(y, stop_x, kick_to=None, kick_t=6.0):
    """returns (ball_fn, dribbler_fn): R1 dribbles right then (optionally) kicks the ball."""
    def pos(t):
        x = 100 + min(t, 6.0) * (stop_x - 100) / 6.0 if t >= 0 else 100
        return x
    def dribbler(t):
        return pos(t), y
    def ball(t):
        if kick_to is not None and t >= kick_t:
            k = min(1.0, (t - kick_t) / 0.5)
            x0 = pos(kick_t) + 22
            return x0 + k * (kick_to - x0), y
        return pos(t) + 22, y
    return ball, dribbler


def make_football():
    out = {}
    b, d = dribble(180, 540, kick_to=612)
    write_video(OUT / "football_goal.mp4", football_scene(12, b, d))
    out["football_goal"] = {"game": "football", "synthetic": True, "expect": {"goals_A": 1, "goals_B": 0, "status": "VERIFIED", "possession_leader": "A"}}
    b, d = dribble(80, 540, kick_to=612)
    write_video(OUT / "football_nogoal.mp4", football_scene(12, b, d))
    out["football_nogoal"] = {"game": "football", "synthetic": True, "expect": {"goals_A": 0, "goals_B": 0}}
    b, d = dribble(180, 540, kick_to=565)
    write_video(OUT / "football_uncertain.mp4", football_scene(12, b, d, hide=(6.6, 12)))
    out["football_uncertain"] = {"game": "football", "synthetic": True, "expect": {"goals_A": 0, "possible_goal": "NEEDS_REVIEW"}}
    return out


# ---------------------------------------------------------------- falaj
CELL = 110
BOARD_PX = (1280, 800)
ORG = (365, 125)  # canonical (0,0) pixel in the flat render


def cpx(cx, cy):
    return int(ORG[0] + cx * CELL), int(ORG[1] + cy * CELL)


SOLUTION = {
    (2, 1): (22, "TEE", 2), (1, 1): (16, "ELBOW", 1), (1, 2): (10, "STRAIGHT", 1), (1, 3): (11, "STRAIGHT", 1), (1, 4): (23, "TEE", 2),
    (3, 1): (17, "ELBOW", 0), (3, 2): (12, "STRAIGHT", 1), (3, 3): (18, "ELBOW", 2), (4, 3): (19, "ELBOW", 0),
}
ORDER = [(2, 1), (1, 1), (1, 2), (1, 3), (1, 4), (3, 1), (3, 2), (3, 3), (4, 3)]


def draw_tile(img, cell, tid, ttype, rot):
    r, c = cell
    x0, y0 = cpx(c, r)
    cv2.rectangle(img, (x0 + 3, y0 + 3), (x0 + CELL - 3, y0 + CELL - 3), (200, 222, 232), -1)
    mid = (x0 + CELL // 2, y0 + CELL // 2)
    for s in frules.open_sides(ttype, rot):
        dr, dc = frules.DELTA[s]
        cv2.line(img, mid, (mid[0] + dc * CELL // 2, mid[1] + dr * CELL // 2), (160, 120, 20), 10)
    m = markers.marker_image(tid, 60)
    for _ in range(rot):
        m = cv2.rotate(m, cv2.ROTATE_90_CLOCKWISE)
    m3 = cv2.cvtColor(m, cv2.COLOR_GRAY2BGR)
    img[mid[1] - 30:mid[1] + 30, mid[0] - 30:mid[0] + 30] = m3


def falaj_frame(tiles, persp):
    img = np.full((BOARD_PX[1], BOARD_PX[0], 3), (232, 238, 244), np.uint8)
    layout = frules.LAYOUTS["oasis-1"]
    for r in range(5):
        for c in range(5):
            x0, y0 = cpx(c, r)
            cv2.rectangle(img, (x0, y0), (x0 + CELL, y0 + CELL), (190, 205, 215), 1)
    sx, sy = cpx(0.5, 2.5)
    cv2.circle(img, (sx - 10, sy), 30, (160, 128, 22), -1)
    for d in layout["destinations"]:
        cv2.circle(img, cpx(d[1] + 0.5, d[0] + 0.5), 34, (107, 163, 198), -1)
    for rk in layout["rocks"]:
        cv2.circle(img, cpx(rk[1] + 0.5, rk[0] + 0.5), 38, (90, 90, 100), -1)
    for cid, (px, py) in {0: (-0.6, -0.6), 1: (5.6, -0.6), 2: (5.6, 5.6), 3: (-0.6, 5.6)}.items():
        cx, cy = cpx(px, py)
        m = cv2.cvtColor(markers.marker_image(cid, 80), cv2.COLOR_GRAY2BGR)
        img[cy - 40:cy + 40, cx - 40:cx + 40] = m
    for cell, (tid, tt, rot) in tiles.items():
        draw_tile(img, cell, tid, tt, rot)
    src = np.float32([[0, 0], [BOARD_PX[0], 0], [BOARD_PX[0], BOARD_PX[1]], [0, BOARD_PX[1]]])
    dst = np.float32(persp)
    Hm = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, Hm, BOARD_PX, borderValue=(232, 238, 244))


def make_falaj():
    persp = [[40, 25], [1235, 5], [1260, 790], [20, 770]]  # mild camera tilt
    out = {}

    def seq(tiles_final, name, order, start=2.0, step=1.0, hold=3.0):
        frames = []
        n_end = start + step * len(order) + hold
        for i in range(int(n_end * FPS)):
            t = i / FPS
            k = max(0, int((t - start) / step) + 1) if t >= start else 0
            placed = {c: tiles_final[c] for c in order[:min(k, len(order))]}
            frames.append(falaj_frame(placed, persp))
        write_video(OUT / name, frames)

    seq(SOLUTION, "falaj_valid.mp4", ORDER)
    out["falaj_valid"] = {"game": "falaj", "synthetic": True, "expect": {"destinations": 3, "leaks": 0, "time_bonus": 2, "total": 11}}
    partial = {c: SOLUTION[c] for c in ORDER[:7]}
    seq(partial, "falaj_partial.mp4", ORDER[:7])
    out["falaj_partial"] = {"game": "falaj", "synthetic": True, "expect": {"destinations": 2, "leaks": 1, "time_bonus": 0, "total": 5}}
    rock = dict(SOLUTION)
    rock[(2, 1)] = (25, "CROSS", 0)  # open east side points into the rock at (2,2)
    seq(rock, "falaj_rock.mp4", ORDER)
    out["falaj_rock"] = {"game": "falaj", "synthetic": True, "expect": {"destinations": 3, "leaks": 1, "time_bonus": 2, "total": 10}}
    return out


# ---------------------------------------------------------------- souq (cards + synthetic speech)
def tts(text: str, path: Path) -> None:
    ps = ("Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate=-1; "
          f"$s.SetOutputToWaveFile('{path}'); $s.Speak('{text}'); $s.Dispose()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, capture_output=True)


def load_16k(path: Path) -> np.ndarray:
    tmp = path.with_suffix(".16k.wav")
    subprocess.run([video.FFMPEG, "-hide_banner", "-y", "-i", str(path), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(tmp)], check=True, capture_output=True)
    with wave.open(str(tmp), "rb") as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    tmp.unlink()
    return data


def make_audio(script: list[tuple[float, str]], seconds: float, path: Path) -> None:
    track = np.zeros(int(seconds * 16000), np.int16)
    for t, text in script:
        p = path.with_name(f"_tts_{abs(hash(text)) % 10**6}.wav")
        tts(text, p)
        d = load_16k(p)
        p.unlink()
        a = int(t * 16000)
        track[a:a + len(d)] += d[:len(track) - a]
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(16000)
        w.writeframes(track.tobytes())


def card(img, cid, label, cx, cy, size=240):
    x0, y0 = cx - size // 2, cy - size // 2 - 30
    cv2.rectangle(img, (x0 - 14, y0 - 14), (x0 + size + 14, y0 + size + 70), (250, 250, 250), -1)
    cv2.rectangle(img, (x0 - 14, y0 - 14), (x0 + size + 14, y0 + size + 70), (60, 60, 60), 3)
    img[y0:y0 + size, x0:x0 + size] = cv2.cvtColor(markers.marker_image(cid, size), cv2.COLOR_GRAY2BGR)
    cv2.putText(img, label, (x0, y0 + size + 45), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (40, 40, 40), 3)


def souq_video(name, shows, script, seconds):
    """shows: [(card_id, label, t0, t1, cx)]"""
    frames = []
    for i in range(int(seconds * FPS)):
        t = i / FPS
        img = np.full((720, 1280, 3), (236, 240, 244), np.uint8)
        cv2.putText(img, "SYNTHETIC TEST FIXTURE", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (150, 150, 150), 2)
        for cid, label, t0, t1, cx in shows:
            if t0 <= t <= t1:
                card(img, cid, label, cx + int(10 * math.sin(t * 3)), 340)
        frames.append(img)
    wav = OUT / f"{name}.wav"
    make_audio(script, seconds, wav)
    write_video(OUT / f"{name}.mp4", frames, wav)
    wav.unlink()


def make_souq():
    out = {}
    souq_video("souq_correct",
               [(60, "Dates", 1.5, 4.5, 640), (61, "Coffee", 5.5, 8.5, 640), (63, "Pottery", 9.5, 12.5, 640)],
               [(1.7, "I choose dates"), (5.7, "Coffee please"), (9.7, "And the pottery")], 14)
    out["souq_correct"] = {"game": "souq", "synthetic": True,
                           "mission": {"requested": ["dates", "coffee", "pottery"], "budget": 60},
                           "transcript_script": [{"start": 1.7, "end": 2.8, "text": "I choose dates"}, {"start": 5.7, "end": 6.6, "text": "Coffee please"},
                                                 {"start": 9.7, "end": 10.7, "text": "And the pottery"}],
                           "expect": {"total": 9, "spend": 55}}
    souq_video("souq_mismatch", [(60, "Dates", 1.5, 4.5, 640)], [(1.8, "I choose honey")], 8)
    out["souq_mismatch"] = {"game": "souq", "synthetic": True, "mission": {"requested": ["dates"], "budget": 60},
                            "transcript_script": [{"start": 1.8, "end": 2.8, "text": "I choose honey"}],
                            "expect": {"mismatch": True, "total": 2}}
    souq_video("souq_budget_dup",
               [(60, "Dates", 1.5, 3.5, 640), (63, "Pottery", 4.5, 6.5, 640), (60, "Dates", 10.0, 12.0, 640), (61, "Coffee", 13.5, 15.5, 640)],
               [(1.7, "dates"), (4.7, "pottery"), (13.7, "coffee")], 17)
    out["souq_budget_dup"] = {"game": "souq", "synthetic": True, "mission": {"requested": ["dates", "pottery", "coffee"], "budget": 50},
                              "transcript_script": [{"start": 1.7, "end": 2.3, "text": "dates"}, {"start": 4.7, "end": 5.3, "text": "pottery"},
                                                    {"start": 13.7, "end": 14.3, "text": "coffee"}],
                              "expect": {"duplicate": True, "budget_exceeded": True, "total": 7}}
    return out


if __name__ == "__main__":
    manifest = {}
    for fn in (make_football, make_falaj, make_souq):
        manifest.update(fn())
        print("generated", fn.__name__)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("done:", sorted(p.name for p in OUT.iterdir()))
