from pathlib import Path
import hashlib

import pandas as pd
from PIL import Image


# AI_judge/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# AI_judge/archive/rvf10k/
ARCHIVE_DIR = BASE_DIR / "archive"
DATA_DIR = ARCHIVE_DIR / "rvf10k"

TRAIN_DIR = DATA_DIR / "train"
VALID_DIR = DATA_DIR / "valid"

TRAIN_CSV = ARCHIVE_DIR / "train.csv"
VALID_CSV = ARCHIVE_DIR / "valid.csv"


def count_image_files(directory: Path) -> int:
    """ディレクトリ内の画像ファイル数を数える"""
    extensions = {".png", ".jpg", ".jpeg"}

    files = sorted(
        file
        for file in directory.iterdir()
        if file.is_file() and file.suffix.lower() in extensions
    )

    print(f"{directory.relative_to(DATA_DIR)}: {len(files)}枚")
    print("最初の5個:", [file.name for file in files[:5]])
    print("最後の5個:", [file.name for file in files[-5:]])
    print()

    return len(files)


def check_csv(csv_path: Path, name: str) -> None:
    """CSVの内容とラベル数を確認する"""
    data = pd.read_csv(csv_path)

    print(f"{name} CSV")
    print("行数:", len(data))
    print("カラム:", list(data.columns))

    if "label" in data.columns:
        print("ラベル数:")
        print(data["label"].value_counts())

    if "label_str" in data.columns:
        print("ラベル名:")
        print(data["label_str"].value_counts())

    print()


def check_missing_files(csv_path: Path, name: str) -> None:
    """CSVに記載された画像が存在するか確認する"""
    data = pd.read_csv(csv_path)

    if "path" not in data.columns:
        print(f"{name}: pathカラムがありません")
        print()
        return

    missing_files = []

    for relative_path in data["path"]:
        full_path = DATA_DIR / relative_path

        if not full_path.exists():
            missing_files.append(relative_path)

    print(f"{name}で存在しない画像: {len(missing_files)}")

    for path in missing_files[:10]:
        print(path)

    print()


def check_image_dimensions() -> None:
    """全画像のサイズを確認する"""
    sizes: dict[tuple[int, int], int] = {}
    unreadable_files = []

    image_dirs = [
        TRAIN_DIR / "fake",
        TRAIN_DIR / "real",
        VALID_DIR / "fake",
        VALID_DIR / "real",
    ]

    for image_dir in image_dirs:
        for image_path in image_dir.iterdir():
            if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                continue

            try:
                with Image.open(image_path) as image:
                    sizes[image.size] = sizes.get(image.size, 0) + 1
            except OSError as error:
                unreadable_files.append((image_path, str(error)))

    print("画像サイズ:")

    for size, count in sorted(sizes.items()):
        print(f"{size}: {count}枚")

    print("読み込めなかった画像:", len(unreadable_files))
    print()


def check_duplicate_images() -> None:
    """trainとvalidを含めて画像の完全重複を確認する"""
    hashes: dict[str, Path] = {}
    duplicates = []

    image_dirs = [
        TRAIN_DIR / "fake",
        TRAIN_DIR / "real",
        VALID_DIR / "fake",
        VALID_DIR / "real",
    ]

    print("画像の重複を確認中...")

    for image_dir in image_dirs:
        for image_path in image_dir.iterdir():
            if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                continue

            image_hash = hashlib.sha256(image_path.read_bytes()).hexdigest()

            if image_hash in hashes:
                duplicates.append((hashes[image_hash], image_path))
            else:
                hashes[image_hash] = image_path

    print("重複した画像:", len(duplicates))

    for original, duplicate in duplicates[:20]:
        print(
            f"{duplicate.relative_to(DATA_DIR)} "
            f"は {original.relative_to(DATA_DIR)} と同一"
        )

    print()