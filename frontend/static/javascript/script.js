// 1. HTMLの部品を取得する
const imageInput = document.getElementById("imageInput");
const previewImage = document.getElementById("previewImage");
const judgeButton = document.getElementById("judgeButton");
const result = document.getElementById("result");
const heatmapImage = document.getElementById("heatmapImage");
const reloadHistoryButton = document.getElementById("reloadHistoryButton");
const historyList = document.getElementById("historyList");


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
    const response = await fetch("http://127.0.0.1:8000/api/predictions", {
        method: "POST",
        body: formData
    });
    const data = await response.json();
    return data;
}

// 4. DBに保存された判定履歴を取得する関数
async function loadPredictionHistory() {
  const response = await fetch("http://127.0.0.1:8000/api/predictions/history");
  const history = await response.json();
  renderPredictionHistory(history);
}

// 5. 判定履歴を画面に表示する関数
function renderPredictionHistory(history) {
  if (!history.length) {
    historyList.innerHTML = '<p class="empty-text">まだ判定履歴はありません</p>';
    return;
  }

  historyList.innerHTML = "";

  history.forEach((item) => {
    const confidencePercent = (item.confidence * 100).toFixed(2);
    const label = item.class_name === "real" ? "実写画像" : "AI生成画像";

    const historyItem = document.createElement("div");
    historyItem.className = "history-item";

    const filename = document.createElement("div");
    filename.className = "history-filename";
    filename.title = item.filename;
    filename.textContent = item.filename;

    const className = document.createElement("div");
    className.textContent = label;

    const confidence = document.createElement("div");
    confidence.textContent = `${confidencePercent}%`;

    const createdAt = document.createElement("div");
    createdAt.className = "history-meta";
    createdAt.textContent = item.created_at;

    historyItem.append(filename, className, confidence, createdAt);
    historyList.appendChild(historyItem);
  });
}

reloadHistoryButton.addEventListener("click", loadPredictionHistory);

// 6. 判定ボタンが押された時の処理
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
    console.log(data);
    const confidencePercent = (data.confidence * 100).toFixed(2);
    const label = data.class_name === "real" ? "実写画像" : "AI生成画像";
    const cacheMessage = data.from_cache ? " / 保存済み結果を使用" : "";
    result.textContent = `判定結果: ${label} / 信頼度: ${confidencePercent}%${cacheMessage}`;

    if (data.heatmap_data_url) {
      heatmapImage.src = data.heatmap_data_url;
      heatmapImage.hidden = false;
    }

    await loadPredictionHistory();
  } catch (error) {
    result.textContent = "判定に失敗しました";
  } finally {
    judgeButton.disabled = false;
  }
});

loadPredictionHistory();
