# よくある質問 (FAQ)

AITuber Starter Kitに関するよくある質問と回答です。

## 目次

1. [一般的な質問](#一般的な質問)
2. [技術的な質問](#技術的な質問)
3. [料金に関する質問](#料金に関する質問)
4. [カスタマイズに関する質問](#カスタマイズに関する質問)
5. [配信に関する質問](#配信に関する質問)

---

## 一般的な質問

### Q: AITuber Starter Kitとは何ですか？

**A**: AITuber Starter Kitは、AIを活用したバーチャルYouTuber（AITuber）を簡単に作成・運用するためのオープンソースツールキットです。YouTube LiveやTwitchのコメントを取得し、AIが自動で応答を生成、音声合成してアバターを動かすことができます。

### Q: プログラミング経験がなくても使えますか？

**A**: 基本的な設定であれば、設定ファイルの編集だけで利用可能です。ただし、以下の知識があるとより活用できます：
- コマンドラインの基本操作
- YAML形式の設定ファイル
- Python（カスタマイズする場合）

### Q: どのようなPCスペックが必要ですか？

**A**: 推奨スペック：
| 項目 | 最小 | 推奨 |
|------|------|------|
| OS | Windows 10 / macOS 12 / Ubuntu 22.04 | 最新版 |
| CPU | Intel Core i5 / AMD Ryzen 5 | Core i7 / Ryzen 7 |
| メモリ | 8GB | 16GB以上 |
| GPU | 統合グラフィック | 専用GPU（VTube Studio用） |
| ストレージ | 10GB | 20GB以上 |

### Q: 商用利用は可能ですか？

**A**: はい、AITuber Starter KitはMITライセンスで提供されており、商用利用が可能です。ただし、以下の点に注意してください：
- 使用するLLM/TTSサービスのライセンスを確認
- VOICEVOXなどの音声合成ソフトの利用規約を確認
- Live2D/VRMモデルの権利を確認

### Q: 日本語以外の言語に対応していますか？

**A**: 現在は日本語を主にサポートしていますが、以下の対応が可能です：
- LLMは多言語対応（OpenAI、Claude、Gemini）
- 感情分析は日本語キーワードベース（カスタマイズ可能）
- TTSは使用するエンジンに依存

---

## 技術的な質問

### Q: 対応しているLLMは何ですか？

**A**: 以下のLLMプロバイダーに対応しています：
- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4-turbo
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- **Google**: Gemini 1.5 Pro, Gemini 1.5 Flash
- **Ollama**: Llama 3.1, Gemma 2 など（ローカル実行）

### Q: 対応している音声合成エンジンは何ですか？

**A**: 以下のTTSエンジンに対応しています：
- **VOICEVOX**: 無料、高品質、多数のキャラクターボイス
- **COEIROINK**: 無料、商用利用可
- **Style-Bert-VITS2**: 感情表現が豊か
- **にじボイス**: API経由、豊富なボイス

### Q: VTube Studio以外のアバターソフトに対応していますか？

**A**: 現在はVTube Studioのみ対応していますが、抽象化されたインターフェースを使用しているため、将来的に他のソフトウェアへの対応も可能です。

### Q: リアルタイム翻訳は対応していますか？

**A**: 現在は対応していませんが、将来のバージョンで対応予定です。現時点では、以下の方法で対応可能です：
- 多言語対応のLLMを使用
- キャラクター設定で複数言語での応答を指示

### Q: 複数のプラットフォームに同時対応できますか？

**A**: 現在は単一プラットフォームの接続を前提としています。複数対応は以下の方法で可能です：
- 複数のインスタンスを起動
- Phase 4でマルチプラットフォーム機能を実装予定

---

## 料金に関する質問

### Q: 無料で使えますか？

**A**: AITuber Starter Kit自体は無料（オープンソース）ですが、以下のサービスには料金がかかる場合があります：

| サービス | 料金 |
|---------|------|
| OpenAI API | 従量課金 |
| Claude API | 従量課金 |
| Gemini API | 無料枠あり（超過は課金） |
| Ollama | 無料（ローカル実行） |
| VOICEVOX | 無料 |
| COEIROINK | 無料 |
| にじボイス | 従量課金 |

### Q: 1時間の配信でどのくらいの費用がかかりますか？

**A**: 目安（応答150回/時間の場合）：

| プロバイダー | モデル | 推定コスト/時間 |
|-------------|--------|----------------|
| OpenAI | gpt-4o-mini | 約$0.15 |
| OpenAI | gpt-4o | 約$2.50 |
| Anthropic | claude-3-5-sonnet | 約$0.90 |
| Google | gemini-1.5-flash | 約$0.05 |
| Ollama | llama3.1 | $0（電気代のみ） |

### Q: 費用を抑えるにはどうすればいいですか？

**A**:
1. **軽量モデルを使用**: gpt-4o-mini、claude-3-haiku、gemini-1.5-flash
2. **ローカルLLMを使用**: Ollama + Llama 3.1
3. **応答間隔を長くする**: 5秒→10秒
4. **max_tokensを制限**: 150以下

---

## カスタマイズに関する質問

### Q: キャラクターの性格を変えるには？

**A**: `config/characters/default.yaml`を編集します：

```yaml
name: "あなたのキャラクター名"
personality: |
  ここに性格の説明を書きます。
  例：明るく元気で、誰とでも仲良くなれる。
speaking_style:
  first_person: "私"
  sentence_endings:
    - "〜だよ"
    - "〜なの"
```

詳細は[キャラクター設計ガイド](ai-config/character-design.md)を参照。

### Q: 新しいTTSエンジンを追加するには？

**A**: `src/tts/base.py`の`BaseTTSEngine`を継承して実装します：

```python
class MyTTSEngine(BaseTTSEngine):
    async def synthesize(self, text: str, speaker_id: int) -> bytes:
        # 実装
        pass

    async def get_speakers(self) -> list[Speaker]:
        # 実装
        pass
```

### Q: 独自の感情を追加するには？

**A**: `src/expression/emotion_analyzer.py`でカスタマイズ：

```python
custom_keywords = {
    Emotion.HAPPY: ["オリジナルキーワード"],
}
analyzer = EmotionAnalyzer(custom_keywords=custom_keywords)
```

### Q: NGワードを設定するには？

**A**: `config/ng_words.txt`を作成し、1行1ワードで記載：

```
NGワード1
NGワード2
```

設定ファイルで有効化：
```yaml
comment:
  ng_words_file: config/ng_words.txt
```

---

## 配信に関する質問

### Q: OBSでアバターを表示するには？

**A**:
1. VTube Studioを起動し、背景を単色に
2. OBSで「ウィンドウキャプチャ」を追加
3. VTube Studioのウィンドウを選択
4. フィルタ→クロマキーで背景を透過

詳細は[OBS設定ガイド](streaming/obs-setup.md)を参照。

### Q: 音声をOBSに取り込むには？

**A**: 仮想オーディオデバイス（VB-Cable等）を使用：
1. VB-Cableをインストール
2. AITuberの音声出力をVB-Cableに設定
3. OBSで音声ソースとしてVB-Cableを追加

### Q: スーパーチャット/Bitsを優先するには？

**A**: 設定で有効化済み（デフォルト）：
```yaml
comment:
  priority_donation: true
```

### Q: 配信中に設定を変更できますか？

**A**: 一部の設定は再起動なしで変更可能です（将来対応予定）。現時点では、設定変更後にアプリケーションの再起動が必要です。

### Q: コメントへの応答を手動で制御できますか？

**A**: 現在は自動応答のみですが、Phase 4のWebダッシュボードで手動制御機能を実装予定です。

---

## その他の質問

### Q: バグを見つけたらどうすればいいですか？

**A**: GitHubのIssueで報告してください。以下の情報を含めてください：
- OS、Pythonバージョン
- エラーメッセージ
- 再現手順
- 関連するログ

### Q: 新機能をリクエストするには？

**A**: GitHubのIssueで「Feature Request」として投稿してください。

### Q: コントリビュートするには？

**A**:
1. リポジトリをフォーク
2. 機能ブランチを作成
3. 変更をコミット
4. プルリクエストを作成

### Q: コミュニティはありますか？

**A**: 今後、Discord/Slackコミュニティの開設を予定しています。

---

この他に質問がある場合は、GitHubのIssueまたはDiscussionsでお気軽にお問い合わせください。
