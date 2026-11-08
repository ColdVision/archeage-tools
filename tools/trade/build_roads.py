#!/usr/bin/env python3
"""Маршруты между торговыми постами вдоль дорог -> data/roads.js.

Дороги выделяются по цвету с assets/worldmap.jpg (тёмно-коричневые линии), мелкий шум отбрасывается.
Кратчайший путь ищется алгоритмом Дейкстры на уменьшенной сетке: по дороге шаг стоит 1, вне дороги OFF
(так пути не режут напрямик, но могут перескочить пробел пунктирной дороги).
Позиции постов должны совпадать с S.pos по умолчанию в index.html (POS ниже).
Использование: python tools/trade/build_roads.py
"""
import heapq, json, os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # корень сайта (Site)
W, H = 4914, 2984
POS = {1100: [0.5719, 0.6576], 1000: [0.6365, 0.7151], 2000: [0.3978, 0.3994],
       2100: [0.3605, 0.6465], 3000: [0.581, 0.4318], 3100: [0.5806, 0.2612]}
STEP = 3        # размер ячейки сетки, px
OFF = 18        # цена шага вне дороги
MIN_COMP = 150  # минимальный размер связной дороги, px


def road_mask():
    a = np.array(Image.open(os.path.join(ROOT, "assets", "trade", "worldmap.jpg")).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (r < 115) & (r - b > 25) & (g < 90) & (r > 45)
    # убрать мелкие компоненты (штриховка гор, значки)
    lab = np.zeros(m.shape, np.int32)
    ys, xs = np.nonzero(m)
    keep = np.zeros(m.shape, bool)
    n = 0
    for y0, x0 in zip(ys, xs):
        if lab[y0, x0]:
            continue
        n += 1
        st = [(y0, x0)]; lab[y0, x0] = n; comp = []
        while st:
            y, x = st.pop(); comp.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and m[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = n; st.append((yy, xx))
        if len(comp) >= MIN_COMP:
            for y, x in comp:
                keep[y, x] = True
    return keep


def main():
    m = road_mask()
    gh, gw = H // STEP, W // STEP
    cell = m[:gh * STEP, :gw * STEP].reshape(gh, STEP, gw, STEP).any(axis=(1, 3))
    cost = np.where(cell, 1.0, float(OFF))
    print("дорожных ячеек:", int(cell.sum()), "из", gh * gw)
    nb = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]

    def dijkstra(src):
        dist = np.full((gh, gw), np.inf); prev = {}
        dist[src] = 0; pq = [(0.0, src)]
        while pq:
            d, (y, x) = heapq.heappop(pq)
            if d > dist[y, x]:
                continue
            for dy, dx, k in nb:
                yy, xx = y + dy, x + dx
                if 0 <= yy < gh and 0 <= xx < gw:
                    nd = d + k * cost[yy, xx]
                    if nd < dist[yy, xx]:
                        dist[yy, xx] = nd; prev[(yy, xx)] = (y, x); heapq.heappush(pq, (nd, (yy, xx)))
        return prev

    def cellof(p):
        return (min(gh - 1, int(p[1] * H / STEP)), min(gw - 1, int(p[0] * W / STEP)))

    ids = sorted(POS)
    routes = {}
    for i, a in enumerate(ids):
        prev = dijkstra(cellof(POS[a]))
        for b in ids[i + 1:]:
            path = []; c = cellof(POS[b]); s = cellof(POS[a])
            while c != s:
                path.append(c); c = prev[c]
            path.append(s); path.reverse()
            pts = [[round((x + .5) * STEP / W, 4), round((y + .5) * STEP / H, 4)] for y, x in path]
            pts[0] = POS[a]; pts[-1] = POS[b]
            # прореживание: каждая 2-я точка
            pts = pts[::2] + ([pts[-1]] if len(pts) % 2 == 0 else [])
            routes["%d-%d" % (a, b)] = pts
            print(a, b, len(pts), "точек")
    out = {"pos": {str(k): v for k, v in POS.items()}, "routes": routes}
    open(os.path.join(ROOT, "data", "trade", "roads.js"), "w", encoding="utf-8").write(
        "window.TR_ROADS = " + json.dumps(out, separators=(",", ":")) + ";\n")


if __name__ == "__main__":
    main()
