# 使用例

AITuber Starter Kitの使用例です。

## 例一覧

| ディレクトリ | 説明 |
|-------------|------|
| basic/ | 基本的な使い方 |
| characters/ | キャラクター設定の例 |

## 基本的な使い方

### 1. シンプルな応答テスト

```python
import asyncio
from src.ai.openai_client import OpenAIClient
from src.ai.character import Character

async def main():
    # キャラクター読み込み
    character = Character.from_yaml("config/characters/default.yaml")

    # LLMクライアント作成
    client = OpenAIClient(model="gpt-4o-mini")
    client.set_character(character)

    # 応答生成
    response = await client.generate_response(
        "こんにちは！",
        context=[]
    )
    print(response)

asyncio.run(main())
```

### 2. 音声合成テスト

```python
import asyncio
from src.tts.voicevox import VoicevoxEngine
from src.utils.audio import AudioPlayer

async def main():
    # VOICEVOX初期化
    engine = VoicevoxEngine()
    player = AudioPlayer()

    # 音声合成
    audio = await engine.synthesize("こんにちは！", speaker_id=1)

    # 再生
    await player.play(audio.data)

asyncio.run(main())
```

### 3. フルパイプラインテスト

```python
import asyncio
from src.config import load_config
from src.main import create_pipeline

async def main():
    config = load_config()
    pipeline = await create_pipeline(config)

    # 手動で応答をテスト
    response = await pipeline.respond_to_text(
        "今日の調子はどう？",
        user_name="テストユーザー"
    )
    print(f"応答: {response}")

asyncio.run(main())
```

## キャラクター例

`examples/characters/` ディレクトリに様々なキャラクターテンプレートがあります。

- `genki.yaml` - 元気系キャラクター
- `cool.yaml` - クール系キャラクター
- `ojou.yaml` - お嬢様系キャラクター
