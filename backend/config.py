from pathlib import Path


# プロジェクト内で使うパスを1か所に集める。
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
MODEL_PATH = BASE_DIR / "output" / "resnet50_real_fake.pth"

DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
HEATMAP_DIR = DATA_DIR / "heatmaps"
DB_PATH = DATA_DIR / "ai_judge.sqlite3"

for directory in (DATA_DIR, UPLOAD_DIR, HEATMAP_DIR):
    directory.mkdir(parents=True, exist_ok=True)
