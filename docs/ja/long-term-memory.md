# 長期記憶システム

AITuber Starter Kitの長期記憶システムは、会話履歴やユーザー情報を永続化し、過去の文脈を活用した応答生成を可能にします。

## 概要

### 特徴

- **SQLiteベース**: 軽量で依存関係なしに動作
- **全文検索**: FTS5による高速な関連記憶の検索
- **ユーザープロファイル**: 視聴者ごとの情報を蓄積
- **RAG対応**: 関連する過去の会話を自動でコンテキストに追加
- **事実抽出**: 会話から重要な情報を自動抽出

## セットアップ

### 1. 長期記憶の有効化

`config/config.yaml` を編集：

```yaml
memory:
  enabled: true
  db_path: data/memory.db  # データベースファイルのパス
  max_results: 5           # 取得する記憶の最大数
  relevance_threshold: 0.3 # 最小関連度スコア（0.0-1.0）
```

### 2. データディレクトリの作成

```bash
mkdir -p data
```

### 3. 起動

通常通り起動すると、自動的にデータベースが初期化されます。

```bash
python -m aituber
```

## 仕組み

### 記憶の保存フロー

```
1. ユーザーコメント受信
      ↓
2. AI応答生成
      ↓
3. 会話を記憶として保存
      ↓
4. 事実の自動抽出・保存（オプション）
      ↓
5. ユーザープロファイル更新
```

### 記憶の取得フロー（RAG）

```
1. 新しいコメント受信
      ↓
2. キーワード抽出
      ↓
3. 関連記憶の検索（FTS5）
      ↓
4. 関連度スコアで順位付け
      ↓
5. コンテキストとしてLLMに提供
```

## 記憶の種類

### MemoryType

| タイプ | 説明 | 例 |
|--------|------|-----|
| CONVERSATION | 会話履歴 | ユーザーとAIのやり取り |
| USER_INFO | ユーザー情報 | 「○○が好き」などの発言 |
| TOPIC | トピック | 話題・議題 |
| FACT | 事実 | 抽出された情報 |
| PREFERENCE | 好み | ユーザーの嗜好 |

### 重要度レベル

| レベル | 説明 | 用途 |
|--------|------|------|
| LOW | 低 | 一般的な会話 |
| MEDIUM | 中 | 通常の情報 |
| HIGH | 高 | 重要な情報 |
| CRITICAL | 最重要 | 絶対に忘れてはいけない情報 |

## ユーザープロファイル

各視聴者について以下の情報を自動で蓄積します：

- **first_seen**: 初回視聴日時
- **last_seen**: 最終視聴日時
- **interaction_count**: やり取りの回数
- **topics**: 話したトピック一覧
- **preferences**: 好み・嗜好
- **notes**: メモ

### プロファイルの活用例

```
[User Info: Viewer123]
Interactions: 42
Topics: ゲーム, アニメ, 料理
Preferences: 好きなゲーム: Minecraft

[Relevant Memories]
- [2h ago] Viewer123: 今日Minecraftで大きな家を建てたよ
- [1d ago] Viewer123さんはアニメ好きと言っていた
```

## 関連度スコアリング

記憶の関連度は以下の要素で計算されます：

### スコアの構成

```python
score = (
    keyword_match_score * 0.5  # キーワード一致度
    + recency_score * 0.3      # 新しさ
    + importance_score * 0.2   # 重要度
    + user_context_bonus       # ユーザーコンテキスト
)
```

### 新しさスコア

| 経過時間 | スコア |
|---------|--------|
| 1時間以内 | 1.0 |
| 1日以内 | 0.8 |
| 1週間以内 | 0.5 |
| 1ヶ月以内 | 0.3 |
| それ以上 | 0.1 |

## 設定オプション

### RetrievalConfig

```python
@dataclass
class RetrievalConfig:
    max_results: int = 5           # 取得する記憶の最大数
    relevance_threshold: float = 0.3  # 最小関連度
    recency_weight: float = 0.3    # 新しさの重み
    importance_weight: float = 0.2  # 重要度の重み
    user_context_weight: float = 0.3  # ユーザーコンテキストの重み
    include_user_profile: bool = True  # プロファイルを含めるか
```

## APIリファレンス

### LongTermMemory

```python
# 初期化
memory = LongTermMemory(db_path="data/memory.db")
await memory.initialize()

# 記憶の保存
entry = MemoryEntry(
    content="ユーザーがMinecraftが好きと言った",
    memory_type=MemoryType.USER_INFO,
    user_name="Viewer123",
    importance=Importance.MEDIUM,
)
entry_id = await memory.store(entry)

# 記憶の検索
results = await memory.search(
    query="ゲーム",
    limit=10,
    user_name="Viewer123",
)

# ユーザープロファイル取得
profile = await memory.get_user_profile("Viewer123")

# 統計情報
stats = await memory.get_stats()
```

### MemoryRetriever

```python
# 初期化
retriever = MemoryRetriever(memory_store, config)

# コンテキスト取得（LLMプロンプト用）
context = await retriever.retrieve_context(
    query="今日は何する？",
    user_name="Viewer123",
)

# 会話の保存
await retriever.store_interaction(
    user_name="Viewer123",
    user_message="こんにちは",
    ai_response="こんにちは！今日も来てくれてありがとう！",
    emotion="happy",
)
```

## データベース構造

### テーブル

```sql
-- 記憶エントリ
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    user_name TEXT,
    keywords TEXT,
    importance TEXT,
    emotion TEXT,
    timestamp TEXT NOT NULL,
    last_accessed TEXT,
    access_count INTEGER DEFAULT 0,
    metadata TEXT
);

-- ユーザープロファイル
CREATE TABLE user_profiles (
    user_name TEXT PRIMARY KEY,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    interaction_count INTEGER DEFAULT 0,
    topics TEXT,
    preferences TEXT,
    notes TEXT
);

-- 全文検索インデックス
CREATE VIRTUAL TABLE memories_fts USING fts5(
    content,
    keywords
);
```

## バックアップとメンテナンス

### バックアップ

```bash
# SQLiteファイルをコピー
cp data/memory.db data/memory_backup_$(date +%Y%m%d).db
```

### データベースの最適化

```bash
sqlite3 data/memory.db "VACUUM;"
```

### 古い記憶の削除

```bash
sqlite3 data/memory.db "DELETE FROM memories WHERE timestamp < datetime('now', '-90 days');"
```

## トラブルシューティング

### データベースが作成されない

1. `memory.enabled: true` を確認
2. `data/` ディレクトリの書き込み権限を確認
3. ディスク容量を確認

### 記憶が取得されない

1. `relevance_threshold` を下げてみる
2. 検索クエリのキーワードを確認
3. データベースに記憶が存在するか確認

### パフォーマンスが遅い

1. `max_results` を減らす
2. 古い記憶を削除してデータベースをスリム化
3. `VACUUM` でデータベースを最適化
