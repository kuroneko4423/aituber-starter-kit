# API設定ガイド

各LLMプロバイダーのAPI設定ガイドです。

## 目次

1. [OpenAI](#openai)
2. [Anthropic (Claude)](#anthropic-claude)
3. [Google (Gemini)](#google-gemini)
4. [ローカルLLM (Ollama)](#ローカルllm-ollama)
5. [料金比較](#料金比較)

---

## OpenAI

### APIキーの取得

1. [OpenAI Platform](https://platform.openai.com/)にアクセス
2. アカウントを作成またはログイン
3. 右上のアイコン → 「View API keys」
4. 「Create new secret key」をクリック
5. キーに名前をつけて作成
6. 表示されたキーをコピー（**一度しか表示されません**）

### 設定

**.env:**
```bash
OPENAI_API_KEY=sk-your-api-key-here
```

**config/config.yaml:**
```yaml
llm:
  provider: openai
  model: gpt-4o-mini  # または gpt-4o
  temperature: 0.7
  max_tokens: 150
```

### 利用可能なモデル

| モデル | 特徴 | コスト |
|--------|------|--------|
| gpt-4o | 最高性能、マルチモーダル | 高 |
| gpt-4o-mini | 高性能、コスト効率良 | 低 |
| gpt-4-turbo | 高性能、長文対応 | 中 |

### 料金体系

| モデル | 入力 | 出力 |
|--------|------|------|
| gpt-4o | $2.50/1M tokens | $10.00/1M tokens |
| gpt-4o-mini | $0.15/1M tokens | $0.60/1M tokens |

### 使用量の確認

1. [Usage Dashboard](https://platform.openai.com/usage)にアクセス
2. 日別・月別の使用量を確認

### 利用制限の設定

1. [Billing](https://platform.openai.com/account/billing/overview)にアクセス
2. 「Usage limits」で上限を設定
3. Hard limit（超えると停止）とSoft limit（警告）を設定

---

## Anthropic (Claude)

> **注意**: 現在のMVP版では未対応です。Phase 2で対応予定。

### APIキーの取得

1. [Anthropic Console](https://console.anthropic.com/)にアクセス
2. アカウントを作成
3. 「API Keys」→「Create Key」
4. キーをコピー

### 設定（将来対応予定）

**.env:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

**config/config.yaml:**
```yaml
llm:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  temperature: 0.7
  max_tokens: 150
```

### 利用可能なモデル

| モデル | 特徴 | コスト |
|--------|------|--------|
| claude-3-5-sonnet | バランス型、高性能 | 中 |
| claude-3-opus | 最高性能 | 高 |
| claude-3-haiku | 高速、低コスト | 低 |

---

## Google (Gemini)

> **注意**: 現在のMVP版では未対応です。Phase 2で対応予定。

### APIキーの取得

1. [Google AI Studio](https://aistudio.google.com/)にアクセス
2. Googleアカウントでログイン
3. 「Get API key」をクリック
4. 「Create API key」でキーを生成

### 設定（将来対応予定）

**.env:**
```bash
GOOGLE_API_KEY=your-api-key-here
```

**config/config.yaml:**
```yaml
llm:
  provider: google
  model: gemini-1.5-pro
  temperature: 0.7
  max_tokens: 150
```

### 利用可能なモデル

| モデル | 特徴 | コスト |
|--------|------|--------|
| gemini-1.5-pro | 高性能、長文対応 | 中 |
| gemini-1.5-flash | 高速、低コスト | 低 |

---

## ローカルLLM (Ollama)

> **注意**: 現在のMVP版では未対応です。Phase 2で対応予定。

### Ollamaのインストール

1. [Ollama公式サイト](https://ollama.ai/)からダウンロード
2. インストーラーを実行
3. コマンドラインで確認:
   ```bash
   ollama --version
   ```

### モデルのダウンロード

```bash
# 日本語対応モデルの例
ollama pull llama3.1
ollama pull gemma2
```

### 設定（将来対応予定）

**config/config.yaml:**
```yaml
llm:
  provider: ollama
  model: llama3.1
  host: localhost
  port: 11434
  temperature: 0.7
  max_tokens: 150
```

### メリット・デメリット

**メリット:**
- APIコストがかからない
- プライバシーが保護される
- オフラインで動作

**デメリット:**
- 高性能GPUが必要
- モデル品質がクラウドより劣る場合がある
- セットアップが複雑

---

## 料金比較

### 1時間配信の目安コスト

前提条件:
- 応答数: 150回/時間
- 平均入力: 200トークン
- 平均出力: 100トークン

| プロバイダー | モデル | 推定コスト/時間 |
|-------------|--------|----------------|
| OpenAI | gpt-4o-mini | 約$0.15 |
| OpenAI | gpt-4o | 約$2.50 |
| Anthropic | claude-3-5-sonnet | 約$0.90 |
| Anthropic | claude-3-haiku | 約$0.08 |
| Google | gemini-1.5-flash | 約$0.05 |
| Ollama | llama3.1 | $0（電気代のみ） |

### 月間コスト目安（週3回×4時間配信）

| モデル | 月間コスト |
|--------|-----------|
| gpt-4o-mini | 約$7-10 |
| gpt-4o | 約$100-150 |
| claude-3-haiku | 約$4-6 |
| ローカルLLM | $0 |

---

## セキュリティのベストプラクティス

### APIキーの管理

1. **絶対にコードにハードコードしない**
   ```python
   # NG
   api_key = "sk-xxxxx"

   # OK
   api_key = os.getenv("OPENAI_API_KEY")
   ```

2. **GitHubにpushしない**
   - `.gitignore`に`.env`を追加（済み）

3. **定期的にローテーション**
   - 月に1回程度キーを更新

4. **使用量アラートを設定**
   - 異常な使用量を早期検知

### 環境分離

```bash
# 開発用
OPENAI_API_KEY=sk-dev-xxxxx

# 本番用（別のキー）
OPENAI_API_KEY=sk-prod-xxxxx
```

---

## トラブルシューティング

### 「API key not found」エラー

1. `.env`ファイルが正しい場所にあるか確認
2. キーの形式が正しいか確認
3. 環境変数が読み込まれているか確認

### 「Rate limit exceeded」エラー

1. リクエスト頻度を下げる
2. プランをアップグレード
3. response_intervalを長くする

### 「Insufficient quota」エラー

1. 請求設定を確認
2. クレジットを追加
3. 利用制限を確認

---

## 参考リンク

- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Google AI Documentation](https://ai.google.dev/docs)
- [Ollama Documentation](https://github.com/ollama/ollama)
