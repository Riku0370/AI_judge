import pandas as pd
import matplotlib.pyplot as plt

train_data = pd.read_csv("archive/train.csv")
val_data = pd.read_csv("archive/val.csv")
test_data = pd.read_csv("archive/test.csv")

for dataset, name in zip([train_data, val_data, test_data], ["train", "validation", "test"]):
    label_counts = dataset["label"].value_counts()
    print(f"{name} set:")
    print(label_counts)
    print()

# グラフの描画
labels = ["real", "fake"]
train_counts = train_data["label"].value_counts()
val_counts = val_data["label"].value_counts()
test_counts = test_data["label"].value_counts()
x = range(len(labels))
df = pd.DataFrame({
    "train": train_counts,
    "val": val_counts,
    "test": test_counts
}, index=labels)

df.plot(kind="bar")
plt.show()