"""ArUco marker detection (printed visual markers used by Falaj Flow tiles and Souq Signal cards)."""
from __future__ import annotations

import cv2
import numpy as np

DICT = cv2.aruco.DICT_4X4_100


def _detector() -> "cv2.aruco.ArucoDetector":
    params = cv2.aruco.DetectorParameters()
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    return cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(DICT), params)


_DET = None


def detect(frame_bgr: np.ndarray) -> list[dict]:
    """-> [{id, corners: 4x2 float32 (TL,TR,BR,BL in marker frame), center: (x,y)}]"""
    global _DET
    if _DET is None:
        _DET = _detector()
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = _DET.detectMarkers(gray)
    out = []
    if ids is None:
        return out
    for c, i in zip(corners, ids.flatten()):
        pts = c.reshape(4, 2).astype(np.float32)
        out.append({"id": int(i), "corners": pts, "center": pts.mean(axis=0)})
    return out


def marker_image(marker_id: int, px: int = 200) -> np.ndarray:
    return cv2.aruco.generateImageMarker(cv2.aruco.getPredefinedDictionary(DICT), marker_id, px)
