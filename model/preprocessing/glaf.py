import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# AI_judge ディレクトリ
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ARCHIVE_DIR = BASE_DIR / "archive"

TRAIN_CSV = ARCHIVE_DIR / "train.csv"
VALID_CSV = ARCHIVE_DIR / "valid.csv"

train_data = pd.read_csv(TRAIN_CSV)
val_data = pd.read_csv(VALID_CSV)

datasets = {
    "train": train_data,
    "validation": val_data,
}

# データ数を表示
for name, dataset in datasets.items():
    label_counts = (
        dataset["label"]
        .value_counts()
        .reindex([0, 1], fill_value=0)
    )

    print(f"{name} set:")
    print(f"fake: {label_counts[0]}")
    print(f"real: {label_counts[1]}")
    print()

# 0 = fake、1 = real
train_counts = (
    train_data["label"]
    .value_counts()
    .reindex([0, 1], fill_value=0)
)

val_counts = (
    val_data["label"]
    .value_counts()
    .reindex([0, 1], fill_value=0)
)

df = pd.DataFrame(
    {
        "train": train_counts,
        "validation": val_counts,
    }
)

df.index = ["fake", "real"]

# グラフの描画
ax = df.plot(kind="bar")

ax.set_xlabel("Label")
ax.set_ylabel("Number of images")
ax.set_title("Train / Validation Class Distribution")

plt.xticks(rotation=0)
plt.tight_layout()
plt.show()