import torch
from torchvision import transforms
from PIL import Image
import sys
import os
import torch.nn as nn

# 1. Load the model
model = nn.Sequential(
    # Input: [B, 3, 64, 64] → [B, 3*64*64 = 12288]
    nn.Flatten(),
    nn.Linear(3 * 64 * 64, 512),    # Layer 1: 12288 → 512
    nn.ReLU(),
    nn.Dropout(0.3),

    nn.Linear(512, 256),             # Layer 2: 512 → 256
    nn.ReLU(),
    nn.Dropout(0.3),

    nn.Linear(256, 128),             # Layer 3: 256 → 128
    nn.ReLU(),
    nn.Dropout(0.2),

    nn.Linear(128, 64),              # Layer 4: 128 → 64
    nn.ReLU(),
    nn.Dropout(0.2),

    nn.Linear(64, 1),                # Layer 5: 64 → 1 (output)
    nn.Sigmoid()                     # Output: probability it's a cat
)
model.load_state_dict(torch.load(
    "cat_model.pth", map_location=torch.device('cpu')))
model.eval()

# 2. Define transform (same as training)
transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor()
])

# 3. Load and process image


def predict_image(img_path):
    if not os.path.exists(img_path):
        print(f"❌ Error: Image '{img_path}' does not exist.")
        return
    image = Image.open(img_path).convert("RGB")
    tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        prob = model(tensor).item()
    return prob


# 4. Run prediction on image path passed via command line
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python CatAI.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    prob = predict_image(image_path)

    if prob is not None:
        print(f"🐱 Cat probability: {prob:.3f}")
