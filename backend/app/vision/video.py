"""Video / audio I/O: FFmpeg normalisation, probing, frame sampling, evidence thumbnails."""
from __future__ import annotations

import re
import subprocess
import wave
from pathlib import Path
from typing import Callable, Iterator

import cv2
import imageio_ffmpeg
import numpy as np

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
Progress = Callable[[str, float, str], None]


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([FFMPEG, "-hide_banner", *args], capture_output=True, text=True, errors="replace")


def normalize(src: str | Path, dst: str | Path, max_width: int = 1280, fps: int = 30) -> bool:
    """Re-encode to H.264/AAC MP4 (browser playable, constant fps). Returns True on success."""
    r = _run(["-y", "-i", str(src), "-vf", f"scale='min({max_width},iw)':-2,fps={fps}", "-c:v", "libx264", "-preset", "veryfast",
              "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(dst)])
    return r.returncode == 0 and Path(dst).exists() and Path(dst).stat().st_size > 0


def probe(path: str | Path) -> dict:
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    info = _run(["-i", str(path)]).stderr
    has_audio = bool(re.search(r"Stream #\d+:\d+.*Audio:", info))
    dur = 0.0
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", info)
    if m:
        dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    elif fps and frames:
        dur = frames / fps
    return {"fps": round(fps, 3), "width": w, "height": h, "duration_s": round(dur, 3), "has_audio": has_audio,
            "frame_count": int(frames)}


def iter_samples(path: str | Path, sample_fps: float, work_width: int | None = None) -> Iterator[tuple[int, float, np.ndarray]]:
    """Yield (sample_index, time_seconds, BGR frame) at ~sample_fps. Frames optionally downscaled."""
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, int(round(fps / sample_fps)))
    i = n = 0
    while True:
        if not cap.grab():
            break
        if i % step == 0:
            ok, frame = cap.retrieve()
            if not ok:
                break
            if work_width and frame.shape[1] > work_width:
                s = work_width / frame.shape[1]
                frame = cv2.resize(frame, (work_width, int(frame.shape[0] * s)), interpolation=cv2.INTER_AREA)
            yield n, i / fps, frame
            n += 1
        i += 1
    cap.release()


def frame_at(path: str | Path, t: float) -> np.ndarray | None:
    cap = cv2.VideoCapture(str(path))
    cap.set(cv2.CAP_PROP_POS_MSEC, max(t, 0) * 1000.0)
    ok, frame = cap.read()
    cap.release()
    return frame if ok else None


def save_jpg(frame: np.ndarray, path: str | Path, max_width: int = 720) -> None:
    if frame.shape[1] > max_width:
        s = max_width / frame.shape[1]
        frame = cv2.resize(frame, (max_width, int(frame.shape[0] * s)), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 82])


def extract_audio(src: str | Path, wav: str | Path) -> bool:
    r = _run(["-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)])
    return r.returncode == 0 and Path(wav).exists() and Path(wav).stat().st_size > 1000


def speech_activity(wav: str | Path, window_s: float = 0.25) -> list[tuple[float, float]]:
    """Return [(t, rms)] energy windows so transcript segments can be checked against real sound."""
    with wave.open(str(wav), "rb") as w:
        sr = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    hop = int(sr * window_s)
    out = []
    for i in range(0, len(data) - hop + 1, hop):
        seg = data[i:i + hop]
        out.append((i / sr, float(np.sqrt(np.mean(seg ** 2)))))
    return out
