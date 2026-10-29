"""Speech transcription.

Gemini is used for *transcription only*. It never scores: its output is a list of timed text
segments that the deterministic Souq rule engine then keyword-matches. Segments that do not
overlap real audio energy are dropped (guards against hallucinated speech on silent clips).
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx

from .. import config
from . import video

PROMPT = (
    "Transcribe the speech in this audio exactly as spoken. The speaker may use English, Arabic or both. "
    "Return a JSON array of segments: {\"start\": seconds, \"end\": seconds, \"text\": verbatim transcript}. "
    "Do not translate, summarise or add words that were not spoken. If there is no speech, return []."
)
SCHEMA = {
    "type": "ARRAY",
    "items": {"type": "OBJECT", "properties": {"start": {"type": "NUMBER"}, "end": {"type": "NUMBER"}, "text": {"type": "STRING"}},
              "required": ["start", "end", "text"]},
}
ENERGY_FLOOR = 0.008


def transcribe(wav_path: str | Path) -> dict:
    """-> {status: OK|NO_SPEECH|UNAVAILABLE, source, segments, reason?}"""
    activity = video.speech_activity(wav_path)
    if not activity or max(e for _, e in activity) < ENERGY_FLOOR:
        return {"status": "NO_SPEECH", "source": "energy-gate", "segments": [], "reason": "audio track is silent"}
    if not config.GEMINI_API_KEY:
        return {"status": "UNAVAILABLE", "source": None, "segments": [], "reason": "no transcription key configured on the server"}
    data = Path(wav_path).read_bytes()
    if len(data) > 18 * 1024 * 1024:
        return {"status": "UNAVAILABLE", "source": None, "segments": [], "reason": "audio longer than the 18 MB transcription limit"}
    payload = {
        "contents": [{"parts": [{"text": PROMPT}, {"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(data).decode()}}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "responseSchema": SCHEMA,
                             "thinkingConfig": {"thinkingBudget": 0}},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent"
    try:
        r = httpx.post(url, headers={"x-goog-api-key": config.GEMINI_API_KEY}, json=payload, timeout=120)
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        raw = json.loads(text)
    except Exception as exc:  # network, quota, malformed output -> never invent a transcript
        return {"status": "UNAVAILABLE", "source": None, "segments": [], "reason": f"transcription failed: {type(exc).__name__}"}
    duration = activity[-1][0] + 0.25
    segs = []
    for s in raw if isinstance(raw, list) else []:
        try:
            a, b, txt = float(s["start"]), float(s["end"]), str(s["text"]).strip()
        except (KeyError, TypeError, ValueError):
            continue
        if not txt or a < 0 or b < a or a > duration + 1:
            continue
        # drop segments with no real sound underneath (anti-hallucination gate)
        if not any(ENERGY_FLOOR <= e and a - 0.5 <= t <= b + 0.5 for t, e in activity):
            continue
        segs.append({"start": round(a, 2), "end": round(min(b, duration), 2), "text": txt})
    return {"status": "OK" if segs else "NO_SPEECH", "source": f"{config.GEMINI_MODEL} (transcription only)", "segments": segs}
