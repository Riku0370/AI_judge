from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps

from backend.config import FRONTEND_DIR
from backend.database import (
    get_existing_prediction,
    get_prediction_detail,
    get_prediction_history,
    init_db,
    row_to_prediction_response,
    save_prediction_record,
)
from backend.model_service import get_current_model_info, predict_with_gradcam
from backend.storage import make_storage_paths


init_db()

# FastAPIアプリ本体。uvicorn app:app --reload の2つ目の app がこれ。
app = FastAPI(title="AI Judge API")

# /static/... というURLで、frontend/static 配下のCSSやJavaScriptを配信する。
# 例: /static/javascript/script.js -> frontend/static/javascript/script.js
app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR / "static"),
    name="static",
)


@app.get("/")
def index():
    # ブラウザで http://127.0.0.1:8000/ を開いたときにHTMLを返す。
    return FileResponse(FRONTEND_DIR / "templates" / "index.html")


@app.get("/history")
def history_page():
    return FileResponse(FRONTEND_DIR / "templates" / "history.html")


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
def prediction_history(
    q: str | None = Query(default=None),
    class_name: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=6, ge=1, le=12),
):
    return get_prediction_history(
        limit=per_page,
        page=page,
        query=q,
        class_name=class_name,
    )


@app.get("/api/predictions/{prediction_id}")
def prediction_detail(prediction_id: int):
    prediction = get_prediction_detail(prediction_id)
    if prediction is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


@app.get("/api/models/current")
def get_current_model():
    # 画面側に「今どのモデルを使っているか」を表示したくなった時用のAPI。
    return get_current_model_info()
