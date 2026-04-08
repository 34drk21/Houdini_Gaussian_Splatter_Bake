from __future__ import annotations

from pathlib import Path
import numpy as np

from .config import InputConfig
from .types import VDBFrame


class InputCache:
    def __init__(self) -> None:
        self._cache: dict[int, VDBFrame] = {}

    def get(self, frame: int) -> VDBFrame | None:
        return self._cache.get(frame)

    def put(self, frame: int, data: VDBFrame) -> None:
        self._cache[frame] = data


class VDBReader:
    def __init__(self, config: InputConfig):
        self.config = config
        self.cache = InputCache()

    def frame_range(self) -> range:
        return range(self.config.frame_start, self.config.frame_end + 1, self.config.frame_step)

    def read_frame(self, frame: int) -> VDBFrame:
        cached = self.cache.get(frame)
        if cached is not None:
            return cached

        if self.config.backend == "npz":
            out = self._read_npz(frame)
        elif self.config.backend == "pyopenvdb":
            out = self._read_pyopenvdb(frame)
        else:
            raise ValueError(f"Unsupported backend: {self.config.backend}")

        self.cache.put(frame, out)
        return out

    def _read_npz(self, frame: int) -> VDBFrame:
        path = Path(self.config.input_path) / f"frame_{frame:04d}.npz"
        if not path.exists():
            raise FileNotFoundError(f"Missing frame file: {path}")

        data = np.load(path)
        mapping = self.config.field_mapping
        density = self._load_required(data, mapping["density"], "density")
        flame = self._load_optional(data, mapping.get("flame"), density.shape)
        temp = self._load_optional(data, mapping.get("temperature"), density.shape)
        vel = self._load_optional_velocity(data, mapping.get("vel"), density.shape)
        voxel_size = float(data["voxel_size"]) if "voxel_size" in data else 1.0

        return VDBFrame(
            frame=frame,
            density=density,
            flame=flame,
            temperature=temp,
            vel=vel,
            voxel_size=voxel_size,
            source_path=str(path),
        )

    @staticmethod
    def _load_required(data: np.lib.npyio.NpzFile, key: str, label: str) -> np.ndarray:
        if key not in data:
            raise KeyError(f"Required field '{label}' mapped to '{key}' was not found")
        return np.asarray(data[key], dtype=np.float32)

    @staticmethod
    def _load_optional(data: np.lib.npyio.NpzFile, key: str | None, shape: tuple[int, ...]) -> np.ndarray:
        if key and key in data:
            return np.asarray(data[key], dtype=np.float32)
        return np.zeros(shape, dtype=np.float32)

    @staticmethod
    def _load_optional_velocity(
        data: np.lib.npyio.NpzFile,
        key: str | None,
        shape: tuple[int, ...],
    ) -> np.ndarray | None:
        if key and key in data:
            vel = np.asarray(data[key], dtype=np.float32)
            if vel.shape[-1] != 3:
                raise ValueError("Velocity field must have trailing channel size of 3")
            return vel
        return None

    def _read_pyopenvdb(self, frame: int) -> VDBFrame:
        try:
            import pyopenvdb as vdb  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "pyopenvdb backend selected, but pyopenvdb is not installed. "
                "Install with: pip install pyopenvdb"
            ) from exc

        path = Path(self.config.input_path) / f"frame_{frame:04d}.vdb"
        if not path.exists():
            raise FileNotFoundError(f"Missing frame file: {path}")

        grids = {g.name: g for g in vdb.readAll(str(path))}
        mapping = self.config.field_mapping

        density = self._grid_to_array(grids[mapping["density"]])
        flame = self._grid_to_array(grids[mapping["flame"]]) if mapping.get("flame") in grids else np.zeros_like(density)
        temp = (
            self._grid_to_array(grids[mapping["temperature"]])
            if mapping.get("temperature") in grids
            else np.zeros_like(density)
        )
        vel = None
        vel_key = mapping.get("vel")
        if vel_key in grids:
            vel = self._vec_grid_to_array(grids[vel_key])

        voxel_size = float(grids[mapping["density"]].voxelSize()[0])
        return VDBFrame(
            frame=frame,
            density=density,
            flame=flame,
            temperature=temp,
            vel=vel,
            voxel_size=voxel_size,
            source_path=str(path),
        )

    @staticmethod
    def _grid_to_array(grid) -> np.ndarray:
        bbox = grid.evalActiveVoxelBoundingBox()
        shape = tuple(bbox[1][i] - bbox[0][i] + 1 for i in range(3))
        out = np.zeros(shape, dtype=np.float32)
        grid.copyToArray(out)
        return out

    @staticmethod
    def _vec_grid_to_array(grid) -> np.ndarray:
        bbox = grid.evalActiveVoxelBoundingBox()
        shape = tuple(bbox[1][i] - bbox[0][i] + 1 for i in range(3)) + (3,)
        out = np.zeros(shape, dtype=np.float32)
        grid.copyToArray(out)
        return out
