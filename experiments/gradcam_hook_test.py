from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "output" / "resnet50_real_fake.pth"
SAMPLE_IMAGE_PATH = BASE_DIR / "archive" / "rvf10k" / "train" / "real" / "69945.jpg"

def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")

def build_model(device):
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, 2)

    checkpoint = torch.load(MODEL_PATH, map_location = device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    class_to_idx = checkpoint.get("class_to_idx", {"fake": 0, "real": 1})
    idx_to_class = {
        index: class_name
        for class_name, index in class_to_idx.items()
    }
    return model, idx_to_class

def save_features(module, inputs, output):
    saved_values["features"] = output
    print("forward hook: 特徴マップを保存しました")

def save_gradients(module, grad_input, grad_output):
    saved_values["gradients"] = grad_output[0]
    print("backward hook: 勾配を保存しました")

image_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])

saved_values = {
    "features": None,
    "gradients": None,
}

def main():
    device = get_device()
    model, idx_to_class = build_model(device)

    target_layer = model.layer4[-1]

    forward_handle = target_layer.register_forward_hook(save_features)
    backward_handle = target_layer.register_full_backward_hook(save_gradients)

    image = Image.open(SAMPLE_IMAGE_PATH).convert("RGB")
    image_tensor = image_transform(image).unsqueeze(0).to(device)

    outputs = model(image_tensor)

    probabilities = torch.softmax(outputs, dim=1)[0]
    confidence, predicted_index = probabilities.max(dim=0)
    class_name = idx_to_class[predicted_index.item()]

    model.zero_grad()
    target_score = outputs[0, predicted_index]
    target_score.backward()

    features = saved_values["features"]
    gradients = saved_values["gradients"]

    print("判定:", class_name)
    print("信頼度:", f"{confidence.item() * 100:.2f}%")
    print("特徴マップ shape:", tuple(features.shape))
    print("勾配 shape:", tuple(gradients.shape))
    print(features[0, 0])
    print(gradients[0, 0])
    print(features.min(), features.max())
    print(gradients.min(), gradients.max())
    forward_handle.remove()
    backward_handle.remove()
    weights = gradients.mean(dim=(2, 3), keepdim=True)
    cam = (weights * features).sum(dim=1)
    cam = torch.relu(cam)
    cam = cam.squeeze()
    cam = cam - cam.min()
    cam = cam / cam.max()
    print("CAM shape:", tuple(cam.shape))
    print("CAM min:", cam.min().item())
    print("CAM max:", cam.max().item())

    cam_np = cam.detach().cpu().numpy()

    cam_image = Image.fromarray(np.uint8(cam_np * 255))
    cam_image = cam_image.resize(image.size)

    plt.imshow(image)
    plt.imshow(cam_image, cmap="jet", alpha=0.45)
    plt.axis("off")
    plt.savefig(BASE_DIR / "experiments" / "gradcam_test.png", bbox_inches="tight", pad_inches=0)
    plt.close()

if __name__ == "__main__":
    main()