# モデリングガイド

AITuberのアバター作成に関するガイドです。

## 目次

1. [概要](#概要)
2. [ツール選定](#ツール選定)
3. [Live2Dモデル](#live2dモデル)
4. [VRMモデル](#vrmモデル)
5. [関連ドキュメント](#関連ドキュメント)

---

## 概要

AITuberのアバターには主に2つの形式があります：

| 形式 | 特徴 | 推奨用途 |
|------|------|---------|
| **Live2D** | 2Dイラストを動かす | イラスト系VTuber、繊細な表現 |
| **VRM** | 3Dモデル | 3D系VTuber、ゲーム実況 |

本プロジェクトでは、VTube Studioを通じてLive2Dモデルを制御します。

---

## ツール選定

### Live2D制作ツール

| ツール | 価格 | 特徴 |
|--------|------|------|
| **Live2D Cubism** | 無料〜有料 | 業界標準、高機能 |
| **VTube Studio** | 無料（iOS有料） | トラッキング、表示 |

### 3Dモデル制作ツール

| ツール | 価格 | 特徴 |
|--------|------|------|
| **VRoid Studio** | 無料 | 初心者向け、簡単操作 |
| **Blender** | 無料 | 高機能、学習コスト高 |

### イラスト制作ツール

| ツール | 価格 | 特徴 |
|--------|------|------|
| **CLIP STUDIO PAINT** | 有料 | プロ向け |
| **Procreate** | 有料 | iPad向け |
| **Krita** | 無料 | オープンソース |

---

## Live2Dモデル

### 制作フロー

```
1. イラスト制作
   ↓
2. パーツ分け（PSD）
   ↓
3. Live2D Cubismでリギング
   ↓
4. VTube Studioで読み込み
   ↓
5. パラメータ設定
```

### 必要なパーツ

Live2Dモデルに必要な基本パーツ：

**顔パーツ**
- 顔の輪郭
- 左目（まぶた、白目、瞳、ハイライト）
- 右目（同上）
- 眉毛（左右）
- 鼻
- 口（上唇、下唇、口内、舌、歯）

**体パーツ**
- 首
- 体
- 腕（左右）
- 髪（前髪、横髪、後ろ髪）

### VTube Studio設定

1. モデルをVTube Studioの`Live2DModels`フォルダに配置
2. VTube Studioでモデルを読み込み
3. 「パラメータ設定」でリップシンクを設定

**リップシンク用パラメータ:**
```
ParamMouthOpenY → 口の開閉
ParamMouthForm → 口の形
```

詳細は [live2d-guide.md](live2d-guide.md) を参照してください。

---

## VRMモデル

### VRoid Studioでの作成

1. [VRoid Studio](https://vroid.com/studio)をダウンロード
2. 新規キャラクターを作成
3. 顔・髪・体をカスタマイズ
4. VRM形式でエクスポート

### Blenderでの作成

1. キャラクターモデルを作成
2. リギング（ボーン設定）
3. VRM Add-onでエクスポート

詳細は [vrm-guide.md](vrm-guide.md) を参照してください。

---

## 関連ドキュメント

- [live2d-guide.md](live2d-guide.md) - Live2Dモデル作成の詳細手順
- [vrm-guide.md](vrm-guide.md) - VRMモデル作成ガイド
- [tools-comparison.md](tools-comparison.md) - ツール比較
- [rigging-tips.md](rigging-tips.md) - リギングのコツ
