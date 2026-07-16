// 1. HTMLの部品を取得する
const imageInput = document.getElementById("imageInput");
const previewImage = document.getElementById("previewImage");
const judgeButton = document.getElementById("judgeButton");
const result = document.getElementById("result");


// 2. 画像が選ばれた時の処理
imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];

  if (!file) {
    result.textContent = "画像が選択されていません";
    return;
  }

  const imageUrl = URL.createObjectURL(file);
  previewImage.src = imageUrl;

  result.textContent = "画像を読み込みました";
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

// 4. 判定ボタンが押された時の処理
judgeButton.addEventListener("click", async () => {
  const file = imageInput.files[0];

  if (!file) {
    result.textContent = "画像を選択してください";
    return;
  }

  try {
    const data = await sendImageToAPI(file);
    console.log(data);
    result.textContent = `判定結果: ${data.class_name} / 信頼度: ${data.confidence}`;
  } catch (error) {
    result.textContent = "判定に失敗しました";
  }
});