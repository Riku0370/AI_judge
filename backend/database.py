from datetime import datetime
import sqlite3

from .config import BASE_DIR, DB_PATH, MODEL_PATH
from .storage import saved_image_to_data_url, saved_thumbnail_to_data_url


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


def row_to_prediction_detail(row):
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
        "original_image_data_url": saved_image_to_data_url(row["original_image_path"]),
        "heatmap_data_url": saved_image_to_data_url(row["heatmap_image_path"]),
        "from_cache": True,
    }


def get_prediction_detail(prediction_id):
    with get_db_connection() as connection:
        row = connection.execute(
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
            WHERE id = ?
            """,
            (prediction_id,),
        ).fetchone()

    if row is None:
        return None
    return row_to_prediction_detail(row)


def save_prediction_record(filename, content_type, original_image_path, heatmap_image_path, prediction):
    created_at = datetime.now().isoformat(timespec="seconds")
    explanation = prediction.get(
        "explanation",
        "Grad-CAMにより、判定時に注目した領域をヒートマップとして可視化しています。",
    )

    with get_db_connection() as connection:
        connection.execute(
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


def get_prediction_history(limit=6, page=1, query=None, class_name=None):
    conditions = []
    params = []

    if query:
        conditions.append("original_filename LIKE ?")
        params.append(f"%{query}%")

    if class_name in ("real", "fake"):
        conditions.append("class_name = ?")
        params.append(class_name)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    count_params = list(params)
    offset = (page - 1) * limit
    params.extend([limit, offset])

    with get_db_connection() as connection:
        total = connection.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM predictions
            {where_clause}
            """,
            count_params,
        ).fetchone()["count"]

        rows = connection.execute(
            f"""
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
            {where_clause}
            ORDER BY id DESC
            LIMIT ?
            OFFSET ?
            """,
            params,
        ).fetchall()

    total_pages = max((total + limit - 1) // limit, 1)

    return {
        "items": [
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
                "thumbnail_data_url": saved_thumbnail_to_data_url(row["original_image_path"]),
            }
            for row in rows
        ],
        "page": page,
        "per_page": limit,
        "total": total,
        "total_pages": total_pages,
    }
