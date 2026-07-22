import numpy as np


REGION_LABELS = [
    ["左上", "上中央", "右上"],
    ["左中央", "中央", "右中央"],
    ["左下", "下中央", "右下"],
]


def describe_gradcam(cam, class_name, confidence):
    # Grad-CAMを3x3に分け、平均値が最も高い領域を文章化する。
    cam_np = np.asarray(cam, dtype=np.float32)
    height, width = cam_np.shape
    row_edges = np.linspace(0, height, 4, dtype=int)
    col_edges = np.linspace(0, width, 4, dtype=int)

    region_scores = []
    for row_index in range(3):
        for col_index in range(3):
            region = cam_np[
                row_edges[row_index]:row_edges[row_index + 1],
                col_edges[col_index]:col_edges[col_index + 1],
            ]
            score = float(region.mean()) if region.size else 0.0
            region_scores.append((score, REGION_LABELS[row_index][col_index]))

    top_score, top_region = max(region_scores, key=lambda item: item[0])
    class_label = "実写画像" if class_name == "real" else "AI生成画像"
    confidence_percent = confidence * 100

    if top_score >= 0.55:
        strength = "特に強く"
    elif top_score >= 0.35:
        strength = "比較的強く"
    else:
        strength = "やや"

    return (
        f"Grad-CAMでは、モデルは画像の{top_region}付近に{strength}反応しています。"
        f"この判定では「{class_label}」と判断しており、信頼度は{confidence_percent:.2f}%です。"
        "これはAI生成の根拠を断定するものではなく、モデルが判定時に注目した領域を示しています。"
    )
