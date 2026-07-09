from PIL import Image
import os
import pandas as pd
import torchvision.transforms as transforms
from torch.utils.data import Dataset
import torch

#Datasetを中に書いているのは別のファイルを読み込んだ際、そこでPytochのDatasetが継承されるため
class FaceDataset(Dataset):

    def __init__(self, csv_file, transform=None):

        self.df = pd.read_csv(csv_file)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor()
        ])

    def __len__(self):

        return len(self.df)

    def __getitem__(self, idx):

        image_path = os.path.join(
            "archive",
            self.df.iloc[idx]["filepath"]
        )

        label = self.df.iloc[idx]["label"]

        img = Image.open(image_path).convert("RGB")

        if self.transform:
            img = self.transform(img)

        if label == "real":
            label = 1
        elif label == "fake":
            label = 0

        return img,  torch.tensor(label, dtype=torch.long)
    

def load_image_as_tensor(image_path, label):
    img = Image.open(image_path).convert("RGB")
    transform = transforms.Compose([
        transforms.Resize((224,224)),
        transforms.ToTensor()
    ])
    transformed_img = transform(img)
    if label == "real":
        label = 1
    elif label == "fake":
        label = 0
    return transformed_img, label
