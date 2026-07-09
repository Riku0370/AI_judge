import pandas as pd
from sklearn.model_selection import train_test_split
data = pd.read_csv("archive/metadata.csv")
train_data, temp_data = train_test_split(
    data,
    test_size=0.3,
    random_state=42
    )

val_data, test_data = train_test_split(
    temp_data,
    test_size=0.5,
    random_state=42
    )

print("全体:", len(data))
print("train:", len(train_data))
print("validation:", len(val_data))
print("test:", len(test_data))

train_data.to_csv("archive/train.csv", index=False)
val_data.to_csv("archive/val.csv", index=False)
test_data.to_csv("archive/test.csv", index=False)
