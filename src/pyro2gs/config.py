from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class InputConfig:
    input_path: Path
    frame_start: int
    frame_end: int
    frame_step: int = 1
    backend: str = "npz"
    field_mapping: dict[str, str] = field(
        default_factory=lambda: {
            "density": "density",
            "flame": "flame",
            "temperature": "temperature",
            "vel": "vel",
        }
    )


@dataclass(slots=True)
class LookdevConfig:
    density_gain: float = 1.0
    density_bias: float = 0.0
    opacity_gain: float = 1.0
    opacity_gamma: float = 1.0
    exposure: float = 0.0
    scatter_color: tuple[float, float, float] = (0.8, 0.8, 0.8)
    emission_color: tuple[float, float, float] = (1.0, 0.45, 0.1)


@dataclass(slots=True)
class ConvertConfig:
    sampling_mode: str = "voxel_center"  # voxel_center | density_scatter
    density_threshold: float = 0.01
    scatter_scale: float = 4.0
    scale_multiplier: float = 1.0
    generate_id: bool = True
    random_seed: int = 42


@dataclass(slots=True)
class ExportConfig:
    output_path: Path
    export_sequence: bool = True
    write_metadata: bool = True
    write_debug_json: bool = False


@dataclass(slots=True)
class PipelineConfig:
    input: InputConfig
    lookdev: LookdevConfig = field(default_factory=LookdevConfig)
    convert: ConvertConfig = field(default_factory=ConvertConfig)
    export: ExportConfig = field(default_factory=lambda: ExportConfig(output_path=Path("./out")))
    fps: float = 24.0
    version: str = "0.1"
