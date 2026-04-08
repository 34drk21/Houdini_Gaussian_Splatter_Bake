# Houdini_Gaussian_Splatter_Bake

HoudiniのPyroボリュームをLookdev済みの見た目でGaussian Splat用ポイントに変換し、UE5向けに出力するためのスタンドアロンPythonツールです。

## Documents

- [仕様書 v0.1 (日本語)](docs/spec_v0.1_ja.md)

## Standalone Tool (Python)

### セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

`pyopenvdb` が利用できる環境では `--backend pyopenvdb` 相当の設定で `.vdb` を直接読み込みできます。
MVPとしては `.npz` 入力バックエンドも同梱しており、CIやローカル検証に使えます。

### 入力フォーマット（npzバックエンド）

`frame_0001.npz` のような連番ファイルを入力ディレクトリに配置します。

必須キー:
- `density` (`float32[z,y,x]`)

任意キー:
- `flame` (`float32[z,y,x]`)
- `temperature` (`float32[z,y,x]`)
- `vel` (`float32[z,y,x,3]`)
- `voxel_size` (`float32`)

### 実行

```bash
pyro2gs --config config.json
```

設定ファイル例:

```json
{
  "input": {
    "input_path": "./input_npz",
    "frame_start": 1,
    "frame_end": 24,
    "backend": "npz",
    "field_mapping": {
      "density": "density",
      "flame": "flame",
      "temperature": "temperature",
      "vel": "vel"
    }
  },
  "lookdev": {
    "density_gain": 1.2,
    "opacity_gain": 1.1,
    "opacity_gamma": 1.2,
    "exposure": 0.5,
    "scatter_color": [0.8, 0.8, 0.85],
    "emission_color": [1.0, 0.4, 0.1]
  },
  "convert": {
    "sampling_mode": "voxel_center",
    "density_threshold": 0.02,
    "scale_multiplier": 1.0,
    "generate_id": true
  },
  "export": {
    "output_path": "./out",
    "write_metadata": true,
    "write_debug_json": false
  },
  "fps": 24.0,
  "version": "0.1"
}
```

### 出力

- `gs_points_####.npz`
  - `P`, `f_dc`, `opacity`, `scale`, `rot`, `id`（必要なら `vel`）
- `metadata.json`
  - `frame_range`, `fps`, `bbox`, `voxel_size`, `point_count_per_frame`, `export_version` など

## Tests

```bash
pytest -q
```
