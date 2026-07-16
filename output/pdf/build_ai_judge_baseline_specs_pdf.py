from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


OUTPUT = "/Users/riku/Project/program/1week_project/AI_judge/output/pdf/AI_judge_baseline_specs.pdf"
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"


def paragraph(text, style):
    return Paragraph(str(text).replace("\n", "<br/>"), style)


def make_table(rows, widths, styles):
    data = [[paragraph(cell, styles["TableCell"]) for cell in row] for row in rows]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "JP"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.6),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6EEF8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1A202C")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FBFD")]),
            ]
        )
    )
    return table


def add_section(story, title, note, rows, widths, styles):
    story.append(paragraph(title, styles["Section"]))
    story.append(paragraph(note, styles["Body"]))
    story.append(Spacer(1, 5 * mm))
    story.append(make_table(rows, widths, styles))


def main():
    pdfmetrics.registerFont(TTFont("JP", FONT))
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="AI_judge baseline specs",
    )
    base = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle(
            "TitleJP",
            parent=base["Title"],
            fontName="JP",
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "Subtitle": ParagraphStyle(
            "SubtitleJP",
            parent=base["BodyText"],
            fontName="JP",
            fontSize=10,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4A5568"),
            spaceAfter=12,
        ),
        "Section": ParagraphStyle(
            "SectionJP",
            parent=base["Heading2"],
            fontName="JP",
            fontSize=15,
            leading=19,
            textColor=colors.HexColor("#1A365D"),
            spaceBefore=2,
            spaceAfter=3,
        ),
        "Body": ParagraphStyle(
            "BodyJP",
            parent=base["BodyText"],
            fontName="JP",
            fontSize=9.2,
            leading=13,
            textColor=colors.HexColor("#4A5568"),
            alignment=TA_LEFT,
        ),
        "TableCell": ParagraphStyle(
            "TableCellJP",
            parent=base["BodyText"],
            fontName="JP",
            fontSize=7.6,
            leading=10.5,
            textColor=colors.HexColor("#1A202C"),
        ),
    }

    screen_rows = [
        ["画面", "目的", "表示項目", "操作・ボタン", "遷移先", "呼び出すAPI", "優先度"],
        ["トップ画面", "アプリの入口。AI判定へ迷わず進ませる。", "アプリ名、短い説明、使い方の一文、履歴リンク", "判定を始める、履歴を見る", "AI判定画面、履歴画面", "なし", "必須"],
        ["AI判定画面", "画像を選び、AI判定を実行する。", "画像選択欄、画像プレビュー、注意文、エラー表示領域", "画像を選択、判定する、トップへ戻る", "結果画面、エラー表示", "POST /api/predictions", "必須"],
        ["結果画面", "判定結果とAIの注目箇所をまとめて見せる。", "アップロード画像、分類結果、信頼度、ヒートマップ、簡単な説明", "もう一度判定、詳しく見る、履歴を見る", "AI判定画面、解説詳細画面、履歴画面", "GET /api/predictions/{id}", "必須"],
        ["解説詳細画面", "初心者向けに判定結果やヒートマップの意味を説明する。", "分類結果の説明、ヒートマップの読み方、注意点", "結果画面へ戻る", "結果画面", "GET /api/predictions/{id}", "推奨"],
        ["履歴画面", "過去の判定結果を見返せるようにする。", "判定日時、画像サムネイル、分類結果、信頼度", "詳細を見る、削除、判定画面へ戻る", "結果画面、AI判定画面", "GET /api/predictions、DELETE /api/predictions/{id}", "推奨"],
        ["エラー表示", "ユーザーが直せるエラーをわかりやすく伝える。", "未選択、非対応形式、容量超過、判定失敗メッセージ", "画像を選び直す、再判定する", "AI判定画面", "POST /api/predictions", "必須"],
        ["管理者ログ画面", "判定失敗などを後から確認できるようにする。", "エラー日時、内容、画像ID、状態", "状態更新、確認済みにする", "なし", "GET /api/error-logs", "将来"],
    ]

    api_rows = [
        ["分類", "メソッド", "エンドポイント", "目的", "リクエスト", "レスポンス", "優先度"],
        ["判定", "POST", "/api/predictions", "画像を受け取り、AI判定とGrad-CAM生成を行う。", "image: file", "prediction_id, class_name, confidence, image_url, heatmap_url, explanation", "必須"],
        ["判定", "GET", "/api/predictions/{id}", "1件の判定結果を取得する。", "path: prediction_id", "prediction detail", "必須"],
        ["履歴", "GET", "/api/predictions", "判定履歴の一覧を取得する。", "limit, offset", "predictions[]", "推奨"],
        ["履歴", "DELETE", "/api/predictions/{id}", "不要な判定履歴を削除する。", "path: prediction_id", "deleted: true", "推奨"],
        ["モデル", "GET", "/api/models/current", "現在使っているモデル情報を取得する。", "なし", "model_name, version, classes, description", "推奨"],
        ["説明", "GET", "/api/predictions/{id}/explanation", "結果の詳しい説明を取得する。", "path: prediction_id", "beginner_explanation, heatmap_note", "推奨"],
        ["ログ", "GET", "/api/error-logs", "判定失敗などのログを確認する。", "limit, offset", "error_logs[]", "将来"],
    ]

    db_rows = [
        ["テーブル", "カラム", "型", "内容", "例", "優先度"],
        ["predictions", "id", "INTEGER / PK", "判定結果ID", "1", "必須"],
        ["predictions", "original_image_path", "TEXT", "アップロード画像の保存先", "uploads/20260716_xxx.png", "必須"],
        ["predictions", "heatmap_image_path", "TEXT", "Grad-CAM画像の保存先", "heatmaps/20260716_xxx.png", "必須"],
        ["predictions", "class_name", "TEXT", "AIの分類結果", "cat", "必須"],
        ["predictions", "confidence", "REAL", "信頼度", "0.92", "必須"],
        ["predictions", "model_id", "INTEGER", "使用したモデルID", "1", "推奨"],
        ["predictions", "explanation", "TEXT", "初心者向けの簡単な説明", "AIは顔付近に注目しています", "推奨"],
        ["predictions", "created_at", "TEXT", "判定日時", "2026-07-16 11:20:00", "必須"],
        ["models", "id", "INTEGER / PK", "モデルID", "1", "推奨"],
        ["models", "name", "TEXT", "モデル名", "ResNet50 baseline", "推奨"],
        ["models", "version", "TEXT", "モデルのバージョン", "v1", "推奨"],
        ["models", "path", "TEXT", "モデルファイルの保存先", "model/baseline/model.pth", "推奨"],
        ["models", "description", "TEXT", "モデル説明", "画像分類用のbaselineモデル", "推奨"],
        ["error_logs", "id", "INTEGER / PK", "エラーログID", "1", "将来"],
        ["error_logs", "prediction_id", "INTEGER", "関連する判定ID", "1", "将来"],
        ["error_logs", "message", "TEXT", "エラー内容", "unsupported file type", "将来"],
        ["error_logs", "created_at", "TEXT", "エラー日時", "2026-07-16 11:20:00", "将来"],
    ]

    order_rows = [
        ["順番", "作業", "完了条件", "理由"],
        ["1", "画像アップロード画面を作る", "HTMLから画像を選び、プレビューできる", "最初にユーザー操作の入口を作る"],
        ["2", "FastAPIで画像を受け取る", "POST /api/predictions が画像を保存できる", "フロントとバックエンドをつなぐ"],
        ["3", "PyTorchモデルで判定する", "class_name と confidence を返す", "アプリの中心機能を作る"],
        ["4", "Grad-CAM画像を生成する", "heatmap_image_path を返す", "AIがどこを見たかを可視化する"],
        ["5", "結果画面を作る", "画像、結果、ヒートマップを表示できる", "baselineの価値が見える"],
        ["6", "SQLiteに保存する", "履歴として判定結果を残せる", "後で履歴画面につなげる"],
        ["7", "履歴画面を作る", "過去の判定結果を一覧表示できる", "学習・ポートフォリオとして見返せる"],
    ]

    story = [
        paragraph("AI_judge baseline specs", styles["Title"]),
        paragraph("画面別表示項目 / API設計 / DB設計 / 実装順メモ", styles["Subtitle"]),
    ]

    add_section(
        story,
        "1. 画面別表示項目",
        "baseline v1で各画面に置くもの、ボタン、遷移先、呼び出すAPIを整理する。",
        screen_rows,
        [24 * mm, 38 * mm, 50 * mm, 42 * mm, 38 * mm, 42 * mm, 18 * mm],
        styles,
    )
    story.append(PageBreak())
    add_section(
        story,
        "2. API設計",
        "フロントエンドとFastAPIの間で必要になるbaseline APIを整理する。",
        api_rows,
        [22 * mm, 17 * mm, 42 * mm, 58 * mm, 36 * mm, 62 * mm, 18 * mm],
        styles,
    )
    story.append(PageBreak())
    add_section(
        story,
        "3. DB設計",
        "SQLiteで保存する最低限のテーブルとカラムを整理する。画像本体はローカル保存し、DBにはパスを保存する。",
        db_rows,
        [28 * mm, 42 * mm, 30 * mm, 56 * mm, 60 * mm, 18 * mm],
        styles,
    )
    story.append(PageBreak())
    add_section(
        story,
        "4. 実装順メモ",
        "設計を作り込みすぎず、動くbaselineまで進めるための作成順。",
        order_rows,
        [18 * mm, 55 * mm, 78 * mm, 78 * mm],
        styles,
    )

    doc.build(story)


if __name__ == "__main__":
    main()
