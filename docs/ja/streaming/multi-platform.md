# マルチプラットフォーム配信ガイド

複数のプラットフォームで同時に配信する方法を解説します。

## 目次

1. [マルチ配信の概要](#マルチ配信の概要)
2. [準備するもの](#準備するもの)
3. [OBS設定](#obs設定)
4. [各プラットフォームの設定](#各プラットフォームの設定)
5. [AITuber Starter Kitの設定](#aituber-starter-kitの設定)
6. [注意事項](#注意事項)

---

## マルチ配信の概要

### メリット

- **視聴者の拡大**: 複数のプラットフォームで視聴者を獲得
- **リスク分散**: 1つのプラットフォームに問題があっても継続可能
- **収益の多様化**: 各プラットフォームの収益化機能を活用

### デメリット

- **管理の複雑さ**: 複数のチャットを同時に管理
- **規約の違い**: プラットフォームごとに異なるルール
- **回線負荷**: より高い配信帯域が必要

---

## 準備するもの

### 必須

- **OBS Studio** または同等の配信ソフト
- **各プラットフォームのアカウント**
  - YouTube
  - Twitch
  - ニコニコ生放送（オプション）
- **マルチ配信サービス**（オプション）
  - Restream.io
  - Streamlabs Multistream

### 推奨スペック

| 項目 | 推奨値 |
|------|--------|
| CPU | Intel Core i7 / AMD Ryzen 7 以上 |
| メモリ | 16GB以上 |
| GPU | NVIDIA GTX 1660 / RTX 2060 以上 |
| 回線速度 | 上り 20Mbps以上 |

---

## OBS設定

### 方法1: OBSの複数出力機能

OBS v28以降では、複数の配信先に同時出力できます。

1. **設定 → 配信**
   - サービス: カスタム
   - サーバー: YouTube/Twitchの配信サーバー
   - ストリームキー: 各プラットフォームのキー

2. **出力 → 詳細設定**
   - エンコーダ: NVENC（GPU）または x264
   - ビットレート: 6000-8000 Kbps
   - キーフレーム間隔: 2秒

### 方法2: Restream.ioを使用

1. [Restream.io](https://restream.io/)にアカウント作成
2. 配信先プラットフォームを追加
3. Restreamから提供されるRTMPサーバーとキーを使用
4. OBSでRestreamに配信 → 各プラットフォームに転送

### 方法3: OBS + プラグイン

1. **Multiple RTMP Outputs Plugin**をインストール
2. プラグイン設定で複数の出力先を設定
3. 各出力先に個別のストリームキーを設定

---

## 各プラットフォームの設定

### YouTube Live

```yaml
# config/config.yaml
platform:
  name: youtube
  video_id: "YOUR_LIVE_VIDEO_ID"
```

### Twitch

```yaml
# config/config.yaml
platform:
  name: twitch
  twitch_channel: "your_channel_name"
```

### 同時接続

現在のAITuber Starter Kitは単一プラットフォームの接続を前提としていますが、
将来のバージョンでマルチプラットフォーム対応を予定しています。

---

## AITuber Starter Kitの設定

### 現在の推奨方法

複数のプラットフォームからコメントを取得するには、複数のインスタンスを起動します。

#### YouTube用インスタンス

```bash
# config/config_youtube.yaml
python -m aituber --config config/config_youtube.yaml
```

#### Twitch用インスタンス

```bash
# config/config_twitch.yaml
python -m aituber --config config/config_twitch.yaml
```

### コメントの統合（将来対応予定）

Phase 4で以下の機能を実装予定：

```yaml
# 将来の設定例
platforms:
  - name: youtube
    video_id: "xxx"
    enabled: true
  - name: twitch
    channel: "xxx"
    enabled: true
  - name: niconico
    live_id: "xxx"
    enabled: false

comment_merge:
  enabled: true
  priority_mode: "round_robin"  # round_robin / priority / random
```

---

## コメント管理のベストプラクティス

### 統一されたコメント表示

複数プラットフォームのコメントを1つの画面に表示：

1. **StreamElements**や**Streamlabs**のマルチチャットウィジェットを使用
2. コメントにプラットフォームアイコンを表示
3. プラットフォームごとに色分け

### コメントの優先順位

```python
# コメント優先度の例
PLATFORM_PRIORITY = {
    "youtube": 1,  # 高優先度
    "twitch": 1,
    "niconico": 2,  # 通常優先度
}

# スーパーチャット/Bitsは最優先
DONATION_BONUS = 100
```

### NGワードの統一

各プラットフォーム共通のNGワードリストを使用：

```
config/
├── ng_words.txt          # 共通NGワード
├── ng_words_youtube.txt  # YouTube固有
└── ng_words_twitch.txt   # Twitch固有
```

---

## 注意事項

### 各プラットフォームの規約

| プラットフォーム | 同時配信 | 独占契約 |
|-----------------|---------|---------|
| YouTube | 許可 | なし |
| Twitch | 許可* | パートナーは制限あり |
| ニコニコ | 許可 | なし |

*Twitchパートナーは24時間の独占期間あり

### 配信品質のバランス

- 回線帯域に注意
- プラットフォームごとの推奨ビットレートを確認
- 最も制限の厳しいプラットフォームに合わせる

### チャット対応

- 全プラットフォームのコメントに公平に反応
- プラットフォーム固有の用語に注意
- 収益化コメント（スパチャ/Bits）を見逃さない

---

## トラブルシューティング

### 一方のプラットフォームだけ切断される

**対策**:
1. 各プラットフォームのサーバーに近いリージョンを選択
2. ビットレートを下げる
3. 接続を監視して自動再接続を設定

### コメントの遅延が大きい

**対策**:
1. 低遅延モードを有効にする
2. コメント取得間隔を短くする
3. サーバーとの接続を最適化

### 配信が不安定

**対策**:
1. CBR（固定ビットレート）を使用
2. バッファサイズを調整
3. 有線LAN接続を使用

---

## 参考リンク

- [Restream.io](https://restream.io/)
- [OBS 複数出力プラグイン](https://github.com/sorayuki/obs-multi-rtmp)
- [YouTube Live 配信ガイド](https://support.google.com/youtube/answer/2474026)
- [Twitch 配信ガイド](https://help.twitch.tv/s/article/guide-to-broadcast-health)
