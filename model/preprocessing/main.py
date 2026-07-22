from pathlib import Path

from preprocessing import (
    count_image_files,
    check_csv,
    check_missing_files,
    check_image_dimensions,
    check_duplicate_images,
)


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


def main() -> None:
    print("データセット:", DATA_DIR)
    print()

    # 画像数の確認
    for image_dir in IMAGE_DIRS:
        count_image_files(image_dir)

    # CSVの内容確認
    check_csv(TRAIN_CSV, "train")
    check_csv(VALID_CSV, "valid")

    # CSVに記載された画像が存在するか確認
    check_missing_files(TRAIN_CSV, DATA_DIR)
    check_missing_files(VALID_CSV, DATA_DIR)

    # 画像サイズの確認
    check_image_dimensions()

    # trainとvalidを含む重複確認
    check_duplicate_images()


if __name__ == "__main__":
    main()