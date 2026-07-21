from pathlib import Path
import base64
from datetime import datetime
import io
import re
import sqlite3

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
from PIL import Image, ImageOps
import torch
import torch.nn as nn
from torchvision import models, transforms

# このファイルから見たプロジェクト内の場所を固定する。
# app.py をどこから起動しても、HTMLやモデルの場所がずれないようにするため。
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
MODEL_PATH = BASE_DIR / "output" / "resnet50_real_fake.pth"
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
HEATMAP_DIR = DATA_DIR / "heatmaps"
DB_PATH = DATA_DIR / "ai_judge.sqlite3"

for directory in (DATA_DIR, UPLOAD_DIR, HEATMAP_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# FastAPIアプリ本体。uvicorn app:app --reload の2つ目の app がこれ。
app = FastAPI(title="AI Judge API")

# /static/... というURLで、frontend/static 配下のCSSやJavaScriptを配信する。
# 例: /static/javascript/script.js -> frontend/static/javascript/script.js
app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR / "static"),
    name="static",
)


def get_db_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    # 画像ファイルはDBに直接入れず、保存先のパスだけをDBに記録する。
    # 同じファイル名の画像は再保存しないため、original_filenameをUNIQUEにする。
    with get_db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                path TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_filename TEXT NOT NULL UNIQUE,
                content_type TEXT,
                original_image_path TEXT NOT NULL,
                heatmap_image_path TEXT NOT NULL,
                class_name TEXT NOT NULL,
                confidence REAL NOT NULL,
                fake_probability REAL NOT NULL,
                real_probability REAL NOT NULL,
                model_id INTEGER,
                explanation TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (model_id) REFERENCES models(id)
            )
        """)
        connection.execute("""
            INSERT INTO models (id, name, version, path, description, created_at)
            VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                version = excluded.version,
                path = excluded.path,
                description = excluded.description
        """, (
            "ResNet50 baseline",
            "dev",
            str(MODEL_PATH.relative_to(BASE_DIR)),
            "Real/Fake image classification model with Grad-CAM visualization.",
            datetime.now().isoformat(timespec="seconds"),
        ))


init_db()


def get_device():
    # MacのMPSが使える場合はGPU系の処理を使い、なければCPUで推論する。
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


device = get_device()

# 学習時と同じResNet50構造を作り、最後の分類層だけ2クラス用にする。
model = models.resnet50(weights=None)
model.fc = nn.Linear(model.fc.in_features, 2)

# 保存済みcheckpointを読み込んで、モデルに学習済みパラメータを反映する。
checkpoint = torch.load(MODEL_PATH, map_location=device)
model.load_state_dict(checkpoint["model_state_dict"])
model.to(device)
model.eval()

# ImageFolderのクラス順をcheckpointから復元する。
# 例: {"fake": 0, "real": 1} を {0: "fake", 1: "real"} に反転して使う。
class_to_idx = checkpoint.get("class_to_idx", {"fake": 0, "real": 1})
idx_to_class = {
    index: class_name
    for class_name, index in class_to_idx.items()
}

# 学習時と同じ前処理を推論時にも使う。
# サイズ、Tensor変換、ImageNet正規化が学習時とずれると判定結果もずれる。
image_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


def make_heatmap_overlay(original_image, cam):
    # 0から1のGrad-CAMを画像サイズまで拡大し、元画像の上に赤色で重ねる。
    cam_np = cam.detach().cpu().numpy()
    cam_image = Image.fromarray(np.uint8(cam_np * 255))
    cam_image = cam_image.resize(original_image.size, resample=Image.BILINEAR)

    heat = np.array(cam_image) / 255.0
    overlay_array = np.zeros((original_image.height, original_image.width, 4), dtype=np.uint8)
    overlay_array[..., 0] = 255
    overlay_array[..., 1] = np.uint8(180 * heat)
    overlay_array[..., 3] = np.uint8(130 * heat)

    base = original_image.convert("RGBA")
    overlay = Image.fromarray(overlay_array, mode="RGBA")
    return Image.alpha_composite(base, overlay).convert("RGB")


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


def get_existing_prediction(filename):
    with get_db_connection() as connection:
        return connection.execute(
            """
            SELECT
                id,
                original_filename,
                content_type,
                original_image_path,
                heatmap_image_path,
                class_name,
                confidence,
                fake_probability,
                real_probability,
                explanation,
                created_at
            FROM predictions
            WHERE original_filename = ?
            """,
            (filename,),
        ).fetchone()


def row_to_prediction_response(row, from_cache):
    return {
        "id": row["id"],
        "filename": row["original_filename"],
        "content_type": row["content_type"],
        "class_name": row["class_name"],
        "confidence": row["confidence"],
        "fake": row["fake_probability"],
        "real": row["real_probability"],
        "explanation": row["explanation"],
        "created_at": row["created_at"],
        "original_image_path": row["original_image_path"],
        "heatmap_image_path": row["heatmap_image_path"],
        "heatmap_data_url": saved_image_to_data_url(row["heatmap_image_path"]),
        "from_cache": from_cache,
    }


def save_prediction_record(filename, content_type, original_image_path, heatmap_image_path, prediction):
    created_at = datetime.now().isoformat(timespec="seconds")
    explanation = "Grad-CAMにより、判定時に注目した領域をヒートマップとして可視化しています。"

    with get_db_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO predictions (
                original_filename,
                content_type,
                original_image_path,
                heatmap_image_path,
                class_name,
                confidence,
                fake_probability,
                real_probability,
                model_id,
                explanation,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                content_type,
                str(original_image_path.relative_to(BASE_DIR)),
                str(heatmap_image_path.relative_to(BASE_DIR)),
                prediction["class_name"],
                prediction["confidence"],
                prediction["fake"],
                prediction["real"],
                1,
                explanation,
                created_at,
            ),
        )

    row = get_existing_prediction(filename)
    return row_to_prediction_response(row, from_cache=False)


def predict_with_gradcam(pil_image):
    # hookが保存する場所。forwardで特徴マップ、backwardで勾配がここに入る。
    saved_values = {
        "features": None,
        "gradients": None,
    }

    def save_features(module, inputs, output):
        saved_values["features"] = output

    def save_gradients(module, grad_input, grad_output):
        saved_values["gradients"] = grad_output[0]

    # ResNet50の最後に近い畳み込み層を見る。
    # ここは「画像のどのあたりを見て判定したか」を取り出しやすい層。
    target_layer = model.layer4[-1]
    forward_handle = target_layer.register_forward_hook(save_features)
    backward_handle = target_layer.register_full_backward_hook(save_gradients)

    try:
        image_tensor = image_transform(pil_image).unsqueeze(0).to(device)

        # Grad-CAMではbackwardが必要なので、torch.no_grad()は使わない。
        outputs = model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)[0]
        confidence, predicted_index = probabilities.max(dim=0)
        class_name = idx_to_class[predicted_index.item()]

        model.zero_grad()
        target_score = outputs[0, predicted_index]
        target_score.backward()

        features = saved_values["features"]
        gradients = saved_values["gradients"]

        # 勾配の平均を「各特徴マップの重要度」として使い、特徴マップに掛ける。
        weights = gradients.mean(dim=(2, 3), keepdim=True)
        cam = (weights * features).sum(dim=1)
        cam = torch.relu(cam).squeeze()
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)

        heatmap_image = make_heatmap_overlay(pil_image, cam)

        return {
            "class_name": class_name,
            "confidence": confidence.item(),
            "fake": probabilities[class_to_idx["fake"]].item(),
            "real": probabilities[class_to_idx["real"]].item(),
            "heatmap_image": heatmap_image,
        }
    finally:
        forward_handle.remove()
        backward_handle.remove()


@app.get("/")
def index():
    # ブラウザで http://127.0.0.1:8000/ を開いたときにHTMLを返す。
    return FileResponse(FRONTEND_DIR / "templates" / "index.html")


@app.post("/api/predictions")
async def create_prediction(image: UploadFile = File(...)):
    # JavaScriptの formData.append("image", file) の "image" がここに入る。
    original_filename = Path(image.filename or "uploaded_image").name

    # 同じファイル名がDBにある場合は、画像を再保存せず既存結果を返す。
    existing_prediction = get_existing_prediction(original_filename)
    if existing_prediction is not None:
        return row_to_prediction_response(existing_prediction, from_cache=True)

    # スマホ写真などの向き情報を反映してから、RGB画像として扱う。
    pil_image = ImageOps.exif_transpose(Image.open(image.file)).convert("RGB")
    prediction = predict_with_gradcam(pil_image)

    original_image_path, heatmap_image_path = make_storage_paths(original_filename)
    pil_image.save(original_image_path)
    prediction["heatmap_image"].save(heatmap_image_path)

    # JavaScriptへJSONとして返す。script.js側では data.class_name などで読める。
    return save_prediction_record(
        filename=original_filename,
        content_type=image.content_type,
        original_image_path=original_image_path,
        heatmap_image_path=heatmap_image_path,
        prediction=prediction,
    )


@app.get("/api/predictions/history")
def get_prediction_history():
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                original_filename,
                content_type,
                original_image_path,
                heatmap_image_path,
                class_name,
                confidence,
                fake_probability,
                real_probability,
                explanation,
                created_at
            FROM predictions
            ORDER BY id DESC
            LIMIT 20
            """
        ).fetchall()

    return [
        {
            "id": row["id"],
            "filename": row["original_filename"],
            "class_name": row["class_name"],
            "confidence": row["confidence"],
            "fake": row["fake_probability"],
            "real": row["real_probability"],
            "created_at": row["created_at"],
            "original_image_path": row["original_image_path"],
            "heatmap_image_path": row["heatmap_image_path"],
        }
        for row in rows
    ]


@app.get("/api/models/current")
def get_current_model():
    # 画面側に「今どのモデルを使っているか」を表示したくなった時用のAPI。
    return {
        "model_name": "ResNet50 baseline",
        "version": "dev",
        "classes": list(class_to_idx.keys()),
        "description": "PyTorch ResNet50 model for real/fake image classification.",
    }
