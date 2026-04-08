from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from pyro2gs.cli import _load_config
from pyro2gs.pipeline import Pipeline


def _write_frame(path: Path, frame: int, density_scale: float) -> None:
    density = np.zeros((8, 8, 8), dtype=np.float32)
    density[2:6, 2:6, 2:6] = density_scale
    flame = density * 0.8
    temperature = density * 0.6
    vel = np.zeros((8, 8, 8, 3), dtype=np.float32)
    vel[..., 2] = density
    np.savez_compressed(
        path / f"frame_{frame:04d}.npz",
        density=density,
        flame=flame,
        temperature=temperature,
        vel=vel,
        voxel_size=np.float32(0.1),
    )


def test_pipeline_end_to_end(tmp_path: Path) -> None:
    in_dir = tmp_path / "input"
    out_dir = tmp_path / "output"
    in_dir.mkdir()

    _write_frame(in_dir, 1, 0.3)
    _write_frame(in_dir, 2, 0.7)

    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "input": {
                    "input_path": str(in_dir),
                    "frame_start": 1,
                    "frame_end": 2,
                    "backend": "npz",
                },
                "convert": {
                    "sampling_mode": "voxel_center",
                    "density_threshold": 0.01,
                },
                "export": {
                    "output_path": str(out_dir),
                    "write_metadata": True,
                },
            }
        ),
        encoding="utf-8",
    )

    cfg = _load_config(config_path)
    result = Pipeline(cfg).run()

    assert len(result.exported_files) == 2
    assert (out_dir / "metadata.json").exists()

    meta = json.loads((out_dir / "metadata.json").read_text(encoding="utf-8"))
    assert meta["frame_range"] == [1, 2]
    assert set(meta["point_count_per_frame"].keys()) == {"1", "2"}
    assert meta["point_count_per_frame"]["2"] >= meta["point_count_per_frame"]["1"]
