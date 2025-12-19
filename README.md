# AITuber Starter Kit

<p align="center">
  <strong>誰でもAITuberをプロデュースできるオープンソースキット</strong>
</p>

<p align="center">
  <a href="#特徴">特徴</a> •
  <a href="#クイックスタート">クイックスタート</a> •
  <a href="#ドキュメント">ドキュメント</a> •
  <a href="#設定">設定</a> •
  <a href="#貢献">貢献</a>
</p>

---

## 概要

AITuber Starter Kitは、AIを活用したバーチャルYouTuber（AITuber）を簡単に始められるツールキットです。配信プラットフォームからのコメント取得、AI応答生成、音声合成、アバター制御までの一連のパイプラインを提供します。

## 特徴

### 🎤 マルチプラットフォーム対応
- **YouTube Live** - pytchatによるリアルタイムコメント取得
- **Twitch** - twitchioによるIRC連携
- ニコニコ生放送（対応予定）

### 🤖 複数のLLMプロバイダー
- **OpenAI** - GPT-4o, GPT-4o-mini
- **Anthropic** - Claude 3.5 Sonnet, Claude 3 Haiku
- **Google** - Gemini 1.5 Pro, Gemini 1.5 Flash
- **Ollama** - Llama 3.1, Gemma 2など（ローカル実行）

### 🔊 多彩な音声合成エンジン
- **VOICEVOX** - 高品質な日本語音声
- **COEIROINK** - 商用利用可能
- **Style-Bert-VITS2** - 感情表現豊かな音声
- **にじボイス** - API経由の音声合成

### 🎭 アバター制御
- **VTube Studio** - Live2Dモデルのリップシンク・表情制御
- **感情分析** - テキストから感情を検出し自動で表情を変更

### 🖥️ Webダッシュボード

- **リアルタイム監視** - パイプライン状態、コメント、応答をリアルタイム表示
- **リモート制御** - ブラウザからパイプラインの開始/停止
- **設定変更** - 一部設定をライブで変更可能

### 🧠 長期記憶

- **SQLiteベース** - 会話履歴の永続化
- **ユーザープロファイル** - 視聴者情報の記録
- **コンテキスト検索** - 関連する過去の会話を自動取得（RAG）

## 必要な環境

| 項目 | 要件 |
|------|------|
| Python | 3.10以上 |
| OS | Windows 10/11, macOS 12+, Ubuntu 22.04+ |
| メモリ | 8GB以上（16GB推奨） |
| ストレージ | 10GB以上 |

### 必須ソフトウェア

- **VOICEVOX** - 音声合成エンジン（[ダウンロード](https://voicevox.hiroshiba.jp/)）
- **VTube Studio** - アバター表示（[Steam](https://store.steampowered.com/app/1325860/VTube_Studio/)）
- **OBS Studio** - 配信ソフト（[ダウンロード](https://obsproject.com/)）

## クイックスタート

### 1. インストール

```bash
# リポジトリのクローン
git clone https://github.com/your-username/aituber-starter-kit.git
cd aituber-starter-kit

# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -e .
```

### 2. 環境変数の設定

```bash
# .envファイルを作成
cp .env.example .env

# 必要なAPIキーを設定
# エディタで.envを開いて編集
```

**.env の設定例:**
```env
# LLM API (いずれか1つは必須)
OPENAI_API_KEY=sk-your-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_API_KEY=your-google-key

# 配信プラットフォーム (Twitch使用時)
TWITCH_ACCESS_TOKEN=oauth:your-token
```

### 3. 設定ファイルの編集

`config/config.yaml` を編集：

```yaml
platform:
  name: youtube
  video_id: "YOUR_VIDEO_ID_HERE"  # YouTube Live の動画ID

llm:
  provider: openai
  model: gpt-4o-mini
```

### 4. 外部ソフトウェアの起動

1. **VOICEVOX**を起動（ポート50021）
2. **VTube Studio**を起動
   - 設定 → API → APIを有効化
   - ポート: 8001

### 5. 実行

```bash
python -m aituber
```

## ドキュメント

詳細なドキュメントは `docs/ja/` にあります：

| ドキュメント | 内容 |
|-------------|------|
| [getting-started.md](docs/ja/getting-started.md) | 導入ガイド |
| [faq.md](docs/ja/faq.md) | よくある質問 |
| [troubleshooting.md](docs/ja/troubleshooting.md) | トラブルシューティング |
| [advanced-usage.md](docs/ja/advanced-usage.md) | 上級者向けガイド |

### モデリング
- [Live2Dガイド](docs/ja/modeling/live2d-guide.md)
- [VRMガイド](docs/ja/modeling/vrm-guide.md)
- [アバターセットアップ](docs/ja/modeling/avatar-setup.md)

### 配信設定
- [OBS設定](docs/ja/streaming/obs-setup.md)
- [YouTube Live設定](docs/ja/streaming/youtube-live.md)
- [Twitch設定](docs/ja/streaming/twitch-setup.md)
- [マルチプラットフォーム](docs/ja/streaming/multi-platform.md)

### AI設定
- [キャラクター設計](docs/ja/ai-config/character-design.md)
- [プロンプト設計](docs/ja/ai-config/prompt-engineering.md)
- [API設定](docs/ja/ai-config/api-setup.md)
- [LLM比較](docs/ja/ai-config/llm-comparison.md)

## 設定

### メイン設定 (`config/config.yaml`)

```yaml
# プラットフォーム
platform:
  name: youtube  # youtube / twitch
  video_id: "xxx"

# LLM
llm:
  provider: openai  # openai / anthropic / google / ollama
  model: gpt-4o-mini
  temperature: 0.7

# 音声合成
tts:
  engine: voicevox  # voicevox / coeiroink / style_bert_vits / nijivoice
  speaker_id: 1
  speed: 1.0

# アバター
avatar:
  enabled: true
  host: localhost
  port: 8001

# 感情分析
expression:
  enabled: true
  analyze_emotion: true
```

### キャラクター設定 (`config/characters/default.yaml`)

```yaml
name: "アイちゃん"
personality: |
  明るく元気な性格で、視聴者との会話を楽しむことが大好き。
speaking_style:
  first_person: "私"
  sentence_endings:
    - "〜だよ！"
    - "〜なの！"
```

サンプルキャラクターは `examples/characters/` にあります。

## プロジェクト構成

```
aituber-starter-kit/
├── src/                    # ソースコード
│   ├── chat/               # コメント取得
│   ├── ai/                 # AI応答生成
│   ├── tts/                # 音声合成
│   ├── avatar/             # アバター制御
│   ├── expression/         # 感情分析・リップシンク
│   ├── dashboard/          # Webダッシュボード
│   ├── memory/             # 長期記憶システム
│   └── utils/              # ユーティリティ
├── config/                 # 設定ファイル
├── docs/                   # ドキュメント
├── examples/               # サンプル
├── tests/                  # テスト
└── scripts/                # スクリプト
```

## 開発ロードマップ

- [x] **Phase 1**: MVP - 基本パイプライン
- [x] **Phase 2**: 機能拡張 - マルチLLM/TTS対応
- [x] **Phase 3**: ドキュメント整備
- [x] **Phase 4**: Webダッシュボード、長期記憶

## 貢献

プルリクエストやイシューは大歓迎です！

### 開発環境のセットアップ

```bash
# 開発用依存関係のインストール
pip install -e ".[dev]"

# テストの実行
pytest

# リンターの実行
ruff check src/
```

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。

## 謝辞

- [VOICEVOX](https://voicevox.hiroshiba.jp/)
- [VTube Studio](https://denchisoft.com/)
- [pytchat](https://github.com/taizan-hokuto/pytchat)
- [pyvts](https://github.com/Genteki/pyvts)

---

<p align="center">
  Made with ❤️ by the AITuber Community
</p>
