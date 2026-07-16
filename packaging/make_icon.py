"""Genere packaging/icon.ico multi-resolutions a partir de assets/logo.jpg."""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "logo.jpg")
DEST = os.path.join(ROOT, "packaging", "icon.ico")

img = Image.open(SRC).convert("RGBA")

# Cadrer le logo (non carre a l'origine) dans un canevas carre transparent,
# centre, pour eviter des icones deformees (largeur != hauteur) dans la
# barre de titre / barre des taches Windows.
side = max(img.width, img.height)
square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))

sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
square.save(DEST, format="ICO", sizes=sizes)
print(f"Icone generee : {DEST}")
