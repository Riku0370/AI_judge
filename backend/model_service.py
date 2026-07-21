import numpy as np
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms

from .config import MODEL_PATH


def get_device():
    # MacのMPSが使える場合はGPU系の処理を使い、なければCPUで推論する。
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


device = get_device()

# 学習時と同じResNet50構造を作り、最後の分類層だけ2クラス用にする。
model = models.resnet50(weights=None)
model.fc = nn.Linear(model.fc.in_features, 2)

# 保存済みcheckpointを読み込んで、モデルに学習済みパラメータを反映する。
checkpoint = torch.load(MODEL_PATH, map_location=device)
model.load_state_dict(checkpoint["model_state_dict"])
model.to(device)
model.eval()

# ImageFolderのクラス順をcheckpointから復元する。
class_to_idx = checkpoint.get("class_to_idx", {"fake": 0, "real": 1})
idx_to_class = {
    index: class_name
    for class_name, index in class_to_idx.items()
}

# 学習時と同じ前処理を推論時にも使う。
image_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


def make_heatmap_overlay(original_image, cam):
    # 0から1のGrad-CAMを画像サイズまで拡大し、元画像の上に赤色で重ねる。
    cam_np = cam.detach().cpu().numpy()
    cam_image = Image.fromarray(np.uint8(cam_np * 255))
    cam_image = cam_image.resize(original_image.size, resample=Image.BILINEAR)

    heat = np.array(cam_image) / 255.0
    overlay_array = np.zeros((original_image.height, original_image.width, 4), dtype=np.uint8)
    overlay_array[..., 0] = 255
    overlay_array[..., 1] = np.uint8(180 * heat)
    overlay_array[..., 3] = np.uint8(130 * heat)

    base = original_image.convert("RGBA")
    overlay = Image.fromarray(overlay_array, mode="RGBA")
    return Image.alpha_composite(base, overlay).convert("RGB")


def predict_with_gradcam(pil_image):
    # hookが保存する場所。forwardで特徴マップ、backwardで勾配がここに入る。
    saved_values = {
        "features": None,
        "gradients": None,
    }

    def save_features(module, inputs, output):
        saved_values["features"] = output

    def save_gradients(module, grad_input, grad_output):
        saved_values["gradients"] = grad_output[0]

    # ResNet50の最後に近い畳み込み層を見る。
    target_layer = model.layer4[-1]
    forward_handle = target_layer.register_forward_hook(save_features)
    backward_handle = target_layer.register_full_backward_hook(save_gradients)

    try:
        image_tensor = image_transform(pil_image).unsqueeze(0).to(device)

        # Grad-CAMではbackwardが必要なので、torch.no_grad()は使わない。
        outputs = model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)[0]
        confidence, predicted_index = probabilities.max(dim=0)
        class_name = idx_to_class[predicted_index.item()]

        model.zero_grad()
        target_score = outputs[0, predicted_index]
        target_score.backward()

        features = saved_values["features"]
        gradients = saved_values["gradients"]

        # 勾配の平均を「各特徴マップの重要度」として使い、特徴マップに掛ける。
        weights = gradients.mean(dim=(2, 3), keepdim=True)
        cam = (weights * features).sum(dim=1)
        cam = torch.relu(cam).squeeze()
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)

        heatmap_image = make_heatmap_overlay(pil_image, cam)

        return {
            "class_name": class_name,
            "confidence": confidence.item(),
            "fake": probabilities[class_to_idx["fake"]].item(),
            "real": probabilities[class_to_idx["real"]].item(),
            "heatmap_image": heatmap_image,
        }
    finally:
        forward_handle.remove()
        backward_handle.remove()


def get_current_model_info():
    return {
        "model_name": "ResNet50 baseline",
        "version": "dev",
        "classes": list(class_to_idx.keys()),
        "description": "PyTorch ResNet50 model for real/fake image classification.",
    }
