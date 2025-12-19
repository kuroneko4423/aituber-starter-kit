# Twitch 配信ガイド

Twitchでの配信設定ガイドです。

## 目次

1. [事前準備](#事前準備)
2. [配信設定](#配信設定)
3. [Bot設定](#bot設定)
4. [AITuber設定](#aituber設定)
5. [配信開始](#配信開始)

---

## 事前準備

### Twitchアカウント

1. [Twitch](https://www.twitch.tv/)でアカウント作成
2. 二段階認証を有効化（配信に必要）

### 配信に必要なもの

- Twitchアカウント（二段階認証済み）
- OBS Studio（設定済み）
- 安定したインターネット接続

---

## 配信設定

### 1. ストリームキーの取得

1. [Twitchダッシュボード](https://dashboard.twitch.tv/)にアクセス
2. 設定 → 配信
3. 「プライマリストリームキー」をコピー

### 2. OBS設定

設定 → 配信:

| 項目 | 設定 |
|------|------|
| サービス | Twitch |
| サーバー | 自動 または 最寄りのサーバー |
| ストリームキー | コピーしたキー |

または:

1. 「アカウント接続」をクリック
2. Twitchにログイン
3. 自動的に設定される

### 3. 配信情報の設定

Twitchダッシュボードで:

| 項目 | 設定内容 |
|------|---------|
| タイトル | 配信タイトル |
| カテゴリ | Just Chatting / ゲーム名 |
| タグ | VTuber, AITuber 等 |
| 言語 | 日本語 |

---

## Bot設定

### Twitchアプリケーション登録

AITuberでチャットを取得するには、Twitchアプリケーションの登録が必要です。

1. [Twitch Developer Console](https://dev.twitch.tv/console/apps)にアクセス
2. 「アプリケーションを登録」をクリック
3. 以下を入力:

| 項目 | 値 |
|------|-----|
| 名前 | AITuber Bot（任意） |
| OAuth リダイレクト URL | http://localhost:3000 |
| カテゴリ | Chat Bot |

4. 「作成」をクリック
5. Client IDをメモ

### OAuthトークンの取得

1. [Twitch Token Generator](https://twitchapps.com/tmi/)にアクセス
2. 「Connect with Twitch」をクリック
3. 認可を許可
4. 表示されたOAuthトークンをコピー

---

## AITuber設定

### 設定ファイル（将来対応予定）

```yaml
# config/config.yaml
platform:
  name: twitch
  channel: "your_channel_name"
```

### 環境変数

```bash
# .env
TWITCH_CLIENT_ID=your-client-id
TWITCH_OAUTH_TOKEN=oauth:your-token
TWITCH_CHANNEL=your_channel_name
```

> **注意**: 現在のMVP版ではYouTubeのみ対応しています。Twitch対応はPhase 2で実装予定です。

---

## 配信開始

### 配信前チェックリスト

- [ ] Twitchダッシュボードで配信情報を設定
- [ ] OBSにストリームキーを設定
- [ ] VOICEVOXが起動している
- [ ] VTube Studioが起動している

### 配信手順

1. **OBSで配信開始**
   - 「配信開始」ボタンをクリック

2. **Twitchで確認**
   - ダッシュボードでプレビューを確認

3. **AITuberを起動**
   ```bash
   python -m src.main
   ```

---

## Twitch特有の機能

### チャンネルポイント

視聴者がポイントで特定のアクションをトリガーできます。

将来的な対応予定:
- 特定の表情を表示
- 特別な応答をトリガー

### Bitsとサブスクライブ

| イベント | 対応状況 |
|---------|---------|
| Bits | 将来対応予定 |
| サブスクライブ | 将来対応予定 |
| ギフトサブ | 将来対応予定 |

### Raidとホスト

| イベント | 対応状況 |
|---------|---------|
| Raid | 将来対応予定 |
| ホスト | 将来対応予定 |

---

## トラブルシューティング

### 配信が開始されない

1. **ストリームキーを確認**
   - 正しくコピーされているか

2. **二段階認証を確認**
   - 有効になっているか

3. **サーバーを変更**
   - 別のサーバーを試す

### チャットが取得できない

1. **OAuthトークンを確認**
   - 有効期限が切れていないか

2. **チャンネル名を確認**
   - 正しいチャンネル名か

---

## 参考リンク

- [Twitch配信ガイド](https://help.twitch.tv/s/article/guide-to-broadcast-health)
- [Twitch Developer Documentation](https://dev.twitch.tv/docs/)
- [twitchio Documentation](https://twitchio.dev/)
