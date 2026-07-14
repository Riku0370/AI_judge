from dataset import create_dataloaders
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
import time
import pandas as pd
from pathlib import Path


# AI_judge/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ARCHIVE_DIR = BASE_DIR / "archive"

# AI_judge/archive/rvf10k/
DATA_DIR = ARCHIVE_DIR / "rvf10k"

TRAIN_DIR = DATA_DIR / "train"
VALID_DIR = DATA_DIR / "valid"

TRAIN_CSV = ARCHIVE_DIR / "train.csv"
VALID_CSV = ARCHIVE_DIR / "valid.csv"

IMAGE_DIRS = [
    TRAIN_DIR / "real",
    TRAIN_DIR / "fake",
    VALID_DIR / "real",
    VALID_DIR / "fake",
]
train_loader,val_loader,class_to_idx = create_dataloaders()

torch.set_num_threads(4)

"""
ここは確認範囲
conv = nn.Conv2d(
    in_channels=3,   # RGBなら3
    out_channels=16, # フィルタの数
    kernel_size=3,   # 3x3フィルタ
    stride=1,
    padding=1        # サイズ維持
)

pool = nn.MaxPool2d(kernel_size=2, stride=2)

relu = nn.ReLU()
"""

class SimpleCNN(nn.Module):
    def __init__(self):
        super().__init__()

        self.conv1 = nn.Conv2d(3, 16, 3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, 3,padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.relu = nn.ReLU()

        self.fc1 = nn.Linear(100352, 128)
        self.fc2 = nn.Linear(128, 2)


    def forward(self, x):
        x = self.conv1(x)
        x = self.relu(x)
        x = self.pool(x)

        x = self.conv2(x)
        x = self.relu(x)
        x = self.pool(x)

        #flatten(x, 1) 1番目からそれ以降を結合する
        #複数次元から1次元へ
        x = torch.flatten(x, 1)

        #いくつもあるノードからtrueとfaseの二次元へ
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)

        return x
    
criterion = nn.CrossEntropyLoss()

model = SimpleCNN()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=0.002
)

def train_one_epoch(model, loader, criterion, optimizer):
    model.train()

    total_loss = 0

    for images, labels in loader:
        out = model(images)
        loss = criterion(out, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(loader)


def val_one_epoch(model, loader, criterion):
    model.eval()
    total_loss = 0
    with torch.no_grad():
        for images, labels in loader:
            out = model(images)
            loss = criterion(out, labels)
            total_loss += loss.item()
    
    return total_loss/ len(loader)

def train_model(model, train_loader, val_loader, criterion, optimizer, epochs=3):
    start = time.time()
    train_losses = []
    val_losses = []

    for epoch in range(epochs):
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer)
        val_loss = val_one_epoch(model, val_loader, criterion)
        train_losses.append(train_loss)
        val_losses.append(val_loss)

        print(f"Epoch {epoch+1}: train_loss = {train_loss:.4f}")
        print(f"Epoch {epoch+1}: val_loss = {val_loss:.4f}")

        
        torch.save(model.state_dict(), f"model_epoch_{epoch}.pth")
        end = time.time()
        print("time:", end - start)

    df = pd.DataFrame({
    "epoch": range(1, epochs + 1),
    "train_loss": train_losses,
    "val_loss": val_losses
    })

    df.to_csv("loss.csv", index=False)
    return 

train_model(
    model,
    train_loader,
    val_loader,
    criterion,
    optimizer,
    epochs=10
)
