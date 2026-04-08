from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import ConvertConfig, ExportConfig, InputConfig, LookdevConfig, PipelineConfig
from .pipeline import Pipeline


DEFAULT_FIELD_MAPPING = {
    "density": "density",
    "flame": "flame",
    "temperature": "temperature",
    "vel": "vel",
}


def _load_config(path: Path) -> PipelineConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))

    input_cfg = InputConfig(
        input_path=Path(raw["input"]["input_path"]),
        frame_start=int(raw["input"]["frame_start"]),
        frame_end=int(raw["input"]["frame_end"]),
        frame_step=int(raw["input"].get("frame_step", 1)),
        backend=raw["input"].get("backend", "npz"),
        field_mapping=raw["input"].get("field_mapping", DEFAULT_FIELD_MAPPING),
    )

    lookdev_cfg = LookdevConfig(**raw.get("lookdev", {}))
    convert_cfg = ConvertConfig(**raw.get("convert", {}))

    export_block = raw.get("export", {})
    export_cfg = ExportConfig(
        output_path=Path(export_block.get("output_path", "./out")),
        export_sequence=bool(export_block.get("export_sequence", True)),
        write_metadata=bool(export_block.get("write_metadata", True)),
        write_debug_json=bool(export_block.get("write_debug_json", False)),
    )

    return PipelineConfig(
        input=input_cfg,
        lookdev=lookdev_cfg,
        convert=convert_cfg,
        export=export_cfg,
        fps=float(raw.get("fps", 24.0)),
        version=str(raw.get("version", "0.1")),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Pyro VDB -> Gaussian Splat converter")
    parser.add_argument("--config", type=Path, required=True, help="Path to JSON config file")
    args = parser.parse_args()

    cfg = _load_config(args.config)
    result = Pipeline(cfg).run()

    print("[pyro2gs] Export complete")
    print(f"  metadata: {result.metadata_file}")
    print("  point counts:")
    for frame, count in result.point_counts.items():
        print(f"    frame {frame}: {count}")


if __name__ == "__main__":
    main()
