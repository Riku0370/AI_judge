from pathlib import Path

from torch.utils.data import DataLoader
from torchvision import datasets, transforms


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "archive" / "rvf10k"

IMAGE_SIZE = 224
BATCH_SIZE = 32


train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.ToTensor(),

    # ImageNetで学習済みのResNet18を使うための正規化
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


valid_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


def create_dataloaders():
    train_dir = DATA_DIR / "train"
    valid_dir = DATA_DIR / "valid"

    if not train_dir.exists():
        raise FileNotFoundError(f"訓練データがありません: {train_dir}")

    if not valid_dir.exists():
        raise FileNotFoundError(f"検証データがありません: {valid_dir}")

    train_dataset = datasets.ImageFolder(
        root=train_dir,
        transform=train_transform,
    )

    valid_dataset = datasets.ImageFolder(
        root=valid_dir,
        transform=valid_transform,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
    )

    valid_loader = DataLoader(
        valid_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
    )

    return train_loader, valid_loader, train_dataset.class_to_idx


if __name__ == "__main__":
    train_loader, valid_loader, class_to_idx = create_dataloaders()

    print("クラス:", class_to_idx)
    print("訓練画像数:", len(train_loader.dataset))
    print("検証画像数:", len(valid_loader.dataset))

    images, labels = next(iter(train_loader))

    print("画像テンソル:", images.shape)
    print("ラベルテンソル:", labels.shape)
    print("ラベル例:", labels[:10])