import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOSS_CSV_CANDIDATES = [
    BASE_DIR / "output" / "loss.csv",
    BASE_DIR / "loss.csv",
    BASE_DIR / "model" / "output" / "loss.csv",
]

loss_csv = next((path for path in LOSS_CSV_CANDIDATES if path.exists()), None)
if loss_csv is None:
    candidates = "\n".join(str(path) for path in LOSS_CSV_CANDIDATES)
    raise FileNotFoundError(f"loss.csv が見つかりません。確認した場所:\n{candidates}")

df = pd.read_csv(loss_csv)
valid_loss_column = "valid_loss" if "valid_loss" in df.columns else "val_loss"

plt.figure()
plt.plot(df["epoch"], df["train_loss"], label="train_loss")
plt.plot(df["epoch"], df[valid_loss_column], label=valid_loss_column)

plt.xlabel("epoch")
plt.ylabel("loss")
plt.title("Train / Validation Loss")
plt.legend()
plt.grid()

loss_output_path = loss_csv.parent / "loss_graph.png"
plt.savefig(loss_output_path)
print(f"グラフを保存しました: {loss_output_path}")
plt.close()

# Accuracy graph
required_accuracy_columns = {"train_accuracy", "valid_accuracy"}
missing_columns = required_accuracy_columns - set(df.columns)
if missing_columns:
    raise KeyError(f"accuracy の列が見つかりません: {sorted(missing_columns)}")

plt.figure()
plt.plot(df["epoch"], df["train_accuracy"], label="train_accuracy")
plt.plot(df["epoch"], df["valid_accuracy"], label="valid_accuracy")

plt.xlabel("epoch")
plt.ylabel("accuracy")
plt.title("Train / Validation Accuracy")
plt.legend()
plt.grid()

accuracy_output_path = loss_csv.parent / "accuracy_graph.png"
plt.savefig(accuracy_output_path)
print(f"グラフを保存しました: {accuracy_output_path}")
plt.close()
