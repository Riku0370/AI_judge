from PIL import Image
import os
import pandas as pd
import torchvision.transforms as transforms
from torch.utils.data import Dataset

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
        label = os.path.join(self.df.iloc[idx]["label"])

        img = Image.open(image_path).convert("RGB")

        if self.transform:
            img = self.dftransform(img)

        if label == "real":
            label = 1
        elif label == "fake":
            label = 0
        
        return img, label