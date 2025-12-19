# アバターセットアップガイド

VTube Studioでのアバター設定とAITuber Starter Kitとの連携方法を解説します。

## 目次

1. [VTube Studioのインストール](#vtube-studioのインストール)
2. [モデルのインポート](#モデルのインポート)
3. [APIの有効化](#apiの有効化)
4. [AITuber Starter Kitとの連携](#aituber-starter-kitとの連携)
5. [パラメータ設定](#パラメータ設定)
6. [トラブルシューティング](#トラブルシューティング)

---

## VTube Studioのインストール

### ダウンロード

1. [Steam](https://store.steampowered.com/app/1325860/VTube_Studio/)からダウンロード
2. または[公式サイト](https://denchisoft.com/)から直接ダウンロード

### 初期設定

1. VTube Studioを起動
2. 言語を日本語に設定（設定 → 言語）
3. 解像度を設定（配信に合わせて1920x1080推奨）

---

## モデルのインポート

### Live2Dモデルの場合

1. VTube Studioのモデルフォルダを開く
   - 設定（歯車アイコン）→「モデルフォルダを開く」

2. 新しいフォルダを作成し、以下のファイルを配置：
   ```
   MyModel/
   ├── MyModel.moc3         # モデルファイル
   ├── MyModel.model3.json  # モデル設定
   ├── MyModel.cdi3.json    # 表示設定（オプション）
   ├── MyModel.physics3.json # 物理演算設定
   └── textures/            # テクスチャフォルダ
       └── texture_00.png
   ```

3. VTube Studioを再起動するか、モデル一覧を更新

### VRMモデルの場合

1. VRMファイルを用意
2. モデルフォルダにVRMファイルを配置
3. VTube Studioで読み込み

---

## APIの有効化

AITuber Starter Kitと連携するには、VTube Studio APIを有効にする必要があります。

### 手順

1. VTube Studioを起動

2. 設定画面を開く（歯車アイコン）

3. 「Plugin API設定」を探す

4. 以下の設定を行う：
   ```
   APIを有効にする: オン
   ポート番号: 8001（デフォルト）
   プラグインからのアクセス: 許可
   ```

5. 設定を保存

### 確認方法

ブラウザで以下にアクセスして確認：
```
http://localhost:8001
```

接続できれば、APIが有効になっています。

---

## AITuber Starter Kitとの連携

### 設定ファイルの編集

`config/config.yaml`を編集：

```yaml
avatar:
  enabled: true
  host: localhost
  port: 8001
  plugin_name: "AITuber Starter Kit"
  plugin_developer: "AITuber Community"
```

### 初回接続時

1. AITuber Starter Kitを起動
2. VTube Studioに認証リクエストが表示される
3. 「許可」をクリック
4. 認証トークンが自動的に保存される

### 認証トークンの保存場所

認証トークンは以下に保存されます：
```
~/.aituber/vtube_studio_token.txt
```

---

## パラメータ設定

### AITuber用カスタムパラメータ

VTube Studioで以下のカスタムパラメータを作成すると、より細かい制御が可能です。

| パラメータ名 | 範囲 | 用途 |
|-------------|------|------|
| AITuberMouthOpen | 0-1 | リップシンク用口の開閉 |
| AITuberEmotion | 0-1 | 感情レベル |

### パラメータの作成方法

1. VTube Studioで設定を開く
2. 「パラメータ設定」を選択
3. 「カスタムパラメータを追加」
4. パラメータ名と範囲を設定

### 表情プリセットの設定

感情に応じた表情プリセットを作成：

1. **happy（嬉しい）**
   - 口角を上げる
   - 目を細める
   - 頬を紅潮

2. **sad（悲しい）**
   - 眉を下げる
   - 口角を下げる

3. **surprised（驚き）**
   - 目を大きく開く
   - 口を開ける
   - 眉を上げる

4. **angry（怒り）**
   - 眉をひそめる
   - 口を引き締める

5. **embarrassed（照れ）**
   - 頬を赤らめる
   - 目線をそらす

---

## リップシンクの調整

### 基本設定

AITuber Starter Kitのリップシンクは、音声の音量に基づいて口を動かします。

`src/expression/lip_sync.py`の設定：

```python
# 音量の閾値
VOLUME_THRESHOLD = 0.1

# 口の開き具合の最大値
MAX_MOUTH_OPEN = 1.0

# 更新間隔（ミリ秒）
UPDATE_INTERVAL = 50
```

### 調整のコツ

1. **反応が鈍い場合**
   - `VOLUME_THRESHOLD`を下げる
   - `UPDATE_INTERVAL`を短くする

2. **口が開きすぎる場合**
   - `MAX_MOUTH_OPEN`を下げる

3. **動きがカクカクする場合**
   - `UPDATE_INTERVAL`を長くする
   - スムージングを追加

---

## 表情制御

### 感情分析との連携

AITuber Starter Kitは、生成されたテキストから感情を分析し、自動的に表情を変更します。

### 対応する感情

| 感情 | トリガーワード例 | 表情 |
|------|-----------------|------|
| 喜び | 嬉しい、やった、最高 | 笑顔 |
| 悲しみ | 悲しい、残念、寂しい | 悲しい顔 |
| 驚き | えっ、マジ、すごい | 驚いた顔 |
| 怒り | むかつく、許せない | 怒った顔 |
| 照れ | 恥ずかしい、照れる | 頬を赤らめる |
| 考え中 | うーん、どう、なぜ | 考え顔 |

### カスタマイズ

`src/expression/emotion_analyzer.py`で感情キーワードをカスタマイズできます：

```python
# カスタムキーワードの追加
custom_keywords = {
    Emotion.HAPPY: ["わーい", "やったね", "最高だね"],
}

analyzer = EmotionAnalyzer(custom_keywords=custom_keywords)
```

---

## OBSとの連携

### ウィンドウキャプチャ設定

1. OBSで「ソースを追加」→「ウィンドウキャプチャ」
2. VTube Studioのウィンドウを選択
3. 「カーソルをキャプチャ」をオフ

### 透過設定

1. VTube Studioで背景を緑（または任意の色）に設定
2. OBSで「フィルタ」→「クロマキー」を追加
3. 背景色を選択して透過

### 推奨設定

```
解像度: 1920x1080
フレームレート: 30fps
背景: 透過または単色
```

---

## トラブルシューティング

### 接続できない

**症状**: AITuber Starter KitがVTube Studioに接続できない

**対策**:
1. VTube StudioのAPI設定を確認
2. ポート番号が一致しているか確認
3. ファイアウォール設定を確認
4. VTube Studioを管理者として実行

### 認証が失敗する

**症状**: 認証リクエストが表示されない

**対策**:
1. 認証トークンファイルを削除して再認証
   ```
   rm ~/.aituber/vtube_studio_token.txt
   ```
2. VTube Studioを再起動
3. AITuber Starter Kitを再起動

### リップシンクが動かない

**症状**: 音声は再生されるが口が動かない

**対策**:
1. VTube Studioでパラメータが正しく設定されているか確認
2. `ParamMouthOpenY`または`AITuberMouthOpen`パラメータが存在するか確認
3. パラメータの入力範囲を確認

### 表情が変わらない

**症状**: 感情分析は動いているが表情が変わらない

**対策**:
1. VTube Studioで表情プリセットが設定されているか確認
2. 表情パラメータ名が一致しているか確認
3. `expression.enabled`が`true`になっているか確認

### パフォーマンスが悪い

**症状**: 動作が重い、遅延がある

**対策**:
1. VTube Studioの描画品質を下げる
2. 不要なエフェクトをオフにする
3. 他のアプリケーションを終了
4. GPUドライバーを更新

---

## 参考リンク

- [VTube Studio 公式ドキュメント](https://github.com/DenchiSoft/VTubeStudio)
- [VTube Studio API仕様](https://github.com/DenchiSoft/VTubeStudio/wiki/API)
- [pyvts ライブラリ](https://github.com/Genteki/pyvts)
