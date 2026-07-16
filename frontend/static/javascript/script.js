const imageInput = document.getElementById("imageInput");
const judgeButton = document.getElementById("judgeButton");
const result = document.getElementById("result");
const previewImage = document.getElementById("previewImage");

imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];

    if (!file) {
        result.textContent = "画像を選択してください";
        previewImage.src = "";
        return;
    }

    const ImageURL = URL.createObjectURL(file);
    previewImage.src = ImageURL;

    result.textContent = "判定準備OKです";
});