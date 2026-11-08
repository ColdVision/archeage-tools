#!/usr/bin/env python3
"""Подложка карты: плитки Worldmap_Gamscom (стилизованная карта игры) -> обрезка по области -> assets/worldmap.jpg.
Плитки получить из X5Viewer: /api/texture?path=X5/Content/UI/Graphic/Texture/Common/WorldMap/Worldmap_Gamscom/WorldmapVT_A_B.uasset
(сохранить как A_B.png). Плитка 12288 px в углу холста 16384, сетка 3 (X) x 4 (Y); целый мир 36864 x 49152 px.
Использование: python tools/trade/build_map.py <папка с плитками> [выход] 
Параметры обрезки (в пикселях полного мира) должны совпадать с константами CROP_* в index.html."""
import sys, os
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
X0, Y0, W, H, K = 4220, 22460, 19656, 11936, 4   # обрезка и делитель (K делит все числа)
src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "trade", "worldmap.jpg")
canvas = Image.new("RGB", (W // K, H // K))
for a in range(3):
    for b in range(4):
        tx0, ty0 = a * 12288, b * 12288
        ix0, iy0, ix1, iy1 = max(X0, tx0), max(Y0, ty0), min(X0 + W, tx0 + 12288), min(Y0 + H, ty0 + 12288)
        if ix0 >= ix1 or iy0 >= iy1: continue
        im = Image.open(os.path.join(src, "%d_%d.png" % (a, b))).convert("RGB").crop((ix0 - tx0, iy0 - ty0, ix1 - tx0, iy1 - ty0)).reduce(K)
        canvas.paste(im, ((ix0 - X0) // K, (iy0 - Y0) // K))
canvas.save(out, quality=82, optimize=True)
print(canvas.size, os.path.getsize(out))
