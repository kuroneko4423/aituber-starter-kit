# 上級者向けガイド

AITuber Starter Kitの高度な使い方やカスタマイズ方法を解説します。

## 目次

1. [アーキテクチャ概要](#アーキテクチャ概要)
2. [カスタムモジュールの作成](#カスタムモジュールの作成)
3. [プラグインシステム](#プラグインシステム)
4. [高度な設定](#高度な設定)
5. [パフォーマンスチューニング](#パフォーマンスチューニング)
6. [デバッグとログ](#デバッグとログ)
7. [APIの拡張](#apiの拡張)

---

## アーキテクチャ概要

### システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                     AITuber Pipeline                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ ChatClient  │───▶│   Comment   │───▶│  LLMClient  │    │
│  │ (YouTube/   │    │   Queue     │    │ (OpenAI/    │    │
│  │  Twitch)    │    │             │    │  Claude...) │    │
│  └─────────────┘    └─────────────┘    └──────┬──────┘    │
│                                               │            │
│                                               ▼            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   Avatar    │◀───│  LipSync    │◀───│  TTSEngine  │    │
│  │ Controller  │    │ Controller  │    │ (VOICEVOX   │    │
│  │ (VTube      │    │             │    │  etc.)      │    │
│  │  Studio)    │    └─────────────┘    └──────┬──────┘    │
│  └─────────────┘                              │            │
│         ▲                                     ▼            │
│         │              ┌─────────────┐  ┌─────────────┐   │
│         └──────────────│  Emotion    │◀─│   Audio     │   │
│                        │  Analyzer   │  │   Player    │   │
│                        └─────────────┘  └─────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 主要クラス

| クラス | 役割 |
|--------|------|
| `AITuberPipeline` | 全体のオーケストレーション |
| `BaseChatClient` | コメント取得の抽象基底クラス |
| `BaseLLMClient` | LLM連携の抽象基底クラス |
| `BaseTTSEngine` | 音声合成の抽象基底クラス |
| `BaseAvatarController` | アバター制御の抽象基底クラス |
| `EmotionAnalyzer` | 感情分析 |
| `LipSyncController` | リップシンク制御 |

---

## カスタムモジュールの作成

### カスタムChatClientの作成

新しい配信プラットフォームに対応する例：

```python
# src/chat/my_platform_chat.py
from .base import BaseChatClient
from .models import Comment, Platform

class MyPlatformChatClient(BaseChatClient):
    """カスタムプラットフォームのチャットクライアント"""

    def __init__(self, api_key: str, room_id: str):
        self.api_key = api_key
        self.room_id = room_id
        self._connected = False
        self._callback = None

    async def connect(self) -> None:
        """接続処理"""
        # WebSocket接続などを実装
        self._connected = True

    async def disconnect(self) -> None:
        """切断処理"""
        self._connected = False

    async def get_comments(self, limit: int = 10) -> list[Comment]:
        """コメント取得"""
        # APIからコメントを取得
        return []

    def on_comment(self, callback) -> None:
        """コールバック登録"""
        self._callback = callback

    @property
    def is_connected(self) -> bool:
        return self._connected
```

### カスタムLLMClientの作成

```python
# src/ai/my_llm_client.py
from .base import BaseLLMClient

class MyLLMClient(BaseLLMClient):
    """カスタムLLMクライアント"""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self._character = None

    def set_character(self, character) -> None:
        self._character = character

    async def generate_response(
        self,
        message: str,
        context: list[dict] = None,
    ) -> str:
        """応答生成"""
        # カスタムAPIを呼び出し
        system_prompt = self._character.to_system_prompt() if self._character else ""
        # ...
        return "応答テキスト"

    async def stream_response(self, message: str, context=None):
        """ストリーミング応答"""
        # ストリーミング対応の場合
        yield "応答"

    @property
    def provider_name(self) -> str:
        return "my_llm"

    @property
    def model_name(self) -> str:
        return self.model
```

### カスタムTTSEngineの作成

```python
# src/tts/my_tts_engine.py
from .base import BaseTTSEngine
from .models import AudioData, Speaker

class MyTTSEngine(BaseTTSEngine):
    """カスタムTTSエンジン"""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.speed = 1.0

    async def synthesize(
        self,
        text: str,
        speaker_id: int = None,
    ) -> bytes:
        """音声合成"""
        # APIを呼び出して音声データを取得
        return b""

    async def get_speakers(self) -> list[Speaker]:
        """話者一覧取得"""
        return [Speaker(id=0, name="Default", style="normal")]

    def set_speed(self, speed: float) -> None:
        self.speed = speed

    @property
    def engine_name(self) -> str:
        return "my_tts"
```

---

## プラグインシステム

### フックの実装

イベント発生時にカスタム処理を挿入：

```python
# カスタムフックの例
from src.pipeline import AITuberPipeline

class MyCustomPipeline(AITuberPipeline):
    """フック付きパイプライン"""

    async def on_comment_received(self, comment):
        """コメント受信時のフック"""
        # カスタム処理（ログ、フィルタリングなど）
        print(f"Comment received: {comment.message}")
        return comment  # 加工したコメントを返す

    async def on_response_generated(self, response):
        """応答生成後のフック"""
        # カスタム処理（ログ、修正など）
        return response

    async def on_audio_synthesized(self, audio):
        """音声合成後のフック"""
        # カスタム処理（エフェクト追加など）
        return audio

    async def _handle_comment(self, comment):
        """コメント処理のオーバーライド"""
        # フックを呼び出し
        comment = await self.on_comment_received(comment)
        if not comment:
            return  # フィルタリングされた場合

        # 親クラスの処理を呼び出し
        await super()._handle_comment(comment)
```

---

## 高度な設定

### 動的設定変更

実行中に設定を変更：

```python
# 設定の動的変更
pipeline.response_interval = 10.0  # 応答間隔を変更
pipeline.speaker_id = 2  # 話者を変更

# LLMの設定変更
pipeline.llm_client.temperature = 0.9
pipeline.llm_client.max_tokens = 200

# TTSの設定変更
pipeline.tts_engine.set_speed(1.5)
```

### 環境別設定

```python
# config/config_dev.yaml - 開発用
llm:
  provider: ollama
  model: llama3.1

# config/config_prod.yaml - 本番用
llm:
  provider: openai
  model: gpt-4o-mini
```

```bash
# 環境に応じて起動
python -m aituber --config config/config_dev.yaml
python -m aituber --config config/config_prod.yaml
```

---

## パフォーマンスチューニング

### 非同期処理の最適化

```python
import asyncio

# 並列処理の例
async def process_multiple_comments(comments):
    """複数コメントを並列処理"""
    tasks = [process_comment(c) for c in comments]
    results = await asyncio.gather(*tasks)
    return results
```

### メモリ管理

```python
# 会話履歴の制限
from src.ai.memory import ConversationMemory

memory = ConversationMemory(max_history=20)  # 最大20件

# 定期的なクリーンアップ
async def cleanup_memory():
    while True:
        await asyncio.sleep(3600)  # 1時間ごと
        memory.clear_old_messages()
```

### 接続プーリング

```python
import httpx

# 接続を再利用
client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(
        max_keepalive_connections=5,
        max_connections=10,
    ),
)
```

---

## デバッグとログ

### 詳細ログの有効化

```yaml
# config/config.yaml
logging:
  level: DEBUG
  file: logs/debug.log
```

### カスタムログフォーマット

```python
import logging

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler(),
    ]
)
```

### プロファイリング

```python
import cProfile
import pstats

# パフォーマンスプロファイリング
profiler = cProfile.Profile()
profiler.enable()

# ... 処理 ...

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

---

## APIの拡張

### REST APIの追加

```python
# api/server.py
from fastapi import FastAPI
from src.pipeline import AITuberPipeline

app = FastAPI()
pipeline: AITuberPipeline = None

@app.post("/api/respond")
async def manual_respond(text: str, user_name: str = "API"):
    """手動で応答を生成"""
    response = await pipeline.respond_to_text(text, user_name)
    return {"response": response}

@app.get("/api/status")
async def get_status():
    """ステータスを取得"""
    return {
        "running": pipeline.is_running,
        "queue_size": pipeline.comment_queue.size(),
    }

@app.post("/api/config")
async def update_config(interval: float = None, speaker_id: int = None):
    """設定を更新"""
    if interval:
        pipeline.response_interval = interval
    if speaker_id:
        pipeline.speaker_id = speaker_id
    return {"status": "updated"}
```

### WebSocket APIの追加

```python
# api/websocket.py
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # 処理
        await websocket.send_text(f"Response: {data}")
```

---

## デプロイメント

### Docker Composeでの運用

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  aituber:
    build: .
    restart: always
    env_file:
      - .env.prod
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    depends_on:
      - voicevox

  voicevox:
    image: voicevox/voicevox_engine:cpu-latest
    restart: always
    ports:
      - "50021:50021"

  redis:
    image: redis:7-alpine
    restart: always
```

### 監視とアラート

```python
# monitoring.py
import aiohttp

async def send_alert(message: str):
    """Discordにアラートを送信"""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json={"content": message})

async def monitor_pipeline(pipeline):
    """パイプラインを監視"""
    while True:
        if not pipeline.is_running:
            await send_alert("⚠️ Pipeline stopped!")
        await asyncio.sleep(60)
```

---

## ベストプラクティス

### 1. エラーハンドリング

```python
async def safe_process(comment):
    try:
        await process_comment(comment)
    except APIError as e:
        logger.error(f"API error: {e}")
        # リトライロジック
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        # アラート送信
```

### 2. テストの作成

```python
# tests/test_custom_module.py
import pytest
from src.chat.my_platform_chat import MyPlatformChatClient

@pytest.mark.asyncio
async def test_connect():
    client = MyPlatformChatClient("key", "room")
    await client.connect()
    assert client.is_connected
```

### 3. ドキュメントの整備

```python
class MyCustomClass:
    """
    カスタムクラスの説明

    Attributes:
        attr1: 属性1の説明
        attr2: 属性2の説明

    Example:
        >>> obj = MyCustomClass()
        >>> obj.method()
    """
```
