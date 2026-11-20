"""Генерирует assets/donate-qr.svg локально (OpenCV QRCodeEncoder) из ссылки поддержки. Без внешних сервисов.
   python tools/make_qr.py [ссылка]"""
import os, sys, cv2, numpy as np
URL = sys.argv[1] if len(sys.argv) > 1 else "https://dalink.to/coldvision"
enc = cv2.QRCodeEncoder.create()
img = enc.encode(URL)                      # 255 = светлый, 0 = тёмный; есть тихая зона
b = (img < 128).astype(np.uint8)
ys, xs = np.where(b)
b = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
n = b.shape[0]
step = None
# размер модуля: ищем по первой строке (finder pattern = 7 модулей)
row = b[0]; run = 0
while run < len(row) and row[run]: run += 1
step = max(1, run // 7)
m = n // step
mod = np.array([[b[r * step + step // 2, c * step + step // 2] for c in range(m)] for r in range(m)])
q = 2
parts = ["M%d %dh1v1h-1z" % (c + q, r + q) for r in range(m) for c in range(m) if mod[r, c]]
svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" shape-rendering="crispEdges"><rect width="100%%" height="100%%" fill="#fff"/><path fill="#000" d="%s"/></svg>\n'
       % (m + 2 * q, m + 2 * q, "".join(parts)))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "donate-qr.svg")
open(out, "w", encoding="utf-8").write(svg)
# проверка: рендерим SVG-матрицу обратно и декодируем
big = np.full(((m + 2 * q) * 10,) * 2, 255, np.uint8)
for r in range(m):
    for c in range(m):
        if mod[r, c]: big[(r + q) * 10:(r + q + 1) * 10, (c + q) * 10:(c + q + 1) * 10] = 0
txt, _, _ = cv2.QRCodeDetector().detectAndDecode(big)
print("модулей:", m, "декодировано:", txt, "OK" if txt == URL else "ОШИБКА")
