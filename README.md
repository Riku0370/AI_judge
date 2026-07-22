# AI Judge

AI Judgeは、アップロードした画像が「実写画像」か「AI生成画像」かを判定するWebアプリケーションです。

PyTorchで学習したResNet50モデルをFastAPIから呼び出し、判定結果・信頼度・Grad-CAMによる注目領域をブラウザ上に表示します。判定履歴はSQLiteに保存し、過去の判定結果を検索・再表示できるようにしています。

## 主な機能

- 画像アップロードによる実写 / AI生成画像の2クラス分類
- 判定結果、信頼度、fake / real確率の表示
- Grad-CAMによるヒートマップ表示
- Grad-CAMの反応が強い領域をもとにした簡易説明コメント
- SQLiteによる判定履歴の保存
- 元画像とGrad-CAM画像の保存
- 同じファイル名の画像は再保存・再判定せず、保存済み結果を再利用
- 履歴ページで画像名検索、実写 / AI生成フィルター、ページ切り替え
- 履歴カードをクリックして、過去の判定結果をトップ画面に再表示

## 使用技術

| 領域 | 技術 |
| --- | --- |
| Backend | Python, FastAPI |
| AI / ML | PyTorch, torchvision, ResNet50, Grad-CAM |
| Image | Pillow, NumPy |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |

## アプリ構成

```text
AI_judge/
  app.py                         # FastAPIのルーティング
  backend/
    config.py                    # パス設定
    database.py                  # SQLite操作
    explanation_service.py       # Grad-CAM説明文生成
    model_service.py             # モデル推論とGrad-CAM生成
    storage.py                   # 画像保存とdata URL変換
  frontend/
    templates/
      index.html                 # 判定画面
      history.html               # 履歴画面
    static/
      css/style.css              # 画面デザイン
      javascript/script.js       # 判定画面の操作
      javascript/history.js      # 履歴画面の操作
  model/
    baseline/ResNet50.py         # ResNet50の学習コード
  output/
    resnet50_real_fake.pth       # アプリで使用する学習済みモデル
  data/
    ai_judge.sqlite3             # 判定履歴DB
    uploads/                     # 保存した元画像
    heatmaps/                    # 保存したGrad-CAM画像
```

## 起動方法

仮想環境を有効化します。

```bash
source .venv/bin/activate
```

必要なライブラリが入っていない場合はインストールします。

```bash
pip install fastapi uvicorn python-multipart torch torchvision pillow numpy
```

FastAPIサーバーを起動します。

```bash
uvicorn app:app --reload
```

ブラウザで以下を開きます。

```text
http://127.0.0.1:8000/
```

履歴画面は以下です。

```text
http://127.0.0.1:8000/history
```

## モデル

| 項目 | 内容 |
| --- | --- |
| モデル | ResNet50 |
| タスク | real / fake の2クラス分類 |
| 入力サイズ | 224 x 224 |
| 前処理 | Resize, ToTensor, ImageNet標準のNormalize |
| 可視化 | Grad-CAM |
| Grad-CAM対象層 | ResNet50の`layer4`最終ブロック |

学習済みモデルは`output/resnet50_real_fake.pth`に配置します。アプリ起動時にこのモデルを読み込み、画像アップロード時に推論を行います。

## 性能

学習ログとして保存していた`output/loss.csv`上では、20 epoch学習した結果、検証データに対して以下の性能でした。

| 指標 | 値 |
| --- | --- |
| 最高Valid Accuracy | 88.37% |
| 最高Valid Accuracyのepoch | 18 |
| epoch 18のValid Loss | 0.2878 |
| 最終epochのTrain Accuracy | 90.90% |
| 最終epochのValid Accuracy | 87.37% |
| 最終epochのValid Loss | 0.2928 |

現時点では、独立したテストデータでの最終評価までは実施していません。そのため、README上では「検証データ上の性能」として扱っています。

## 画面

### 判定画面

画像を選択して判定すると、判定結果、信頼度、説明コメント、元画像、Grad-CAMヒートマップを表示します。

同じファイル名の画像がすでに保存されている場合は、再度モデル推論を行わず、DBに保存済みの結果を表示します。

### 履歴画面

保存済みの判定履歴を6件ずつ表示します。画像名検索、実写 / AI生成フィルター、ページ切り替えに対応しています。

履歴カードをクリックすると、トップ画面に戻り、その画像の過去の判定結果とGrad-CAMを再表示します。

## データ保存

画像ファイル自体はSQLiteに直接保存せず、ファイルとして保存したうえでDBには保存先パスを記録します。

```text
data/
  ai_judge.sqlite3
  uploads/
  heatmaps/
```

`predictions`テーブルでは、画像名、判定結果、信頼度、fake / real確率、元画像パス、ヒートマップ画像パス、説明文、判定日時を管理しています。

また、`original_filename`を一意に扱うことで、同じファイル名の画像が再アップロードされた場合に、既存の判定結果を再利用できるようにしています。

## 工夫した点

判定結果だけを表示するのではなく、Grad-CAMを使ってモデルが画像のどこに反応したかを可視化しました。これにより、利用者が「なぜその判定になったのか」を確認しやすくしています。

また、履歴機能を追加し、一度判定した画像を検索・再表示できるようにしました。画像保存とDB保存を分けることで、DBには軽い情報だけを残し、画像はファイルとして管理しています。

## 現在の制限

- Grad-CAMは「モデルが注目した領域」を示すものであり、AI生成画像の根拠を断定するものではありません。
- 現在の説明コメントは、Grad-CAMを3x3領域に分割して最も反応が強い場所を文章化する簡易版です。
- 顔、目、背景などの具体的な物体名や部位名までは判定していません。
- 独立したテストデータでの評価は未実施です。
- 現在はローカル実行を前提としており、デプロイ対応は今後の改善項目です。

## 今後の改善

- 物体検出や顔検出を組み合わせ、注目領域をより具体的に説明する
- ResNet50以外のモデルとの比較機能を追加する
- Data AugmentationやFine-tuningによる精度改善
- 判定結果の集計ダッシュボードを追加する
- Docker化やクラウドデプロイに対応する
- ファイル名だけでなく、画像ハッシュを使った重複判定に変更する

## 提出時の注意

`data/`は判定履歴や保存画像が増えるため、Git管理から外しています。アプリ実行に必要な学習済みモデル`output/resnet50_real_fake.pth`は、コード提出時に一緒に含める想定です。
