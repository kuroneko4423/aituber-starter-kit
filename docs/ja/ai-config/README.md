# AI設定ガイド

AITuberのAI設定に関するガイドです。

## 目次

1. [概要](#概要)
2. [LLM設定](#llm設定)
3. [キャラクター設計](#キャラクター設計)
4. [プロンプト設計](#プロンプト設計)
5. [関連ドキュメント](#関連ドキュメント)

---

## 概要

AITuber Starter Kitでは、以下のAI関連設定が可能です：

| 設定項目 | 説明 | 設定ファイル |
|---------|------|-------------|
| LLMプロバイダー | 使用するAIサービス | config/config.yaml |
| モデル | 使用するモデル名 | config/config.yaml |
| キャラクター | 性格・話し方 | config/characters/*.yaml |
| 応答設定 | 応答の長さ・スタイル | config/config.yaml |

---

## LLM設定

### 対応プロバイダー

| プロバイダー | 対応状況 | 特徴 |
|------------|---------|------|
| OpenAI | ✅ 対応 | GPT-4o, GPT-4o-mini |
| Anthropic | 🔜 予定 | Claude 3.5 Sonnet |
| Google | 🔜 予定 | Gemini 1.5 Pro |
| Ollama | 🔜 予定 | ローカルLLM |

### config/config.yaml

```yaml
llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 150
```

### パラメータ説明

| パラメータ | 説明 | 推奨値 |
|-----------|------|--------|
| provider | LLMプロバイダー | openai |
| model | モデル名 | gpt-4o-mini |
| temperature | 創造性（0.0-2.0） | 0.7 |
| max_tokens | 最大応答トークン数 | 150 |

### temperatureの選び方

| 値 | 特徴 | 用途 |
|----|------|------|
| 0.0-0.3 | 一貫性重視 | 情報提供系 |
| 0.4-0.7 | バランス | 一般的な雑談 |
| 0.8-1.2 | 創造性重視 | エンタメ系 |
| 1.3-2.0 | ランダム性高 | 実験的 |

---

## キャラクター設計

### 基本構成

キャラクター設定ファイル（config/characters/default.yaml）：

```yaml
# 基本情報
name: "キャラクター名"
age: 17
gender: "女性"

# 性格
personality: |
  性格の詳細説明...

# 話し方
speaking_style:
  first_person: "私"
  second_person: "あなた"
  sentence_endings:
    - "〜だよ！"
    - "〜なの！"

# 背景設定
background: |
  キャラクターの背景ストーリー...

# 禁止事項
restrictions:
  - 政治的な話題には触れない
  - ...

# 会話例
example_dialogues:
  - user: "こんにちは！"
    assistant: "やっほー！来てくれて嬉しいな！"
```

### 効果的なキャラクター設計

詳細は [character-design.md](character-design.md) を参照

**ポイント:**
1. 一貫した性格設定
2. 明確な話し方のルール
3. 具体的な会話例
4. 適切な禁止事項

---

## プロンプト設計

### システムプロンプトの構造

AITuber Starter Kitでは、キャラクター設定から自動的にシステムプロンプトが生成されます：

```
あなたは「{name}」というAITuberとして振る舞ってください。

【基本情報】
名前: {name}
年齢: {age}歳
性別: {gender}

【性格】
{personality}

【話し方】
一人称: {first_person}
二人称: {second_person}
語尾の例: {sentence_endings}

【背景設定】
{background}

【禁止事項】
{restrictions}

【会話例】
{example_dialogues}

【応答ルール】
- 視聴者からのコメントに対して自然に応答してください
- 応答は簡潔に（1-3文程度）してください
- キャラクターの設定を守り、一貫性のある応答をしてください
```

詳細は [prompt-engineering.md](prompt-engineering.md) を参照

---

## APIキーの設定

### OpenAI

1. [OpenAI Platform](https://platform.openai.com/)にログイン
2. API Keys → Create new secret key
3. `.env`に設定:
```
OPENAI_API_KEY=sk-your-key-here
```

### 料金の目安

| モデル | 入力 | 出力 |
|--------|------|------|
| gpt-4o | $2.50/1M tokens | $10.00/1M tokens |
| gpt-4o-mini | $0.15/1M tokens | $0.60/1M tokens |

**1時間配信の目安:**
- 応答数: 100-200回
- トークン数: 約50,000-100,000
- コスト: $0.50-$2.00（gpt-4o-mini使用時）

---

## 関連ドキュメント

- [character-design.md](character-design.md) - キャラクター設計の詳細
- [prompt-engineering.md](prompt-engineering.md) - プロンプト設計ガイド
- [api-setup.md](api-setup.md) - API設定の詳細
