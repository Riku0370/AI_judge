from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="AI Judge API")

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR / "static"),
    name="static",
)

@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "templates" / "index.html")


@app.post("/api/predictions")
async def create_prediction(image: UploadFile = File(...)):
    return {
        "filename": image.filename,
        "content_type": image.content_type,
        "class_name": "dummy",
        "confidence": 0.0,
    }


@app.get("/api/models/current")
def get_current_model():
    return {
        "model_name": "not connected yet",
        "version": "dev",
        "classes": ["fake", "real"],
        "description": "PyTorch model will be connected later.",
    }