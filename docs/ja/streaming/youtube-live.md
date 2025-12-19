# YouTube Live 配信ガイド

YouTube Liveでの配信設定ガイドです。

## 目次

1. [事前準備](#事前準備)
2. [配信の作成](#配信の作成)
3. [APIキーの取得](#apiキーの取得)
4. [AITuber設定](#aituber設定)
5. [配信開始](#配信開始)

---

## 事前準備

### チャンネルの要件

YouTube Liveを使用するには：

1. **チャンネルの確認**
   - 電話番号による確認が必要
   - [YouTube確認ページ](https://www.youtube.com/verify)

2. **ライブ配信の有効化**
   - 初回は有効化から24時間後に配信可能
   - YouTube Studio → 作成 → ライブ配信を開始

### 配信に必要なもの

- YouTube確認済みアカウント
- OBS Studio（設定済み）
- 安定したインターネット接続（上り5Mbps以上推奨）

---

## 配信の作成

### 1. YouTube Studioにアクセス

1. [YouTube Studio](https://studio.youtube.com/)にログイン
2. 右上の「作成」ボタンをクリック
3. 「ライブ配信を開始」を選択

### 2. 配信設定

**配信タブで設定:**

| 項目 | 設定 |
|------|------|
| タイトル | 配信タイトル |
| 公開設定 | 公開 / 限定公開 / 非公開 |
| 説明 | 配信の説明文 |
| カテゴリ | ゲーム / エンターテインメント等 |
| サムネイル | カスタム画像推奨 |

**詳細設定:**

| 項目 | 推奨設定 |
|------|---------|
| チャット | 有効 |
| 遅延 | 通常の遅延（推奨） |
| DVR | 有効（巻き戻し可能） |

### 3. ストリームキーの取得

1. 「ストリームキーをコピー」をクリック
2. OBSの配信設定に貼り付け

---

## APIキーの取得

AITuber Starter Kitでコメントを取得するには、Video IDが必要です。

### Video IDの確認方法

配信URLから取得：
```
https://www.youtube.com/watch?v=XXXXXXXXXXX
                               ↑ これがVideo ID
```

### YouTube Data API（オプション）

より高度な機能を使用する場合：

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. 「APIとサービス」→「ライブラリ」
4. 「YouTube Data API v3」を検索して有効化
5. 「認証情報」→「認証情報を作成」→「APIキー」
6. 作成されたAPIキーをコピー

**.envに設定:**
```
YOUTUBE_API_KEY=your-api-key-here
```

> **注意**: pytchatライブラリは公開配信であればAPIキーなしでも動作します。

---

## AITuber設定

### config/config.yamlの設定

```yaml
platform:
  name: youtube
  video_id: "YOUR_VIDEO_ID"  # 配信のVideo ID
```

### 実行

```bash
# Video IDを指定して起動
python -m src.main --video-id YOUR_VIDEO_ID
```

---

## 配信開始

### 配信前チェックリスト

- [ ] YouTube Studioで配信を作成済み
- [ ] OBSにストリームキーを設定済み
- [ ] VOICEVOXが起動している
- [ ] VTube Studioが起動している
- [ ] config.yamlにVideo IDを設定済み

### 配信手順

1. **OBSで配信開始**
   - 「配信開始」ボタンをクリック
   - YouTube Studioで映像が届いていることを確認

2. **AITuberを起動**
   ```bash
   python -m src.main
   ```

3. **YouTube Studioで配信開始**
   - 右上の「ライブ配信を開始」をクリック
   - 配信が公開される

### 配信終了

1. YouTube Studioで「ライブ配信を終了」
2. AITuberプログラムを停止（Ctrl+C）
3. OBSで「配信停止」

---

## コメント機能

### サポートされるコメント

| 種類 | 対応状況 | 優先度 |
|------|---------|--------|
| 通常コメント | ✅ | 標準 |
| スーパーチャット | ✅ | 高 |
| メンバーシップ | ✅ | 中 |
| モデレーターコメント | ✅ | 中 |

### スーパーチャットの処理

スーパーチャットは自動的に優先処理されます：

- 金額に応じて優先度が上昇
- 通常コメントより先に処理

---

## トラブルシューティング

### コメントが取得できない

1. **Video IDを確認**
   - URLからVideo IDを正しくコピー

2. **配信が公開されているか確認**
   - 非公開配信ではコメント取得不可

3. **チャットが有効か確認**
   - 配信設定でチャットを有効化

### 配信が途切れる

1. **ビットレートを下げる**
   - OBSで4500kbps以下に設定

2. **ネットワークを確認**
   - 有線接続を推奨

3. **遅延設定を確認**
   - 「通常の遅延」を使用

---

## 参考リンク

- [YouTube Liveヘルプ](https://support.google.com/youtube/topic/9257891)
- [YouTube Data API](https://developers.google.com/youtube/v3)
