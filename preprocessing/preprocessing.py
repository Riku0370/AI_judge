import os
import pandas as pd
from PIL import Image
real_path = "archive/Real faces"
fake_path = "archive/Fake faces"
data = pd.read_csv("archive/metadata.csv")
sizes = {}
hashes = {}
duplicates = []


#pathにある.pngファイルの数を数える
def count_png_files(path):
    files = [f for f in os.listdir(path) if f.endswith(".png")]
    print(path + ":", len(files))
    print("最初の5個:", files[:5])
    print("最後の5個:", files[-5:])

    
#metadata.csvの内容を確認する
def metadata_check():
    fake_data = data[
        data["filepath"].str.contains("fake_")
        & (data["label"] == "fake")
    ]
    real_data = data[
        data["filepath"].str.contains("real_")
        & (data["label"] == "real")
    ]
    print("fakeデータ:", len(fake_data))
    print("realデータ:", len(real_data))
    print("metadata.csvの行数:", len(data))

#metadata.csvに記載されているファイルが実際に存在するか確認する
def check_missing_files():
    missing_files = []
    for path in data["filepath"]:
        full_path = os.path.join("archive", path)
        if not os.path.exists(full_path):
            missing_files.append(path)
    print("存在しない画像:", len(missing_files))
    for file in missing_files[:10]:
        print(file)

#画像のサイズを確認する
def check_image_dimensions():
    for path in data["filepath"]:
        full_path = os.path.join("archive", path)
        img = Image.open(full_path)
        size = img.size
        sizes[size] = sizes.get(size, 0) + 1
    print(sizes)

#画像の重複を確認する
def check_duplicate_images():
    print("画像の重複を確認中...")
    for path in data["filepath"]:
        full_path = os.path.join("archive", path)
        img = Image.open(full_path)
        img_hash = hash(img.tobytes())
        if img_hash in hashes:
            duplicates.append(path)
        hashes[img_hash] = path
    print("重複した画像:", len(duplicates))
    for file in duplicates:
        print(file)