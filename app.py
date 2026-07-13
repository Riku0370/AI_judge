from pathlib import Path

import streamlit as st
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "resnet18_real_fake.pth"


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


@st.cache_resource
def load_model():
    device = get_device()

    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 2)

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=False,
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    class_to_idx = checkpoint.get(
        "class_to_idx",
        {"fake": 0, "real": 1},
    )

    idx_to_class = {
        index: class_name
        for class_name, index in class_to_idx.items()
    }

    return model, idx_to_class, device


transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


def predict(image):
    model, idx_to_class, device = load_model()

    image_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted_index = probabilities.max(dim=1)

    label = idx_to_class[predicted_index.item()]
    probability = confidence.item()

    return label, probability, probabilities[0].cpu()


st.set_page_config(
    page_title="AI Image Judge",
    page_icon="🔍",
)

st.title("AI Image Judge")
st.write("画像が実写かAI生成画像かを判定します。")

if not MODEL_PATH.exists():
    st.error(
        f"モデルが見つかりません。\n\n"
        f"`{MODEL_PATH.name}`をAI_judge直下に置いてください。"
    )
    st.stop()

uploaded_file = st.file_uploader(
    "判定したい画像を選択してください",
    type=["jpg", "jpeg", "png", "webp"],
)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")

    st.image(
        image,
        caption="アップロード画像",
        use_container_width=True,
    )

    if st.button("判定する"):
        with st.spinner("判定中..."):
            label, confidence, probabilities = predict(image)

        if label == "real":
            st.success("判定結果：実写画像")
        else:
            st.warning("判定結果：AI生成画像")

        st.metric(
            label="信頼度",
            value=f"{confidence * 100:.2f}%",
        )

        st.write(
            {
                "AI生成画像": f"{probabilities[0].item() * 100:.2f}%",
                "実写画像": f"{probabilities[1].item() * 100:.2f}%",
            }
        )

        st.caption(
            "現在は開発途中のモデルです。判定結果が常に正しいとは限りません。"
        )