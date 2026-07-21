from pathlib import Path
import base64
import io
import re

from PIL import Image

from .config import BASE_DIR, HEATMAP_DIR, UPLOAD_DIR


def image_to_data_url(image):
    # 画像をファイル保存せず、ブラウザで表示できる文字列に変換する。
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded_image}"


def saved_image_to_data_url(image_path):
    # DBに保存したパスから画像を読み、画面表示用のdata URLへ変換する。
    saved_path = BASE_DIR / image_path
    with Image.open(saved_path) as saved_image:
        return image_to_data_url(saved_image.convert("RGB"))


def saved_thumbnail_to_data_url(image_path, size=(360, 240)):
    # 履歴一覧用の小さい画像を作り、画面表示用のdata URLへ変換する。
    saved_path = BASE_DIR / image_path
    with Image.open(saved_path) as saved_image:
        thumbnail = saved_image.convert("RGB")
        thumbnail.thumbnail(size)
        return image_to_data_url(thumbnail)


def make_safe_filename(filename):
    # ユーザー入力のファイル名を、保存に使いやすい安全な名前へ寄せる。
    original_name = Path(filename or "uploaded_image").name
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", original_name)
    return safe_name or "uploaded_image"


def make_storage_paths(filename):
    # 元画像とGrad-CAM画像を、それぞれ専用フォルダ直下に保存する。
    safe_name = make_safe_filename(filename)
    stem = Path(safe_name).stem or "uploaded_image"
    suffix = Path(safe_name).suffix.lower() or ".png"

    original_image_path = UPLOAD_DIR / f"{stem}{suffix}"
    heatmap_image_path = HEATMAP_DIR / f"{stem}_gradcam.png"
    return original_image_path, heatmap_image_path
