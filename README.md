# AI Judge

## 概要

AI Judgeは、画像が**実写（Real）**か**AI生成画像（Fake）**かを判定する画像分類AIです。

現在は開発途中のプロジェクトであり、転移学習を用いたベースラインモデルの構築と、Webアプリケーション化を進めています。

---

## 開発状況

✅ データセットの前処理

✅ ResNet18 (ImageNet事前学習) を用いた転移学習

✅ 学習・検証LossおよびAccuracyの記録

✅ ベストモデルの保存

✅ Streamlitを用いたWebアプリ開発（進行中）

⬜ 推論精度の改善

⬜ Data Augmentationの追加

⬜ ResNet50・EfficientNetとの比較

⬜ UIの改善

---

## 使用技術

- Python
- PyTorch
- torchvision
- Streamlit
- Pillow

---

## 現在のモデル

- モデル：ResNet18
- 事前学習：ImageNet
- 学習方法：転移学習（FC層）

---

## 今後の予定

- layer4を解凍したFine-tuning
- Data Augmentationによる精度向上
- 他モデルとの性能比較
- Webアプリケーションとして公開
- html,css,javasprictに変更して使いやすさ上昇
