from pathlib import Path
import csv

import torch
import torch.nn as nn
from torchvision import models
from model.baseline.tensor import create_dataloaders

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = OUTPUT_DIR / "resnet50_real_fake.pth"
LOG_PATH = OUTPUT_DIR / "loss.csv"

EPOCHS = 20
LEARNING_RATE = 0.001


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")

    return torch.device("cpu")


def create_model():
    model = models.resnet50(
        weights=models.ResNet50_Weights.DEFAULT
    )

    # 既存部分は凍結
    for param in model.parameters():
        param.requires_grad = False

    # 最後の全結合層だけ2クラス用に変更
    model.fc = nn.Linear(model.fc.in_features, 2)

    #layer4の最後のブロックだけ学習可能にする
    for param in model.layer4[-1].parameters():
        param.requires_grad = True
        
    return model


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()

    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)

        predictions = outputs.argmax(dim=1)
        total_correct += (predictions == labels).sum().item()
        total_samples += labels.size(0)

    average_loss = total_loss / total_samples
    accuracy = total_correct / total_samples

    return average_loss, accuracy


def evaluate(model, loader, criterion, device):
    model.eval()

    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item() * images.size(0)

            predictions = outputs.argmax(dim=1)
            total_correct += (predictions == labels).sum().item()
            total_samples += labels.size(0)

    average_loss = total_loss / total_samples
    accuracy = total_correct / total_samples

    return average_loss, accuracy


def initialize_log():
    """
    学習開始時にCSVを新規作成する。
    """
    with open(LOG_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "epoch",
            "train_loss",
            "train_accuracy",
            "valid_loss",
            "valid_accuracy",
        ])
        
def save_log(
    epoch,
    train_loss,
    train_accuracy,
    valid_loss,
    valid_accuracy,
):
    """
    1epoch分の結果をCSVへ追記する。
    """
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            epoch,
            train_loss,
            train_accuracy,
            valid_loss,
            valid_accuracy,
        ])


def main():
    device = get_device()
    print("使用デバイス:", device)

    train_loader, valid_loader, class_to_idx = create_dataloaders()
    print("クラス:", class_to_idx)

    model = create_model().to(device)

    criterion = nn.CrossEntropyLoss()

    optimizer = torch.optim.Adam(
        model.fc.parameters(),
        lr=LEARNING_RATE,
    )

    initialize_log()

    best_valid_accuracy = 0.0

    for epoch in range(1, EPOCHS + 1):
        train_loss, train_accuracy = train_one_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            device,
        )

        valid_loss, valid_accuracy = evaluate(
            model,
            valid_loader,
            criterion,
            device,
        )

        print(f"\nEpoch {epoch}/{EPOCHS}")

        print(
            f"Train Loss: {train_loss:.4f} | "
            f"Train Accuracy: {train_accuracy:.4f}"
        )

        print(
            f"Valid Loss: {valid_loss:.4f} | "
            f"Valid Accuracy: {valid_accuracy:.4f}"
        )

        # epochごとにCSVへ保存
        save_log(
            epoch,
            train_loss,
            train_accuracy,
            valid_loss,
            valid_accuracy,
        )

        print("結果を記録しました:", LOG_PATH)

        # 検証精度が最良のときだけモデルを保存
        if valid_accuracy > best_valid_accuracy:
            best_valid_accuracy = valid_accuracy

            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "class_to_idx": class_to_idx,
                    "valid_accuracy": valid_accuracy,
                },
                MODEL_PATH,
            )

            print(
                f"ベストモデルを保存しました "
                f"(Valid Accuracy: {valid_accuracy:.4f})"
            )


if __name__ == "__main__":
    main()