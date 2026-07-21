// 1. HTMLの部品を取得する
const imageInput = document.getElementById("imageInput");
const previewImage = document.getElementById("previewImage");
const judgeButton = document.getElementById("judgeButton");
const result = document.getElementById("result");
const heatmapImage = document.getElementById("heatmapImage");


// 2. 画像が選ばれた時の処理
imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];

  if (!file) {
    result.textContent = "画像が選択されていません";
    return;
  }

  const imageUrl = URL.createObjectURL(file);
  previewImage.src = imageUrl;
  heatmapImage.hidden = true;
  heatmapImage.removeAttribute("src");

  result.textContent = `${file.name} を読み込みました`;
});


// 3. APIに画像を送信する関数
async function sendImageToAPI(file) {
  const formData = new FormData();
  formData.append("image", file);

  const response = await fetch("/api/predictions", {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    throw new Error("判定APIの呼び出しに失敗しました");
  }

  return response.json();
}


// 4. 判定結果を画面に表示する関数
function showPredictionResult(data) {
  const confidencePercent = (data.confidence * 100).toFixed(2);
  const label = data.class_name === "real" ? "実写画像" : "AI生成画像";
  const cacheMessage = data.from_cache ? " / 保存済み結果を使用" : "";

  result.textContent = `判定結果: ${label} / 信頼度: ${confidencePercent}%${cacheMessage}`;

  if (data.original_image_data_url) {
    previewImage.src = data.original_image_data_url;
  }

  if (data.heatmap_data_url) {
    heatmapImage.src = data.heatmap_data_url;
    heatmapImage.hidden = false;
  }
}

async function loadPredictionFromHistory() {
  const params = new URLSearchParams(window.location.search);
  const predictionId = params.get("prediction_id");

  if (!predictionId) {
    return;
  }

  try {
    result.textContent = "履歴を読み込んでいます...";
    const response = await fetch(`/api/predictions/${predictionId}`);
    if (!response.ok) {
      throw new Error("履歴詳細APIの呼び出しに失敗しました");
    }

    const data = await response.json();
    showPredictionResult(data);
  } catch (error) {
    result.textContent = "履歴の読み込みに失敗しました";
  }
}


// 5. 判定ボタンが押された時の処理
judgeButton.addEventListener("click", async () => {
  const file = imageInput.files[0];

  if (!file) {
    result.textContent = "画像を選択してください";
    return;
  }

  try {
    judgeButton.disabled = true;
    result.textContent = "判定中です...";

    const data = await sendImageToAPI(file);
    showPredictionResult(data);
  } catch (error) {
    result.textContent = "判定に失敗しました";
  } finally {
    judgeButton.disabled = false;
  }
});

loadPredictionFromHistory();
