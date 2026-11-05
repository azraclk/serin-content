import os
import sys

from PIL import Image

src = sys.argv[1] if len(sys.argv) > 1 else "output"
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "images", "meditations")
os.makedirs(out, exist_ok=True)
for name in sorted(os.listdir(src)):
    if name.endswith(".png"):
        target = os.path.join(out, name[:-4] + ".webp")
        Image.open(os.path.join(src, name)).convert("RGB").save(target, lossless=True, method=6)
        print("written:", target)
