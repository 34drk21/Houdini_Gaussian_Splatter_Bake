from __future__ import annotations

import numpy as np

from .config import ConvertConfig
from .types import LookdevFrame, PointsFrame


class GSPointConverter:
    def __init__(self, config: ConvertConfig):
        self.config = config
        self.rng = np.random.default_rng(config.random_seed)

    def convert(self, frame: LookdevFrame) -> PointsFrame:
        if self.config.sampling_mode == "voxel_center":
            mask = frame.opacity_final > self.config.density_threshold
        elif self.config.sampling_mode == "density_scatter":
            prob = np.clip(frame.density_shaped * self.config.scatter_scale, 0.0, 1.0)
            mask = self.rng.random(prob.shape) < prob
            mask &= frame.opacity_final > self.config.density_threshold
        else:
            raise ValueError(f"Unsupported sampling mode: {self.config.sampling_mode}")

        ijk = np.argwhere(mask)
        if ijk.size == 0:
            return self._empty(frame.frame)

        P = ijk.astype(np.float32) * frame.voxel_size

        sampled_cd = frame.cd_final[mask]
        sampled_opacity = frame.opacity_final[mask]

        isotropic = np.full((P.shape[0], 3), frame.voxel_size * self.config.scale_multiplier, dtype=np.float32)
        rot = np.zeros((P.shape[0], 4), dtype=np.float32)
        rot[:, 3] = 1.0  # identity quaternion

        if self.config.generate_id:
            ids = np.arange(P.shape[0], dtype=np.int32)
        else:
            ids = np.full(P.shape[0], -1, dtype=np.int32)

        vel = frame.vel[mask] if frame.vel is not None else None

        return PointsFrame(
            frame=frame.frame,
            P=P,
            f_dc=sampled_cd.astype(np.float32),
            opacity=sampled_opacity.astype(np.float32),
            scale=isotropic,
            rot=rot,
            id=ids,
            vel=vel.astype(np.float32) if vel is not None else None,
        )

    @staticmethod
    def _empty(frame: int) -> PointsFrame:
        return PointsFrame(
            frame=frame,
            P=np.zeros((0, 3), dtype=np.float32),
            f_dc=np.zeros((0, 3), dtype=np.float32),
            opacity=np.zeros((0,), dtype=np.float32),
            scale=np.zeros((0, 3), dtype=np.float32),
            rot=np.zeros((0, 4), dtype=np.float32),
            id=np.zeros((0,), dtype=np.int32),
            vel=None,
        )
