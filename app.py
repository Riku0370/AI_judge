from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms

# このファイルから見たプロジェクト内の場所を固定する。
# app.py をどこから起動しても、HTMLやモデルの場所がずれないようにするため。
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
MODEL_PATH = BASE_DIR / "output" / "resnet50_real_fake.pth"

# FastAPIアプリ本体。uvicorn app:app --reload の2つ目の app がこれ。
app = FastAPI(title="AI Judge API")

# /static/... というURLで、frontend/static 配下のCSSやJavaScriptを配信する。
# 例: /static/javascript/script.js -> frontend/static/javascript/script.js
app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR / "static"),
    name="static",
)


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


@app.get("/")
def index():
    # ブラウザで http://127.0.0.1:8000/ を開いたときにHTMLを返す。
    return FileResponse(FRONTEND_DIR / "templates" / "index.html")


@app.post("/api/predictions")
async def create_prediction(image: UploadFile = File(...)):
    # JavaScriptの formData.append("image", file) の "image" がここに入る。
    # UploadFileの中身をPillowで開き、RGB画像として扱う。
    pil_image = Image.open(image.file).convert("RGB")

    # モデルに入れられる形へ変換し、batch次元を1つ追加する。
    # shapeは [3, 224, 224] から [1, 3, 224, 224] になる。
    image_tensor = image_transform(pil_image).unsqueeze(0).to(device)

    # 推論だけなので勾配計算を止める。メモリと処理時間を節約できる。
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)[0]
        confidence, predicted_index = probabilities.max(dim=0)

    class_name = idx_to_class[predicted_index.item()]

    # JavaScriptへJSONとして返す。script.js側では data.class_name などで読める。
    return {
        "filename": image.filename,
        "content_type": image.content_type,
        "class_name": class_name,
        "confidence": confidence.item(),
        "fake": probabilities[class_to_idx["fake"]].item(),
        "real": probabilities[class_to_idx["real"]].item(),
    }


@app.get("/api/models/current")
def get_current_model():
    # 画面側に「今どのモデルを使っているか」を表示したくなった時用のAPI。
    return {
        "model_name": "ResNet50 baseline",
        "version": "dev",
        "classes": list(class_to_idx.keys()),
        "description": "PyTorch ResNet50 model for real/fake image classification.",
    }
