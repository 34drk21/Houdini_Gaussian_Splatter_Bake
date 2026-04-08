from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
import numpy as np

from .config import ExportConfig, PipelineConfig
from .types import PointsFrame, VDBFrame


class UE5Exporter:
    def __init__(self, config: ExportConfig, pipeline_config: PipelineConfig):
        self.config = config
        self.pipeline_config = pipeline_config
        self.config.output_path.mkdir(parents=True, exist_ok=True)

    def export_frame(self, points: PointsFrame) -> Path:
        out = self.config.output_path / f"gs_points_{points.frame:04d}.npz"
        payload: dict[str, np.ndarray] = {
            "P": points.P,
            "f_dc": points.f_dc,
            "opacity": points.opacity,
            "scale": points.scale,
            "rot": points.rot,
            "id": points.id,
        }
        if points.vel is not None:
            payload["vel"] = points.vel
        np.savez_compressed(out, **payload)

        if self.config.write_debug_json:
            debug = self.config.output_path / f"gs_points_{points.frame:04d}.json"
            debug.write_text(
                json.dumps(
                    {
                        "frame": points.frame,
                        "point_count": int(points.P.shape[0]),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

        return out

    def export_metadata(self, frames: list[VDBFrame], point_counts: dict[int, int]) -> Path:
        if not self.config.write_metadata:
            return self.config.output_path / "metadata.skipped.json"

        bmin = [float("inf"), float("inf"), float("inf")]
        bmax = [float("-inf"), float("-inf"), float("-inf")]
        for fr in frames:
            shape = fr.density.shape
            ext = [shape[2] * fr.voxel_size, shape[1] * fr.voxel_size, shape[0] * fr.voxel_size]
            for i in range(3):
                bmin[i] = min(bmin[i], 0.0)
                bmax[i] = max(bmax[i], ext[i])

        meta = {
            "frame_range": [self.pipeline_config.input.frame_start, self.pipeline_config.input.frame_end],
            "fps": self.pipeline_config.fps,
            "bbox": {"min": bmin, "max": bmax},
            "voxel_size": float(frames[0].voxel_size) if frames else 1.0,
            "point_count_per_frame": point_counts,
            "source_sim_info": {
                "input_path": str(self.pipeline_config.input.input_path),
                "backend": self.pipeline_config.input.backend,
                "field_mapping": self.pipeline_config.input.field_mapping,
            },
            "export_version": self.pipeline_config.version,
            "export_config": asdict(self.pipeline_config.export),
        }
        out = self.config.output_path / "metadata.json"
        out.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return out
