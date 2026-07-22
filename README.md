# AI Judge

AI Judgeは、画像が実写画像かAI生成画像かを判定するWebアプリケーションです。  
PyTorchで学習したResNet50モデルをFastAPIから呼び出し、判定結果、信頼度、Grad-CAMによる注目領域の可視化を表示します。

## 主な機能

- 画像アップロードによる実写 / AI生成画像の判定
- 判定結果と信頼度の表示
- Grad-CAMによるヒートマップ表示
- Grad-CAMの強い反応領域をもとにした簡易説明コメント
- SQLiteによる判定履歴の保存
- 元画像とヒートマップ画像の保存
- 同じファイル名の画像は再保存・再判定せず、保存済み結果を再利用
- 履歴ページで画像名検索、実写 / AI生成フィルター、ページ切り替え
- 履歴から過去の判定結果をトップページで再表示

## 使用技術

- Python
- FastAPI
- PyTorch
- torchvision
- Pillow
- SQLite
- HTML
- CSS
- JavaScript

## アプリ構成

```text
AI_judge/
  app.py                         # FastAPIのルーティング
  backend/
    config.py                    # パス設定
    database.py                  # SQLite操作
    explanation_service.py        # Grad-CAM説明文生成
    model_service.py             # モデル推論とGrad-CAM生成
    storage.py                   # 画像保存とdata URL変換
  frontend/
    templates/
      index.html                 # 判定画面
      history.html               # 履歴画面
    static/
      css/style.css
      javascript/script.js
      javascript/history.js
  output/
    resnet50_real_fake.pth       # 学習済みモデル
```

## 画面

### 判定画面

画像を選択して判定すると、以下を表示します。

- 判定結果
- 信頼度
- Grad-CAMの説明コメント
- 元画像
- ヒートマップ画像

### 履歴画面

保存済みの判定履歴を表示します。

- 画像名検索
- 実写 / AI生成フィルター
- 6件ずつのページ切り替え
- 履歴カード選択による過去結果の再表示

## 起動方法

仮想環境を有効化します。

```bash
source .venv/bin/activate
```

FastAPIサーバーを起動します。

```bash
uvicorn app:app --reload
```

ブラウザで以下を開きます。

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/history
```

## モデル

- モデル: ResNet50
- タスク: real / fake の2クラス分類
- 入力画像サイズ: 224 x 224
- 可視化: Grad-CAM
- Grad-CAM対象層: ResNet50のlayer4最終ブロック

## データ保存

判定結果はSQLiteに保存します。画像ファイル自体はDBに直接保存せず、保存先パスをDBに記録します。

```text
data/
  ai_judge.sqlite3
  uploads/       # 元画像
  heatmaps/      # Grad-CAM画像
```

`predictions`テーブルでは、画像名、判定結果、信頼度、fake / real確率、元画像パス、ヒートマップ画像パス、説明文、判定日時を管理しています。

## 工夫した点

単に判定結果だけを表示するのではなく、Grad-CAMを使ってモデルがどの領域に注目したかを可視化しました。  
また、判定履歴をSQLiteで管理し、過去の画像を検索・再表示できるようにしました。

## 現在の制限

- Grad-CAMは「モデルが注目した領域」を示すものであり、AI生成画像の根拠を断定するものではありません。
- 現在の説明コメントは、Grad-CAMを3x3領域に分割して最も反応が強い場所を文章化する簡易版です。
- 顔や目、背景などの具体的な物体名・部位名までは判定していません。

## 今後の改善

- 物体検出や顔検出を組み合わせ、注目領域をより具体的に説明する
- ResNet50以外のモデルとの比較
- Data AugmentationやFine-tuningによる精度改善
- 判定結果の集計ダッシュボード追加
- デプロイ対応

## 発表時の説明ポイント

1. AI生成画像と実写画像を判定するWebアプリを作成した
2. PyTorchのResNet50モデルをFastAPIから利用している
3. 判定結果だけでなく、Grad-CAMでモデルの注目領域を表示した
4. 判定履歴をSQLiteに保存し、検索・再表示できるようにした
5. 今後は物体検出やモデル比較に発展させたい
