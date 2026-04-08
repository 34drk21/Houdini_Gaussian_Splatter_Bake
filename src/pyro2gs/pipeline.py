from __future__ import annotations

from dataclasses import dataclass

from .config import PipelineConfig
from .convert import GSPointConverter
from .exporter import UE5Exporter
from .lookdev import LookdevProcessor
from .types import PointsFrame, VDBFrame
from .vdb_reader import VDBReader


@dataclass(slots=True)
class PipelineResult:
    exported_files: list[str]
    metadata_file: str
    point_counts: dict[int, int]


class Pipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.reader = VDBReader(config.input)
        self.lookdev = LookdevProcessor(config.lookdev)
        self.converter = GSPointConverter(config.convert)
        self.exporter = UE5Exporter(config.export, config)

    def run(self) -> PipelineResult:
        source_frames: list[VDBFrame] = []
        exported: list[str] = []
        counts: dict[int, int] = {}

        for frame in self.reader.frame_range():
            src = self.reader.read_frame(frame)
            source_frames.append(src)

            look = self.lookdev.process(src)
            points: PointsFrame = self.converter.convert(look)

            out = self.exporter.export_frame(points)
            exported.append(str(out))
            counts[frame] = int(points.P.shape[0])

        metadata = self.exporter.export_metadata(source_frames, counts)
        return PipelineResult(exported_files=exported, metadata_file=str(metadata), point_counts=counts)
