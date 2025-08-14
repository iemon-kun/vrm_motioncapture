# vrm_motioncapture
## VRMベース OSC/VMC トラッキング送信アプリ 詳細仕様書（拡張版）

## アプリ概要
ローカルカメラ映像から姿勢・表情を推定し、参照VRMファイルを読み込んでアバターのHumanoidボーンおよびExpression（BlendShape）定義に基づき、送信可能な情報のみを選定してLAN経由でcluster等にOSC送信するGUIアプリ。  
加えて、VMCプロトコル出力・手指トラッキング・肩すくめ・視線安定化・iPhone Perfect Sync受け入れ・収録＆リプレイ・プレビュー映像出力を実装。

---

## 技術スタック詳細
**フロント（UI）**:  
- React Native × Expo (TypeScript)
- 状態管理: Zustand
- 通信: REST/WebSocket
- プレビュー: three.js + three-vrm（PC優先）

**バックエンド（推論・送信エンジン）**:  
- Python 3.11+, FastAPI + uvicorn
- OpenCV, MediaPipe (Pose, FaceMesh, Hands, SelfieSegmentation)
- NumPy（ベクトル・クォータニオン計算）
- python-osc（OSC/VMC送信）
- pygltflib（VRM/glTF解析）
- SQLite（SQLAlchemy/peewee）
- （iPhone PS受信用）WebSocket/TCPリスナー

**対応プロトコル**:
- OSC（cluster向け, 任意のPrefix）
- VMC（VMC Protocol 1.1系 `/VMC/Ext/*`）

---

## DBスキーマ（差分含む）

```sql
CREATE TABLE app_settings (
  id INTEGER PRIMARY KEY CHECK (id=1),
  auth_token TEXT NOT NULL,
  engine_http_port INTEGER NOT NULL DEFAULT 8800
);

CREATE TABLE osc_targets (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  protocol TEXT NOT NULL CHECK (protocol IN ('OSC','VMC')),
  host TEXT NOT NULL,
  port INTEGER NOT NULL,
  path_prefix TEXT DEFAULT '/ps',  -- OSC時のみ
  send_rate_hz INTEGER NOT NULL DEFAULT 30,
  UNIQUE(host, port, protocol)
);

CREATE TABLE camera_sources (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('DEVICE','RTSP','FILE')),
  label TEXT NOT NULL,
  device_index INTEGER,
  url TEXT,
  width INTEGER, height INTEGER, fps INTEGER,
  enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE vrm_models (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  version TEXT,
  path TEXT NOT NULL,
  humanoid_json TEXT NOT NULL,
  expressions_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE pipelines (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  camera_id TEXT NOT NULL REFERENCES camera_sources(id) ON DELETE CASCADE,
  osc_target_id TEXT NOT NULL REFERENCES osc_targets(id) ON DELETE CASCADE,
  vrm_id TEXT NOT NULL REFERENCES vrm_models(id) ON DELETE RESTRICT,
  pose_enabled INTEGER NOT NULL DEFAULT 1,
  face_enabled INTEGER NOT NULL DEFAULT 1,
  hands_enabled INTEGER NOT NULL DEFAULT 0,         -- ★手指
  shrug_enabled INTEGER NOT NULL DEFAULT 0,         -- ★肩すくめ
  gaze_enabled INTEGER NOT NULL DEFAULT 0,          -- ★視線
  smoothing_alpha REAL NOT NULL DEFAULT 0.7,
  scale REAL NOT NULL DEFAULT 1.0,
  active INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE tx_channels (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pipeline_id TEXT NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK (kind IN ('BONE','BLENDSHAPE')),
  name TEXT NOT NULL,
  source TEXT NOT NULL,
  map_expr TEXT,
  enabled INTEGER NOT NULL DEFAULT 1,
  UNIQUE(pipeline_id, kind, name)
);

CREATE TABLE export_jobs (
  id TEXT PRIMARY KEY,
  pipeline_id TEXT NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
  fmt TEXT NOT NULL CHECK(fmt IN ('jsonl','csv')),
  path TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE replays (  -- ★収録ファイル管理
  id TEXT PRIMARY KEY,
  pipeline_id TEXT NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  duration_sec REAL NOT NULL
);
````

---

## 機能仕様（追加・更新点）

### 出力プロトコル選択

* Pipeline単位でOSCまたはVMCを選択
* OSC時: `/ps/...`形式（Bone/BlendShape/指/肩）
* VMC時: `/VMC/Ext/Bone/Pos`, `/VMC/Ext/Blend/Val`, `/VMC/Ext/Root/Pos`等、必要最小限実装

### 手指トラッキング（MediaPipe Hands）

* VRMにFingerボーンが存在する場合のみ送信
* 送信形式:

  * OSC: `/ps/bone/{FingerName}/rot` float\[4]
  * VMC: `/VMC/Ext/Bone/Pos`に含める
* 21ランドマーク→ボーン回転推定、左右両手

### 肩すくめ検出

* Poseランドマーク（肩峰・首基部）から高さ差分とロール角で推定
* VRMに肩Exprやボーンがあればマッピング、無ければスキップ

### 視線安定化

* FaceMeshから瞳ランドマーク重心を取得
* One Euroフィルタ + EMA複合で滑らかに
* 出力:

  * OSC: `/ps/eyes/{left|right}` float\[2] yaw,pitch
  * VMC: `/VMC/Ext/Blend/Val`のgaze系にマッピング

### iPhone Perfect Sync受信

* 外部（iFacialMocap等）からのWebSocket/TCPでARKit52値受信
* VRMマッピングを適用し、OSC/VMC送信ループに統合
* UIで受信ポート指定

### 収録＆リプレイ

* 任意のPipeline送信データをJSONL/CSV形式で保存
* 再生時はカメラ入力をバイパスし、記録ファイルから再生
* 送信先は通常と同様

### プレビュー映像出力

* three-vrmで参照VRMを描画し、推定姿勢・表情を適用
* WebRTC/NDI/OBS仮想カメラへの出力オプション（段階実装）

---

## UI/UX構成（更新）

### Dashboard

* Pipelineごとに出力プロトコル・送信先を表示
* 「収録開始/停止」「リプレイ」ボタン

### VRM管理

* VRMインポート＆能力表示
* Txチャンネル自動生成

### Pipeline Editor

* 機能ON/OFF（Pose/Face/Hands/Shrug/Gaze/iPhonePS）
* 出力プロトコル選択
* キャリブレーション

### Preview

* three-vrmでのリアルタイム表示
* 出力プレビュー（OSC/VMC送信内容の可視化）

---

## モジュール分割（追加）

**Python**

```
track/hands.py           # 手指推定
features/shrug.py        # 肩すくめ推定
features/gaze.py         # 視線安定化
net/iphone_ps_server.py  # iPhone PS受信
osc/vmc_sender.py        # VMCプロトコル送信
svc/recorder.py          # 収録
svc/replay.py            # 再生
render/preview.py        # three-vrm連携用API（将来）
```

---

## APIシグネチャ（追加）

```
PUT  /api/pipelines/{id}/protocol     # OSC/VMC切替
PUT  /api/pipelines/{id}/features     # hands/shrug/gaze/iphonePS ON/OFF
POST /api/record/{id}/start
POST /api/record/{id}/stop
POST /api/replay/{id}/start
POST /api/replay/{id}/stop
```

---

## 実装タスク分解（追加分）

1. VMC送信モジュール作成（/VMC/Ext/\*）
2. MediaPipe Hands実装＋VRM指ボーン対応表作成
3. 肩すくめ推定
4. 視線安定化（One Euro + EMA）
5. iPhone PS受信サーバ
6. 収録・リプレイ機能
7. three-vrmプレビュー描画（PC優先）

---

## 受け入れ基準（MVP+拡張）

* PipelineでOSC/VMCを切替できる
* 手指ON時、VRMに指ボーンがあれば送信される
* 肩すくめON時、肩動作が推定・送信される
* 視線ON時、目線が安定して出力される
* iPhone PS受信時、受信値がVRMマッピングされ送信される
* 収録したデータをリプレイし、同じ出力が再現される

```

---
