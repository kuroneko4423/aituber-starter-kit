# LLMプロバイダー比較ガイド

各LLMプロバイダーの特徴、メリット・デメリット、選び方を解説します。

## 目次

1. [プロバイダー一覧](#プロバイダー一覧)
2. [詳細比較](#詳細比較)
3. [選び方ガイド](#選び方ガイド)
4. [設定例](#設定例)
5. [コスト最適化](#コスト最適化)

---

## プロバイダー一覧

| プロバイダー | モデル | 特徴 |
|-------------|--------|------|
| OpenAI | GPT-4o, GPT-4o-mini | 高品質、安定、豊富なドキュメント |
| Anthropic | Claude 3.5 Sonnet, Claude 3 | 長文対応、安全性重視 |
| Google | Gemini 1.5 Pro/Flash | マルチモーダル、コスパ良好 |
| Ollama | Llama 3.1, Gemma 2 | ローカル実行、無料 |

---

## 詳細比較

### OpenAI (GPT-4o / GPT-4o-mini)

**メリット**:
- 最も成熟したAPI、安定性が高い
- 豊富なドキュメントとサンプル
- Function Calling対応
- 日本語性能が高い

**デメリット**:
- API料金が比較的高い
- レート制限あり
- データがOpenAIに送信される

**推奨用途**:
- 高品質な応答が必要な場合
- 商用プロジェクト
- 開発・テスト用

**料金** (2024年時点):
| モデル | 入力 | 出力 |
|--------|------|------|
| gpt-4o | $2.50/1M | $10.00/1M |
| gpt-4o-mini | $0.15/1M | $0.60/1M |

---

### Anthropic (Claude 3.5 / Claude 3)

**メリット**:
- 非常に長いコンテキストウィンドウ（200K+）
- 安全性・倫理面に配慮
- 論理的な応答
- 日本語性能が高い

**デメリット**:
- APIの歴史が浅い
- 一部機能がOpenAIより少ない
- 料金がやや高め

**推奨用途**:
- 長文の会話履歴を保持したい場合
- 安全性を重視する配信
- 論理的な回答が必要な場合

**料金** (2024年時点):
| モデル | 入力 | 出力 |
|--------|------|------|
| claude-3-5-sonnet | $3.00/1M | $15.00/1M |
| claude-3-haiku | $0.25/1M | $1.25/1M |

---

### Google (Gemini 1.5)

**メリット**:
- 無料枠が比較的大きい
- マルチモーダル対応（画像理解）
- 非常に長いコンテキスト（1M+トークン）
- 高速な応答

**デメリット**:
- APIが比較的新しい
- 日本語が時々不安定
- 機能がOpenAIより少ない場合あり

**推奨用途**:
- コストを抑えたい場合
- 画像を含む配信（将来対応）
- 長時間の会話履歴が必要な場合

**料金** (2024年時点):
| モデル | 入力 | 出力 |
|--------|------|------|
| gemini-1.5-pro | $1.25/1M | $5.00/1M |
| gemini-1.5-flash | $0.075/1M | $0.30/1M |

---

### Ollama (ローカルLLM)

**メリット**:
- 完全無料（電気代のみ）
- データがローカルに留まる（プライバシー）
- オフラインで動作可能
- 制限なし

**デメリット**:
- 高性能GPU/CPUが必要
- 品質がクラウドより劣る場合あり
- セットアップが複雑
- 日本語性能がモデルに依存

**推奨用途**:
- プライバシーを重視する場合
- コストを完全に抑えたい場合
- 実験・開発用
- オフライン環境

**推奨モデル**:
| モデル | VRAM | 特徴 |
|--------|------|------|
| llama3.1:8b | 8GB | バランス型 |
| llama3.1:70b | 40GB+ | 高品質 |
| gemma2:9b | 8GB | 高速 |
| mistral:7b | 8GB | 高速、欧州言語得意 |

---

## 選び方ガイド

### フローチャート

```
開始
  │
  ├─ コストを最優先したい？
  │   ├─ YES → 高性能GPUある？
  │   │         ├─ YES → Ollama
  │   │         └─ NO → Gemini Flash
  │   │
  │   └─ NO → 品質を最優先したい？
  │           ├─ YES → GPT-4o / Claude Sonnet
  │           └─ NO → GPT-4o-mini
  │
  └─ プライバシーを最優先したい？
      ├─ YES → Ollama
      └─ NO → 上記参照
```

### ユースケース別推奨

| ユースケース | 推奨プロバイダー | 推奨モデル |
|-------------|-----------------|-----------|
| 趣味の配信（低コスト） | Google / Ollama | gemini-1.5-flash / llama3.1 |
| 本格的な配信 | OpenAI | gpt-4o-mini |
| 企業・商用利用 | OpenAI / Anthropic | gpt-4o / claude-3-5-sonnet |
| 開発・テスト | Ollama | llama3.1 |
| プライバシー重視 | Ollama | llama3.1 |

---

## 設定例

### OpenAI (GPT-4o-mini)

```yaml
# config/config.yaml
llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 150
```

```env
# .env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Anthropic (Claude 3.5 Sonnet)

```yaml
# config/config.yaml
llm:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  temperature: 0.7
  max_tokens: 150
```

```env
# .env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Google (Gemini 1.5 Flash)

```yaml
# config/config.yaml
llm:
  provider: google
  model: gemini-1.5-flash
  temperature: 0.7
  max_tokens: 150
```

```env
# .env
GOOGLE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Ollama (Llama 3.1)

```yaml
# config/config.yaml
llm:
  provider: ollama
  model: llama3.1
  ollama_host: localhost
  ollama_port: 11434
  temperature: 0.7
  max_tokens: 150
```

---

## コスト最適化

### 1. 軽量モデルを使用

```yaml
# 高品質だが高コスト
llm:
  model: gpt-4o

# コスパ重視
llm:
  model: gpt-4o-mini
```

### 2. 応答長を制限

```yaml
# 長い応答（コスト高）
llm:
  max_tokens: 500

# 短い応答（コスト低）
llm:
  max_tokens: 100
```

### 3. 応答間隔を長くする

```yaml
# 高頻度（コスト高）
comment:
  response_interval: 3.0

# 低頻度（コスト低）
comment:
  response_interval: 10.0
```

### 4. キャッシュを活用（将来対応予定）

同じような質問への応答をキャッシュして、API呼び出しを削減。

### 5. ハイブリッド運用

```python
# 通常コメント → 軽量モデル
# スーパーチャット → 高品質モデル
if comment.donation_amount > 0:
    model = "gpt-4o"
else:
    model = "gpt-4o-mini"
```

---

## パフォーマンス比較

### 応答速度（目安）

| プロバイダー | モデル | 応答時間 |
|-------------|--------|---------|
| OpenAI | gpt-4o-mini | 0.5-1秒 |
| OpenAI | gpt-4o | 1-2秒 |
| Anthropic | claude-3-5-sonnet | 1-2秒 |
| Anthropic | claude-3-haiku | 0.5-1秒 |
| Google | gemini-1.5-flash | 0.3-0.8秒 |
| Ollama | llama3.1 (GPU) | 1-3秒 |

### 日本語品質（主観評価）

| プロバイダー | モデル | 評価 |
|-------------|--------|------|
| OpenAI | gpt-4o | ★★★★★ |
| OpenAI | gpt-4o-mini | ★★★★☆ |
| Anthropic | claude-3-5-sonnet | ★★★★★ |
| Google | gemini-1.5-pro | ★★★★☆ |
| Ollama | llama3.1 | ★★★☆☆ |

---

## まとめ

- **初心者・趣味**: `gpt-4o-mini` または `gemini-1.5-flash`
- **本格運用**: `gpt-4o-mini` → 成長したら `gpt-4o`
- **コスト最重視**: `Ollama` + `llama3.1`
- **品質最重視**: `gpt-4o` または `claude-3-5-sonnet`
