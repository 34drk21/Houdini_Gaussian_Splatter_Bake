from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(slots=True)
class VDBFrame:
    frame: int
    density: np.ndarray
    flame: np.ndarray
    temperature: np.ndarray
    vel: np.ndarray | None
    voxel_size: float
    source_path: str


@dataclass(slots=True)
class LookdevFrame:
    frame: int
    density_shaped: np.ndarray
    cd_final: np.ndarray
    opacity_final: np.ndarray
    vel: np.ndarray | None
    voxel_size: float


@dataclass(slots=True)
class PointsFrame:
    frame: int
    P: np.ndarray
    f_dc: np.ndarray
    opacity: np.ndarray
    scale: np.ndarray
    rot: np.ndarray
    id: np.ndarray
    vel: np.ndarray | None
