import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
df = pd.read_csv(BASE_DIR / "loss.csv")

plt.plot(df["epoch"], df["train_loss"], label="train_loss")
plt.plot(df["epoch"], df["val_loss"], label="val_loss")

plt.xlabel("epoch")
plt.ylabel("loss")
plt.title("Train / Validation Loss")
plt.legend()
plt.grid()

plt.savefig("loss_graph.png")
plt.show()