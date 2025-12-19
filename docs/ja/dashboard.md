# Webダッシュボード

AITuber Starter KitのWebダッシュボードを使用すると、ブラウザからAITuberシステムを監視・制御できます。

## 機能

### リアルタイム監視

- **システムステータス**: パイプラインの状態、稼働時間、メモリ使用量
- **コメントキュー**: 処理待ちのコメント一覧
- **会話ログ**: ユーザーとAIのやり取りをリアルタイム表示

### リモート制御

- **パイプライン制御**: 開始/停止をブラウザから操作
- **手動メッセージ送信**: テスト用にAIへ直接メッセージを送信
- **設定変更**: 一部の設定をライブで変更

### 設定可能な項目（ライブ変更）

- 応答間隔（response_interval）
- TTSスピーカーID
- TTS速度
- LLM温度

## セットアップ

### 1. ダッシュボードの有効化

`config/config.yaml` を編集：

```yaml
dashboard:
  enabled: true
  host: localhost  # 外部からアクセスする場合は 0.0.0.0
  port: 8080
```

### 2. 起動

```bash
python -m aituber
```

起動すると以下のようなログが表示されます：

```
Dashboard available at http://localhost:8080
```

### 3. アクセス

ブラウザで `http://localhost:8080` を開きます。

## 画面構成

### 左パネル

- **System Status**: システム統計情報
- **Pipeline Control**: 開始/停止ボタン
- **Character**: 現在のキャラクター情報
- **Quick Settings**: ライブ設定変更

### 中央パネル

- **Conversation Log**: 会話履歴
- **Send Manual Message**: テスト用メッセージ入力

### 右パネル

- **Comment Queue**: 処理待ちコメント
- **Long-term Memory**: 長期記憶システム統計

## WebSocket API

ダッシュボードはWebSocketを使用してリアルタイム更新を受信します。

### エンドポイント

```
ws://localhost:8080/api/ws
```

### メッセージ形式

```json
{
  "type": "status|comment|response|ping",
  "data": { ... },
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

## REST API

### エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/health | ヘルスチェック |
| GET | /api/status | システムステータス取得 |
| POST | /api/pipeline/start | パイプライン開始 |
| POST | /api/pipeline/stop | パイプライン停止 |
| GET | /api/comments | 最近のコメント取得 |
| GET | /api/responses | 最近の応答取得 |
| GET | /api/conversations | 会話履歴取得 |
| POST | /api/message | 手動メッセージ送信 |
| GET | /api/config | 設定取得 |
| PATCH | /api/config | 設定更新 |
| GET | /api/character | キャラクター情報取得 |
| GET | /api/memory/stats | 長期記憶統計取得 |

### API ドキュメント

Swagger UIで詳細なAPIドキュメントを確認できます：

```
http://localhost:8080/api/docs
```

## セキュリティ注意事項

### 本番環境での利用

1. **CORSの設定**: `allow_origins` を適切に制限
2. **認証の追加**: 必要に応じて認証機能を実装
3. **HTTPS**: リバースプロキシ経由でHTTPS化
4. **ファイアウォール**: ポートへのアクセスを制限

### 推奨構成

```
[クライアント] -> [Nginx (HTTPS)] -> [Dashboard (HTTP)]
```

## トラブルシューティング

### ダッシュボードにアクセスできない

1. `dashboard.enabled: true` を確認
2. ポートが使用されていないか確認：`netstat -an | grep 8080`
3. ファイアウォール設定を確認

### WebSocketが接続できない

1. ブラウザのコンソールでエラーを確認
2. プロキシ設定を確認（WebSocketのアップグレードが必要）
3. タイムアウト設定を確認

### データが更新されない

1. パイプラインが実行中か確認
2. WebSocket接続状態を確認（画面右上のインジケーター）
3. ブラウザを更新
