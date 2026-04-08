from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .cli import _load_config
from .config import ConvertConfig, ExportConfig, InputConfig, LookdevConfig, PipelineConfig
from .convert import GSPointConverter
from .exporter import UE5Exporter
from .lookdev import LookdevProcessor
from .vdb_reader import VDBReader


class AppState:
    def __init__(self) -> None:
        self.config = PipelineConfig(
            input=InputConfig(input_path=Path("."), frame_start=1, frame_end=1),
            lookdev=LookdevConfig(),
            convert=ConvertConfig(),
            export=ExportConfig(output_path=Path("./out")),
        )


class Pyro2GSApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Pyro2GS Standalone")
        self.geometry("980x700")
        self.state_obj = AppState()

        self._build_menu()
        self._build_layout()
        self._refresh_ui_from_config()

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Import NPZ Sequence...", command=self._on_import_npz)
        file_menu.add_command(label="Load Config...", command=self._on_load_config)
        file_menu.add_command(label="Save Config...", command=self._on_save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Export...", command=self._on_export_sequence)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_input = ttk.Frame(notebook)
        self.tab_lookdev = ttk.Frame(notebook)
        self.tab_convert = ttk.Frame(notebook)
        self.tab_export = ttk.Frame(notebook)

        notebook.add(self.tab_input, text="Sim Input")
        notebook.add(self.tab_lookdev, text="Lookdev")
        notebook.add(self.tab_convert, text="GS Convert")
        notebook.add(self.tab_export, text="Export")

        self._build_input_tab()
        self._build_lookdev_tab()
        self._build_convert_tab()
        self._build_export_tab()

        bottom = ttk.Frame(root)
        bottom.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(bottom, text="Preview Current Frame", command=self._on_preview_frame).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Export Sequence", command=self._on_export_sequence).pack(side=tk.LEFT, padx=(8, 0))
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(bottom, textvariable=self.status_var).pack(side=tk.RIGHT)

        log_frame = ttk.LabelFrame(root, text="Log", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=False, pady=(8, 0))
        self.log = tk.Text(log_frame, height=8)
        self.log.pack(fill=tk.BOTH, expand=True)

    def _build_input_tab(self) -> None:
        frame = self.tab_input
        frame.columnconfigure(1, weight=1)

        self.input_path_var = tk.StringVar()
        self.frame_start_var = tk.IntVar(value=1)
        self.frame_end_var = tk.IntVar(value=1)
        self.frame_step_var = tk.IntVar(value=1)
        self.backend_var = tk.StringVar(value="npz")

        ttk.Label(frame, text="Input Path").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.input_path_var).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(frame, text="Browse", command=self._on_import_npz).grid(row=0, column=2, padx=(8, 0), pady=4)

        ttk.Label(frame, text="Frame Start").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.frame_start_var).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Frame End").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.frame_end_var).grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Frame Step").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.frame_step_var).grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Backend").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Combobox(frame, textvariable=self.backend_var, values=["npz", "pyopenvdb"], state="readonly").grid(
            row=4, column=1, sticky="ew", pady=4
        )

    def _build_lookdev_tab(self) -> None:
        frame = self.tab_lookdev
        frame.columnconfigure(1, weight=1)

        self.density_gain_var = tk.DoubleVar(value=1.0)
        self.opacity_gain_var = tk.DoubleVar(value=1.0)
        self.opacity_gamma_var = tk.DoubleVar(value=1.0)
        self.exposure_var = tk.DoubleVar(value=0.0)

        self.scatter_color_var = tk.StringVar(value="0.8,0.8,0.8")
        self.emission_color_var = tk.StringVar(value="1.0,0.45,0.1")

        entries = [
            ("Density Gain", self.density_gain_var),
            ("Opacity Gain", self.opacity_gain_var),
            ("Opacity Gamma", self.opacity_gamma_var),
            ("Exposure", self.exposure_var),
            ("Scatter Color (r,g,b)", self.scatter_color_var),
            ("Emission Color (r,g,b)", self.emission_color_var),
        ]
        for i, (label, var) in enumerate(entries):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=4)
            ttk.Entry(frame, textvariable=var).grid(row=i, column=1, sticky="ew", pady=4)

    def _build_convert_tab(self) -> None:
        frame = self.tab_convert
        frame.columnconfigure(1, weight=1)

        self.sampling_mode_var = tk.StringVar(value="voxel_center")
        self.density_threshold_var = tk.DoubleVar(value=0.01)
        self.scale_multiplier_var = tk.DoubleVar(value=1.0)
        self.scatter_scale_var = tk.DoubleVar(value=4.0)
        self.generate_id_var = tk.BooleanVar(value=True)

        ttk.Label(frame, text="Sampling Mode").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Combobox(
            frame,
            textvariable=self.sampling_mode_var,
            values=["voxel_center", "density_scatter"],
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Density Threshold").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.density_threshold_var).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Scatter Scale").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.scatter_scale_var).grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(frame, text="Scale Multiplier").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.scale_multiplier_var).grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Checkbutton(frame, text="Generate Point IDs", variable=self.generate_id_var).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=4
        )

    def _build_export_tab(self) -> None:
        frame = self.tab_export
        frame.columnconfigure(1, weight=1)

        self.output_path_var = tk.StringVar(value="./out")
        self.fps_var = tk.DoubleVar(value=24.0)
        self.write_metadata_var = tk.BooleanVar(value=True)
        self.write_debug_json_var = tk.BooleanVar(value=False)

        ttk.Label(frame, text="Output Path").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.output_path_var).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(frame, text="Browse", command=self._on_select_output).grid(row=0, column=2, padx=(8, 0), pady=4)

        ttk.Label(frame, text="FPS").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.fps_var).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Checkbutton(frame, text="Write metadata.json", variable=self.write_metadata_var).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=4
        )
        ttk.Checkbutton(frame, text="Write debug json per frame", variable=self.write_debug_json_var).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=4
        )

    def _on_import_npz(self) -> None:
        selected = filedialog.askdirectory(title="Select NPZ Sequence Folder")
        if not selected:
            return
        self.input_path_var.set(selected)
        self._log(f"Imported input folder: {selected}")

    def _on_select_output(self) -> None:
        selected = filedialog.askdirectory(title="Select Output Folder")
        if not selected:
            return
        self.output_path_var.set(selected)

    def _on_load_config(self) -> None:
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], title="Load Config")
        if not file_path:
            return
        try:
            cfg = _load_config(Path(file_path))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Load Failed", str(exc))
            return

        self.state_obj.config = cfg
        self._refresh_ui_from_config()
        self._log(f"Loaded config: {file_path}")

    def _on_save_config(self) -> None:
        self._apply_ui_to_config()
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not file_path:
            return

        cfg = self.state_obj.config
        raw = {
            "input": {
                "input_path": str(cfg.input.input_path),
                "frame_start": cfg.input.frame_start,
                "frame_end": cfg.input.frame_end,
                "frame_step": cfg.input.frame_step,
                "backend": cfg.input.backend,
                "field_mapping": cfg.input.field_mapping,
            },
            "lookdev": {
                "density_gain": cfg.lookdev.density_gain,
                "density_bias": cfg.lookdev.density_bias,
                "opacity_gain": cfg.lookdev.opacity_gain,
                "opacity_gamma": cfg.lookdev.opacity_gamma,
                "exposure": cfg.lookdev.exposure,
                "scatter_color": list(cfg.lookdev.scatter_color),
                "emission_color": list(cfg.lookdev.emission_color),
            },
            "convert": {
                "sampling_mode": cfg.convert.sampling_mode,
                "density_threshold": cfg.convert.density_threshold,
                "scatter_scale": cfg.convert.scatter_scale,
                "scale_multiplier": cfg.convert.scale_multiplier,
                "generate_id": cfg.convert.generate_id,
                "random_seed": cfg.convert.random_seed,
            },
            "export": {
                "output_path": str(cfg.export.output_path),
                "export_sequence": cfg.export.export_sequence,
                "write_metadata": cfg.export.write_metadata,
                "write_debug_json": cfg.export.write_debug_json,
            },
            "fps": cfg.fps,
            "version": cfg.version,
        }
        Path(file_path).write_text(json.dumps(raw, indent=2), encoding="utf-8")
        self._log(f"Saved config: {file_path}")

    def _on_preview_frame(self) -> None:
        try:
            self._apply_ui_to_config()
            cfg = self.state_obj.config
            reader = VDBReader(cfg.input)
            src = reader.read_frame(cfg.input.frame_start)
            look = LookdevProcessor(cfg.lookdev).process(src)
            points = GSPointConverter(cfg.convert).convert(look)

            self.status_var.set(f"Preview frame {src.frame}: {points.P.shape[0]} points")
            self._log(
                f"Preview frame={src.frame}, density_shape={src.density.shape}, "
                f"points={points.P.shape[0]}, voxel_size={src.voxel_size}"
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Preview Failed", str(exc))

    def _on_export_sequence(self) -> None:
        try:
            self._apply_ui_to_config()
            cfg = self.state_obj.config
            reader = VDBReader(cfg.input)
            lookdev = LookdevProcessor(cfg.lookdev)
            converter = GSPointConverter(cfg.convert)
            exporter = UE5Exporter(cfg.export, cfg)

            source_frames = []
            point_counts: dict[int, int] = {}
            for frame in reader.frame_range():
                src = reader.read_frame(frame)
                source_frames.append(src)
                look = lookdev.process(src)
                points = converter.convert(look)
                out = exporter.export_frame(points)
                point_counts[frame] = int(points.P.shape[0])
                self._log(f"Exported frame {frame} -> {out} ({points.P.shape[0]} pts)")

            metadata = exporter.export_metadata(source_frames, point_counts)
            self.status_var.set("Export done")
            self._log(f"Metadata written: {metadata}")
            messagebox.showinfo("Export Complete", f"Export finished.\nMetadata: {metadata}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Export Failed", str(exc))

    def _apply_ui_to_config(self) -> None:
        cfg = self.state_obj.config

        cfg.input.input_path = Path(self.input_path_var.get())
        cfg.input.frame_start = int(self.frame_start_var.get())
        cfg.input.frame_end = int(self.frame_end_var.get())
        cfg.input.frame_step = int(self.frame_step_var.get())
        cfg.input.backend = self.backend_var.get()

        cfg.lookdev.density_gain = float(self.density_gain_var.get())
        cfg.lookdev.opacity_gain = float(self.opacity_gain_var.get())
        cfg.lookdev.opacity_gamma = float(self.opacity_gamma_var.get())
        cfg.lookdev.exposure = float(self.exposure_var.get())
        cfg.lookdev.scatter_color = self._parse_color(self.scatter_color_var.get())
        cfg.lookdev.emission_color = self._parse_color(self.emission_color_var.get())

        cfg.convert.sampling_mode = self.sampling_mode_var.get()
        cfg.convert.density_threshold = float(self.density_threshold_var.get())
        cfg.convert.scatter_scale = float(self.scatter_scale_var.get())
        cfg.convert.scale_multiplier = float(self.scale_multiplier_var.get())
        cfg.convert.generate_id = bool(self.generate_id_var.get())

        cfg.export.output_path = Path(self.output_path_var.get())
        cfg.export.write_metadata = bool(self.write_metadata_var.get())
        cfg.export.write_debug_json = bool(self.write_debug_json_var.get())

        cfg.fps = float(self.fps_var.get())

    def _refresh_ui_from_config(self) -> None:
        cfg = self.state_obj.config
        self.input_path_var.set(str(cfg.input.input_path))
        self.frame_start_var.set(cfg.input.frame_start)
        self.frame_end_var.set(cfg.input.frame_end)
        self.frame_step_var.set(cfg.input.frame_step)
        self.backend_var.set(cfg.input.backend)

        self.density_gain_var.set(cfg.lookdev.density_gain)
        self.opacity_gain_var.set(cfg.lookdev.opacity_gain)
        self.opacity_gamma_var.set(cfg.lookdev.opacity_gamma)
        self.exposure_var.set(cfg.lookdev.exposure)
        self.scatter_color_var.set(",".join(f"{v:.3g}" for v in cfg.lookdev.scatter_color))
        self.emission_color_var.set(",".join(f"{v:.3g}" for v in cfg.lookdev.emission_color))

        self.sampling_mode_var.set(cfg.convert.sampling_mode)
        self.density_threshold_var.set(cfg.convert.density_threshold)
        self.scatter_scale_var.set(cfg.convert.scatter_scale)
        self.scale_multiplier_var.set(cfg.convert.scale_multiplier)
        self.generate_id_var.set(cfg.convert.generate_id)

        self.output_path_var.set(str(cfg.export.output_path))
        self.fps_var.set(cfg.fps)
        self.write_metadata_var.set(cfg.export.write_metadata)
        self.write_debug_json_var.set(cfg.export.write_debug_json)

    def _parse_color(self, text: str) -> tuple[float, float, float]:
        parts = [float(x.strip()) for x in text.split(",")]
        if len(parts) != 3:
            raise ValueError("Color must be 3 comma-separated numbers")
        return (parts[0], parts[1], parts[2])

    def _log(self, text: str) -> None:
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)


def main() -> None:
    app = Pyro2GSApp()
    app.mainloop()


if __name__ == "__main__":
    main()
