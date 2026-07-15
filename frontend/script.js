const imageInput = document.querySelector("#imageInput");
const dropZone = document.querySelector("#dropZone");
const previewImage = document.querySelector("#previewImage");
const emptyPreview = document.querySelector("#emptyPreview");
const judgeButton = document.querySelector("#judgeButton");
const resultLabel = document.querySelector("#resultLabel");
const confidenceValue = document.querySelector("#confidenceValue");
const confidenceBar = document.querySelector("#confidenceBar");
const fakeScore = document.querySelector("#fakeScore");
const realScore = document.querySelector("#realScore");
const resultNote = document.querySelector("#resultNote");

let selectedFile = null;

function formatPercent(value) {
  return `${Math.round(value * 100)}%`;
}

function resetResult() {
  resultLabel.textContent = "未判定";
  confidenceValue.textContent = "--%";
  confidenceBar.style.width = "0%";
  fakeScore.textContent = "--%";
  realScore.textContent = "--%";
  resultNote.textContent = "画像を選ぶと判定できます。";
}

function loadImage(file) {
  if (!file || !file.type.startsWith("image/")) {
    return;
  }

  selectedFile = file;
  const imageUrl = URL.createObjectURL(file);
  previewImage.src = imageUrl;
  previewImage.hidden = false;
  emptyPreview.hidden = true;
  judgeButton.disabled = false;
  resetResult();
  resultNote.textContent = "画像を読み込みました。";
}

function createMockPrediction(file) {
  const nameScore = [...file.name].reduce((sum, char) => {
    return sum + char.charCodeAt(0);
  }, 0);
  const base = ((nameScore + file.size) % 36) / 100;
  const fakeProbability = 0.32 + base;
  const clampedFake = Math.min(0.86, Math.max(0.14, fakeProbability));
  const realProbability = 1 - clampedFake;
  const isFake = clampedFake >= realProbability;
  const confidence = Math.max(clampedFake, realProbability);

  return {
    label: isFake ? "AI生成画像の可能性" : "実写画像の可能性",
    confidence,
    fakeProbability: clampedFake,
    realProbability,
  };
}

function showPrediction(prediction) {
  resultLabel.textContent = prediction.label;
  confidenceValue.textContent = formatPercent(prediction.confidence);
  confidenceBar.style.width = formatPercent(prediction.confidence);
  fakeScore.textContent = formatPercent(prediction.fakeProbability);
  realScore.textContent = formatPercent(prediction.realProbability);
  resultNote.textContent = "現在は画面確認用の仮判定です。";
}

imageInput.addEventListener("change", (event) => {
  const [file] = event.target.files;
  loadImage(file);
});

judgeButton.addEventListener("click", () => {
  if (!selectedFile) {
    return;
  }

  judgeButton.disabled = true;
  resultLabel.textContent = "判定中";
  resultNote.textContent = "画像を確認しています。";

  window.setTimeout(() => {
    showPrediction(createMockPrediction(selectedFile));
    judgeButton.disabled = false;
  }, 520);
});

dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("is-dragging");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("is-dragging");
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("is-dragging");
  const [file] = event.dataTransfer.files;
  loadImage(file);
});
