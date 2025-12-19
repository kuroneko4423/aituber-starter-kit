# はじめに

AITuber Starter Kitを使ってAITuberを始めるためのガイドです。

## 目次

1. [必要な環境](#必要な環境)
2. [インストール](#インストール)
3. [初期設定](#初期設定)
4. [起動方法](#起動方法)
5. [トラブルシューティング](#トラブルシューティング)

---

## 必要な環境

### ハードウェア要件

| 項目 | 最小要件 | 推奨 |
|------|---------|------|
| OS | Windows 10 / macOS 12 / Ubuntu 22.04 | Windows 11 / macOS 14 |
| メモリ | 8GB | 16GB以上 |
| ストレージ | 10GB以上 | SSD 20GB以上 |
| ネットワーク | 安定したインターネット接続 | 光回線推奨 |

### 必要なソフトウェア

| ソフトウェア | バージョン | 用途 | 必須/オプション |
|------------|----------|------|---------------|
| Python | 3.10以上 | メインプログラム実行 | 必須 |
| VOICEVOX | 最新版 | 音声合成 | 必須 |
| VTube Studio | 最新版 | アバター表示 | 必須 |
| OBS Studio | 最新版 | 配信 | 必須 |
| VB-Cable | - | 仮想オーディオ | 推奨 |

---

## インストール

### 1. Pythonのインストール

[Python公式サイト](https://www.python.org/downloads/)から Python 3.10以上をダウンロードしてインストールします。

```bash
# バージョン確認
python --version
# Python 3.10.x 以上であることを確認
```

### 2. プロジェクトのセットアップ

```bash
# リポジトリのクローン
git clone https://github.com/your-username/aituber-starter-kit.git
cd aituber-starter-kit

# 仮想環境の作成（推奨）
python -m venv venv

# 仮想環境の有効化
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. VOICEVOXのインストール

1. [VOICEVOX公式サイト](https://voicevox.hiroshiba.jp/)からダウンロード
2. インストーラーを実行
3. VOICEVOXを起動（デフォルトでポート50021で待機）

### 4. VTube Studioのセットアップ

1. [Steam](https://store.steampowered.com/app/1325860/VTube_Studio/)からVTube Studioをインストール
2. VTube Studioを起動
3. 設定 → 一般設定 → 「APIを起動する」を有効化
4. ポート8001で接続を許可

---

## 初期設定

### 1. 環境変数の設定

```bash
# テンプレートをコピー
cp .env.example .env

# .envファイルを編集
# OPENAI_API_KEY=sk-your-api-key-here
```

OpenAI APIキーは[OpenAIダッシュボード](https://platform.openai.com/api-keys)から取得できます。

### 2. 設定ファイルの編集

#### config/config.yaml

```yaml
# 配信プラットフォーム設定
platform:
  name: youtube
  video_id: "YOUR_VIDEO_ID_HERE"  # YouTube LiveのビデオID

# LLM設定
llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7

# TTS設定
tts:
  engine: voicevox
  speaker_id: 1  # 話者ID（VOICEVOXで確認）
  speed: 1.0

# アバター設定
avatar:
  enabled: true
```

#### config/characters/default.yaml

キャラクターの性格や話し方を設定します。詳細は[キャラクター設計ガイド](ai-config/character-design.md)を参照してください。

---

## 起動方法

### 1. 外部ソフトウェアを起動

1. **VOICEVOX**を起動
2. **VTube Studio**を起動し、モデルを読み込む
3. **OBS Studio**を起動し、配信設定を行う

### 2. AITuberを起動

```bash
# 仮想環境を有効化（まだの場合）
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 起動
python -m src.main

# または、オプション指定
python -m src.main --video-id YOUR_VIDEO_ID --debug
```

### 3. 動作確認

- コンソールに「AITuber pipeline started successfully!」と表示されれば成功
- YouTube Liveにコメントを投稿し、AIが応答することを確認

---

## トラブルシューティング

### VOICEVOXに接続できない

```
Error: VOICEVOX not available
```

**解決方法:**
1. VOICEVOXが起動しているか確認
2. ポート50021が使用されていないか確認
3. ファイアウォール設定を確認

### VTube Studioに接続できない

```
Error: Failed to connect to VTube Studio
```

**解決方法:**
1. VTube StudioでAPIが有効になっているか確認
2. ポート8001が正しいか確認
3. 初回接続時はVTube Studio側で認証を許可

### OpenAI APIエラー

```
Error: OpenAI API key not found
```

**解決方法:**
1. `.env`ファイルに`OPENAI_API_KEY`が設定されているか確認
2. APIキーが有効か確認
3. APIの利用制限を確認

### YouTube Liveに接続できない

```
Error: Failed to connect to YouTube chat
```

**解決方法:**
1. video_idが正しいか確認
2. 配信が「公開」または「限定公開」になっているか確認
3. インターネット接続を確認

---

## 次のステップ

- [モデリングガイド](modeling/README.md) - アバターの作成方法
- [配信ガイド](streaming/README.md) - OBSや各プラットフォームの設定
- [AI設定ガイド](ai-config/README.md) - キャラクター設計とプロンプト設計
