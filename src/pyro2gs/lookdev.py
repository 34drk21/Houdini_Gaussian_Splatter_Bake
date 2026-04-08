from __future__ import annotations

import numpy as np

from .config import LookdevConfig
from .types import LookdevFrame, VDBFrame


class LookdevProcessor:
    def __init__(self, config: LookdevConfig):
        self.config = config

    def process(self, frame: VDBFrame) -> LookdevFrame:
        density_shaped = np.clip(frame.density * self.config.density_gain + self.config.density_bias, 0.0, 1.0)

        flame_mask = np.clip(frame.flame, 0.0, 1.0)
        temperature_mask = np.clip(frame.temperature, 0.0, 1.0)

        scatter_col = np.asarray(self.config.scatter_color, dtype=np.float32)
        emit_col = np.asarray(self.config.emission_color, dtype=np.float32)

        cd_scatter = density_shaped[..., None] * scatter_col
        cd_emit = (flame_mask * temperature_mask)[..., None] * emit_col

        exposure_mult = 2.0 ** self.config.exposure
        cd_final = np.clip((cd_scatter + cd_emit) * exposure_mult, 0.0, 1.0).astype(np.float32)

        opacity_raw = np.clip(density_shaped * self.config.opacity_gain, 0.0, 1.0)
        opacity_final = np.power(opacity_raw, self.config.opacity_gamma).astype(np.float32)

        return LookdevFrame(
            frame=frame.frame,
            density_shaped=density_shaped.astype(np.float32),
            cd_final=cd_final,
            opacity_final=opacity_final,
            vel=frame.vel,
            voxel_size=frame.voxel_size,
        )
