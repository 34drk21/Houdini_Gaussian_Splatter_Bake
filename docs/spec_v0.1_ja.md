# Houdini Pyro → Lookdev → Gaussian Splat → UE5 変換ツール 仕様書

- ドキュメントバージョン: v0.1
- 作成日: 2026-04-09
- 想定環境: Houdini / UE5
- 目的: Houdiniで作成したPyroシミュレーションを、独自VDB表示ツール内でルックデブし、その見た目を保持したままGaussian Splatting用ポイントデータへ変換し、UE5で再生可能な形式へ出力する。

## 1. 概要

本ツールは、Houdiniで生成したPyroシミュレーションデータ（VDB）を入力とし、独自VDB表示ツール上でPyro Bake相当のルックデブを行い、その結果をGaussian Splatting向けのポイント群へ変換、さらにUE5用データへエクスポートする一連のワークフローを提供する。

本ツールの主眼は以下の3点である。

- Pyroの見た目をHoudini上で確定できること
- その見た目を維持したまま点群化できること
- UE5で軽量かつ実用的に再生できること

本ツールは、シミュレーション、ルックデブ、ゲーム用変換を明確に分離することで、調整と再利用を容易にする。

## 2. 目的

### 2.1 主目的

- HoudiniのPyro sim結果を、最終見た目ベースでゲーム向けデータへ変換する
- 既存のVDB表示ツールを、単なるプレビュー用途ではなく、最終出力の基準となるルックデブ環境として機能させる
- UE5上で再利用可能な独自Gaussian Splat表現の中間資産を作る

### 2.2 副目的

- Pyroのボリューム表現をそのまま持ち込むのではなく、ゲーム用途向けに圧縮・軽量化する
- 将来的にVATライクなデータ構造やNiagara再生にも発展可能な設計にする
- Houdini内でのデバッグ性と可視性を高める

## 3. 対象範囲

### 3.1 本仕様書の対象

- Houdini内の入力、ルックデブ、点群変換、属性設計、エクスポート
- UE5用出力形式の定義
- MVP実装に必要な機能
- 将来的な拡張のための前提設計

### 3.2 対象外

- UE5側の最終レンダラー実装詳細
- 既存Gaussian Splattingプラグインへの完全対応保証
- ネットワーク配信やストリーミング最適化の詳細実装
- モバイル最適化

## 4. 想定ユーザー

- Houdiniを用いてPyro simを制作するFXアーティスト
- Houdiniベースでゲーム向けエフェクト変換を行うTA
- 映画品質寄りのルックをゲームエンジンへ持ち込みたいVFX/リアルタイム開発者

## 5. 用語定義

### 5.1 Pyro sim

Houdiniで生成された煙、炎、爆発などのボリュームシミュレーション。

### 5.2 VDB表示ツール

Pyro sim結果を独自に可視化・調整するためのボリューム表示ツール。Pyro Bake相当のルックデブ機能を持つことを想定。

### 5.3 Lookdev

色、発光、不透明度、密度の見え方など、最終表示のための調整工程。

### 5.4 Gaussian Splatting用ポイント

位置・色・不透明度・スケール・回転などを保持するポイント群。UE5内でGaussian的な描画に用いる。

### 5.5 UE5向け変換

Gaussian Splat用ポイントを、UE5内の独自描画、Niagara、または将来的なカスタムプラグイン向けに利用できる形式へ変換すること。

## 6. システム全体構成

本ツールは以下の4モジュールで構成される。

- Pyro Input / Cache
- VDB Lookdev
- GS Point Convert
- UE5 Export

処理フローは以下の通り。

```text
Pyro sim (VDB)
→ フィールド正規化
→ VDB Lookdev
→ 最終色・最終Opacity生成
→ ポイント化
→ GS属性付与
→ UE5形式へ出力
```

## 7. 機能要件

### 7.1 Pyro Input / Cache モジュール

#### 7.1.1 目的

Pyro sim由来の各VDBフィールドを受け取り、内部処理に適した共通形式へ正規化する。

#### 7.1.2 入力

- density
- flame
- temperature
- vel
- 任意追加フィールド（Cd, emissive mask等）

#### 7.1.3 機能

- 入力VDBの読み込み
- フィールド名マッピング
- フレーム範囲取得
- bbox取得
- voxel size取得
- 欠損フィールドの補完
- キャッシュ管理

#### 7.1.4 要件

- density単体でも最低限動作すること
- flameやtemperatureが無い場合でもエラーで停止せず、代替処理すること
- フィールド名が異なっていても手動マッピングで対応可能であること
- フレームごとのキャッシュ再利用が可能であること

#### 7.1.5 出力

- 正規化済みVDBセット
- メタデータ
  - frame
  - bbox
  - voxel size
  - source path

### 7.2 VDB Lookdev モジュール

#### 7.2.1 目的

Pyro Bake相当のルックデブを独自ツール上で行い、最終的な見た目を決定する。

#### 7.2.2 主な機能

- density remap
- flame / temperature remap
- scatter color制御
- emission color制御
- opacity shaping
- intensity / exposure調整
- rampベースの色・不透明度調整
- 各種プレビュー表示

#### 7.2.3 内部中間フィールド

- density_shaped
- flame_mask
- temperature_mask
- Cd_scatter
- Cd_emit
- opacity_raw
- opacity_final
- Cd_final

#### 7.2.4 最終出力フィールド

- Cd_final
- opacity_final

#### 7.2.5 要件

- VDB表示上の最終見た目が、その後の点群変換結果の基準となること
- Pyro sim元データとルックデブ結果を切り替えて比較表示できること
- 最終色と最終Opacityを明示的に可視化できること
- 将来的にemissionとscatterを別出力可能な余地を残すこと

#### 7.2.6 表示モード

- raw density
- shaped density
- flame
- temperature
- final color
- final opacity
- combined preview

### 7.3 GS Point Convert モジュール

#### 7.3.1 目的

ルックデブ済みVDBから、Gaussian Splatting向けポイント群を生成する。

#### 7.3.2 入力

- VDB density系
- Cd_final
- opacity_final
- 必要に応じてvel

#### 7.3.3 処理内容

- ボリューム内サンプリング
- 閾値以下の領域の除去
- densityに応じたポイント生成密度制御
- 各ポイントへの色・opacity・scale・rotation付与
- 必要に応じたID割り当て

#### 7.3.4 サンプリングモード

- **Voxel Center Sampling**: ボクセル中心に点を生成（実装が単純でデバッグしやすい）
- **Density Scatter Sampling**: densityに応じて散布密度を変える（見た目効率が高い）
- **Adaptive Sampling**: densityやgradientに応じて点密度を最適化（将来拡張用）

#### 7.3.5 ポイント属性

- P
- v
- f@density_sample
- v@Cd_final
- f@opacity_final
- v@scale_final
- p@orient_final
- i@id

#### 7.3.6 エクスポート用属性

- P
- v@f_dc
- f@opacity
- v@scale
- p@rot
- i@id

必要に応じて以下も保持可能。

- f[]@f_rest
- v@vel
- i@alive
- f@age

#### 7.3.7 要件

- 最低限、単フレームを安定して点群化できること
- 点群化結果をHoudiniビューポート上で確認できること
- 点数の増減をパラメータで制御できること
- 点スケール・不透明度・色の分布を可視化できること

### 7.4 Scale / Rotation 推定

#### 7.4.1 目的

各ポイントをGaussianらしい見え方にするための形状パラメータを定義する。

#### 7.4.2 MVP仕様

- scale: voxel sizeベースの等方スケール
- rotation: identity quaternion

#### 7.4.3 拡張仕様

- velocity方向に伸ばす異方スケール
- gradient方向に基づく向き推定
- 近傍点PCAによる主軸推定

#### 7.4.4 要件

- 初期版は実装の安定性を優先し、複雑な回転推定を必須としない
- scale multiplier調整が可能であること
- 将来的にanisotropic対応できるデータ構造を持つこと

### 7.5 UE5 Export モジュール

#### 7.5.1 目的

生成されたGSポイントをUE5で再生可能な形式へ出力する。

#### 7.5.2 MVP出力形式

- BGEO Sequence
- Custom Binary Sequence
- JSON Metadata

#### 7.5.3 将来的な出力形式

- texture baked animation
- VATライク属性テクスチャ
- UE5 plugin専用形式
- USD Point Instancer互換

#### 7.5.4 出力内容

各フレームごとに以下を含む。

- point count
- positions
- colors / f_dc
- opacity
- scale
- rotation
- optional velocity
- metadata

#### 7.5.5 メタデータ

- frame range
- fps
- bbox
- voxel size
- point count per frame
- source sim info
- export version

#### 7.5.6 要件

- 単フレーム / シーケンス両対応
- フレーム番号付き出力
- UE側で解釈しやすい命名ルールを持つこと
- バージョン情報を含めること

## 8. 非機能要件

### 8.1 再現性

同一入力・同一パラメータなら同一出力を得られること。

### 8.2 可視性

各工程で可視化デバッグが可能であること。

### 8.3 拡張性

MVPでは簡易実装でも、将来的に

- temporal tracking
- texture baking
- true GS対応

へ拡張できる構造であること。

### 8.4 パフォーマンス

- 単フレーム点群化が実用時間内で終わること
- 高密度ボリュームでも閾値やサンプリング制御で削減可能であること

### 8.5 保守性

- モジュールごとに責務を分離すること
- lookdevとexportを密結合しすぎないこと

## 9. UI仕様

### 9.1 タブ構成

- **Tab 1: Sim Input**
  - input path
  - field mapping
  - frame range
  - cache mode
  - bbox info
  - voxel size info
- **Tab 2: Lookdev**
  - density remap
  - flame remap
  - temperature remap
  - scatter color ramp
  - emission ramp
  - opacity shaping
  - exposure / gain
  - preview mode switch
- **Tab 3: GS Convert**
  - sampling mode
  - density threshold
  - point count target
  - scale multiplier
  - rotation mode
  - id generation on/off
  - preview density / color / opacity / scale
- **Tab 4: Export**
  - output path
  - output format
  - frame range
  - sequence export on/off
  - metadata export on/off
  - debug export on/off

### 9.2 ビューポート表示モード

- source volume
- final volume preview
- generated points
- point color
- point opacity
- point scale
- point id
- export preview

## 10. データ仕様

### 10.1 内部属性仕様

| 属性名 | 型 | 用途 |
|---|---|---|
| P | vector3 | ポイント位置 |
| v | vector3 | 速度 |
| density_sample | float | densityサンプル値 |
| Cd_final | vector3 | 最終色 |
| opacity_final | float | 最終opacity |
| scale_final | vector3 | 内部スケール |
| orient_final | quaternion | 内部回転 |
| id | int | ポイントID |

### 10.2 エクスポート属性仕様

| 属性名 | 型 | 用途 |
|---|---|---|
| P | vector3 | 位置 |
| f_dc | vector3 | Gaussian DCカラー |
| opacity | float | 不透明度 |
| scale | vector3 | Gaussianスケール |
| rot | quaternion | Gaussian回転 |
| id | int | 識別子 |

## 11. 処理フロー

### 11.1 単フレーム処理

1. VDB読み込み
2. フィールド正規化
3. Lookdev適用
4. 最終色・最終Opacity生成
5. VDBからポイント生成
6. scale / rot付与
7. エクスポート属性へ変換
8. 出力

### 11.2 シーケンス処理

1. フレーム範囲ループ
2. 各フレームに対し単フレーム処理を実行
3. メタデータ集約
4. 連番出力

## 12. MVP定義

### 必須

- density/flame/temperature/vel読み込み
- field mapping
- VDB lookdev
- final color / opacity生成
- voxel center or density scatterでの点群化
- 等方scale
- identity rotation
- bgeo/custom binary sequence出力
- JSON metadata出力
- Houdini内プレビュー

### 非必須

- temporal point tracking
- texture bake
- anisotropic scale推定
- SH高次係数対応
- true GS plugin向け完全対応

## 13. 将来拡張

### 13.1 Temporal Tracking

フレーム間で点IDを維持し、固定点数データとして扱えるようにする。

### 13.2 Texture Bake

位置、色、opacity、scale、rotationをテクスチャへ焼き、UE5側でGPU再構築する。

### 13.3 LOD生成

距離や重要度に応じて点数を削減する。

### 13.4 Hybrid Renderer

Gaussian Splatそのものではなく、Niagaraやquad rendererとのハイブリッド表現にも対応する。

### 13.5 Plugin Preset

出力先プラグインごとの属性フォーマットプリセットを追加する。

## 14. 技術的前提と方針

### 14.1 基本方針

本ツールは「シミュレーション結果をそのまま運ぶ」のではなく、「見た目を焼いた結果を運ぶ」思想を採用する。

### 14.2 理由

- UE側でHoudiniと同じPyro shading再現が困難
- 見た目をHoudini側で固定した方が品質保証しやすい
- 調整責任範囲が明確になる

### 14.3 描画戦略

MVP段階では、UE側では厳密なGaussian Splat再生よりも、まずは以下で成立する構造を優先する。

- custom point renderer
- Niagara
- billboard / quad近似

## 15. 想定リスク

### 15.1 見た目差異

Houdini上のVDB表示とUE側の点表示で見え方がズレる可能性がある。

**対策:** final color / opacityを明示的に焼き、同一値を使う。

### 15.2 データ量増大

フレームごとに点群を持つと容量が増える。

**対策:** MVPでは許容し、後でtrackingやtexture化で対応する。

### 15.3 点のちらつき

フレームごとに独立サンプリングすると安定しない。

**対策:** MVPでは許容。将来的にID追跡を導入する。

### 15.4 変換コスト

高解像度Pyroでは点群生成が重くなる。

**対策:** threshold, adaptive sampling, decimationを用意する。

## 16. 開発優先順位

- **Phase 1:** 単フレーム入力 / lookdev / 点群化 / Houdiniプレビュー
- **Phase 2:** シーケンス対応 / export / metadata
- **Phase 3:** UE5再生テスト / 表示調整 / debug強化
- **Phase 4:** temporal tracking / texture bake / 最適化

## 17. 成功条件

本ツールの初期成功条件は以下とする。

- HoudiniでPyro simを読み込める
- 独自VDB表示ツールで見た目を作れる
- その見た目を維持したポイント群を生成できる
- UE5で再生確認できる
- 少なくとも単フレームおよび短尺シーケンスで成立する

## 18. 補足: 実装ポリシー

- まずは正確さより「破綻しない流れ」を優先する
- ルックデブ結果を基準データとして扱う
- true GSに縛られず、ゲーム向け実装として成立する設計を優先する
- デバッグ可視化を最初から組み込む
