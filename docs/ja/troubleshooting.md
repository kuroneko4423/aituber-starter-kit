# トラブルシューティングガイド

よくある問題と解決方法をまとめたガイドです。

## 目次

1. [インストール関連](#インストール関連)
2. [起動時のエラー](#起動時のエラー)
3. [コメント取得](#コメント取得)
4. [AI応答生成](#ai応答生成)
5. [音声合成](#音声合成)
6. [アバター制御](#アバター制御)
7. [パフォーマンス](#パフォーマンス)
8. [その他](#その他)

---

## インストール関連

### pip install でエラーが発生する

**症状**: `pip install -e .` でエラー

**原因と対策**:

1. **Pythonバージョンが古い**
   ```bash
   python --version
   # Python 3.10以上が必要
   ```

2. **pipが古い**
   ```bash
   pip install --upgrade pip
   ```

3. **依存関係の競合**
   ```bash
   # 仮想環境を作り直す
   rm -rf venv
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -e .
   ```

### sounddevice のインストールに失敗

**症状**: `sounddevice`のインストールでエラー

**対策**:

**Windows**:
```bash
# Visual C++ Build Toolsが必要な場合
pip install pipwin
pipwin install sounddevice
```

**macOS**:
```bash
brew install portaudio
pip install sounddevice
```

**Linux**:
```bash
sudo apt-get install libportaudio2 portaudio19-dev
pip install sounddevice
```

### pyvts のインストールに失敗

**症状**: `pyvts`のインストールでエラー

**対策**:
```bash
pip install websockets
pip install pyvts
```

---

## 起動時のエラー

### ModuleNotFoundError

**症状**: `ModuleNotFoundError: No module named 'xxx'`

**対策**:
```bash
# 依存関係を再インストール
pip install -r requirements.txt

# または
pip install -e .
```

### 設定ファイルが見つからない

**症状**: `FileNotFoundError: config/config.yaml`

**対策**:
1. カレントディレクトリを確認
   ```bash
   pwd  # プロジェクトルートにいることを確認
   ```

2. 設定ファイルの存在を確認
   ```bash
   ls config/config.yaml
   ```

3. サンプルからコピー
   ```bash
   cp config/config.yaml.example config/config.yaml
   ```

### 環境変数が読み込まれない

**症状**: `API key not found`

**対策**:
1. `.env`ファイルの存在を確認
   ```bash
   ls -la .env
   ```

2. `.env`の内容を確認
   ```bash
   cat .env
   # APIキーが正しく設定されているか確認
   ```

3. `.env.example`からコピー
   ```bash
   cp .env.example .env
   # その後、APIキーを設定
   ```

---

## コメント取得

### YouTube Liveのコメントが取得できない

**症状**: コメントが取得されない、エラーが発生

**原因と対策**:

1. **video_idが間違っている**
   ```
   正しい形式: dQw4w9WgXcQ
   間違った形式: https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

2. **配信がまだ開始されていない**
   - 配信開始後に再度実行

3. **配信が非公開/メンバー限定**
   - 公開配信でのみ動作します

4. **pytchatの制限**
   ```bash
   # pytchatを最新版に更新
   pip install --upgrade pytchat
   ```

### Twitchのコメントが取得できない

**症状**: Twitchチャットに接続できない

**原因と対策**:

1. **アクセストークンが無効**
   - [https://twitchapps.com/tmi/](https://twitchapps.com/tmi/)で新しいトークンを取得
   - `.env`ファイルを更新

2. **チャンネル名が間違っている**
   ```yaml
   # 正しい形式
   twitch_channel: "channelname"

   # 間違った形式
   twitch_channel: "#channelname"
   twitch_channel: "https://twitch.tv/channelname"
   ```

3. **twitchioのバージョン**
   ```bash
   pip install --upgrade twitchio
   ```

---

## AI応答生成

### OpenAI APIエラー

**症状**: `openai.error.AuthenticationError`

**対策**:
1. APIキーを確認
   ```bash
   echo $OPENAI_API_KEY
   ```

2. APIキーの形式を確認
   ```
   正しい形式: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

3. 利用制限を確認
   - [OpenAIダッシュボード](https://platform.openai.com/usage)で確認

### Rate Limit エラー

**症状**: `openai.error.RateLimitError`

**対策**:
1. `response_interval`を長くする
   ```yaml
   comment:
     response_interval: 10.0  # 5.0から10.0に変更
   ```

2. モデルを変更
   ```yaml
   llm:
     model: gpt-4o-mini  # より制限の緩いモデルに
   ```

### 応答が生成されない

**症状**: コメントに対して応答がない

**対策**:
1. ログを確認
   ```yaml
   logging:
     level: DEBUG
   ```

2. キャラクター設定を確認
   - `config/characters/default.yaml`が正しく設定されているか

3. コンテキストウィンドウを確認
   - 履歴が多すぎると問題が発生する可能性

---

## 音声合成

### VOICEVOXに接続できない

**症状**: `Connection refused`

**対策**:
1. VOICEVOXが起動しているか確認

2. ポート番号を確認
   ```yaml
   tts:
     host: localhost
     port: 50021  # デフォルトポート
   ```

3. ファイアウォール設定を確認

4. 接続テスト
   ```bash
   curl http://localhost:50021/speakers
   ```

### 音声が再生されない

**症状**: 音声合成は成功するが再生されない

**対策**:

1. **オーディオデバイスを確認**
   ```python
   import sounddevice as sd
   print(sd.query_devices())
   ```

2. **デフォルトデバイスを設定**
   ```python
   sd.default.device = 'デバイス名'
   ```

3. **音量を確認**
   - システムの音量設定
   - アプリケーションの音量設定

### 話者IDが見つからない

**症状**: `Speaker ID not found`

**対策**:
1. 利用可能な話者を確認
   ```bash
   curl http://localhost:50021/speakers | python -m json.tool
   ```

2. 正しいspeaker_idを設定
   ```yaml
   tts:
     speaker_id: 1  # 利用可能なIDに変更
   ```

---

## アバター制御

### VTube Studioに接続できない

**症状**: `WebSocket connection failed`

**対策**:

1. **VTube Studioが起動しているか確認**

2. **APIが有効か確認**
   - VTube Studio設定 → Plugin API → APIを有効化

3. **ポート番号を確認**
   ```yaml
   avatar:
     host: localhost
     port: 8001
   ```

4. **認証トークンを削除して再認証**
   ```bash
   rm ~/.aituber/vtube_studio_token.txt
   ```

### リップシンクが動かない

**症状**: 音声は再生されるが口が動かない

**対策**:

1. **パラメータ名を確認**
   - VTube Studioで`ParamMouthOpenY`が存在するか確認

2. **パラメータの入力範囲を確認**
   - 0-1の範囲で動作するか確認

3. **カスタムパラメータを作成**
   ```
   パラメータ名: AITuberMouthOpen
   最小値: 0
   最大値: 1
   ```

### 表情が変わらない

**症状**: 感情に応じて表情が変わらない

**対策**:

1. **expression設定を確認**
   ```yaml
   expression:
     enabled: true
     analyze_emotion: true
   ```

2. **VTube Studioで表情プリセットを確認**
   - happy, sad, surprised などのプリセットが存在するか

---

## パフォーマンス

### 応答が遅い

**症状**: コメントから応答まで時間がかかる

**対策**:

1. **より軽量なモデルを使用**
   ```yaml
   llm:
     model: gpt-4o-mini  # gpt-4oより高速
   ```

2. **ストリーミング応答を使用**（将来対応予定）

3. **TTSの話速を上げる**
   ```yaml
   tts:
     speed: 1.2
   ```

### メモリ使用量が多い

**症状**: 長時間実行するとメモリが増加

**対策**:

1. **会話履歴を制限**
   ```python
   memory = ConversationMemory(max_history=10)
   ```

2. **定期的に再起動**
   - 数時間ごとに再起動をスケジュール

### CPUが高負荷

**症状**: CPU使用率が高い

**対策**:

1. **ポーリング間隔を長くする**

2. **不要な機能を無効化**
   ```yaml
   avatar:
     enabled: false  # アバター制御が不要な場合

   expression:
     enabled: false  # 表情制御が不要な場合
   ```

---

## その他

### ログが出力されない

**対策**:
```yaml
logging:
  level: DEBUG  # INFO から DEBUG に変更
  file: logs/aituber.log  # ファイル出力を有効化
```

### 設定変更が反映されない

**対策**:
1. アプリケーションを再起動
2. 設定ファイルの構文エラーを確認
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
   ```

### 文字化けする

**対策**:
1. ファイルのエンコーディングをUTF-8に
2. コンソールの文字コード設定を確認
   ```bash
   # Windows
   chcp 65001
   ```

---

## サポート

問題が解決しない場合は：

1. **GitHubのIssue**を確認
   - 同様の問題が報告されていないか確認

2. **新しいIssueを作成**
   - エラーメッセージ
   - 環境情報（OS、Pythonバージョン）
   - 再現手順
   - 設定ファイル（APIキーは除く）

3. **ログを添付**
   ```bash
   python -m aituber 2>&1 | tee debug.log
   ```
