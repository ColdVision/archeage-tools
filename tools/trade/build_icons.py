#!/usr/bin/env python3
"""Иконки товаров и предметов (материалы, награды) -> assets/icons/*.png (64x64).

Источник картинок — файлы игры через HTTP-API X5Viewer (запустить: X5Viewer.exe --no-browser, порт 8766):
  /api/texture?path=X5/Content/UI/....uasset  (только чтение).
Иконки предметов: Item.csv (FK_iconId) -> Icon.csv (icon) -> путь текстуры.
Иконки торговых товаров: в клиенте таблица TradeGood пуста, соответствие «товар -> текстура» взято с questlog.gg
(только имена текстур, ниже), сами картинки берутся из игры.

Использование: python tools/trade/build_icons.py [--cms DIR] [--api http://127.0.0.1:8766]
"""
import argparse, csv, io, json, os, sys, urllib.request
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # корень сайта (Site)
AA = r"D:\Claude\aa-tools"

# товар -> имя текстуры в Item/Trade/ (с questlog.gg)
def good_icons():
    m = {1101: "UI_Item_TradeGoods_Bundle_BlueSalt", 1102: "UI_Item_TradeGoods_Sack_BlueSalt",
         1103: "UI_Item_TradeGoods_Oak_Shadowhk", 1104: "UI_Item_TradeGoods_Sack_Antiqus",
         1162: "UI_Item_TradeGoods_Type_Agricultural01", 1163: "UI_Item_TradeGoods_WoodenBox_Shadowhk",
         1164: "UI_Item_TradeGoods_WoodenBox_Antiqus"}
    def rng(a, b, name):
        for i in range(a, b + 1): m[i] = "UI_Item_TradeGoods_Type_" + name
    rng(1105, 1106, "Sacks01"); rng(1107, 1109, "Agricultural01"); rng(1116, 1118, "Archeum01")
    rng(1119, 1121, "Wood01"); rng(1122, 1124, "Leather01"); rng(1125, 1127, "Cotton01")
    rng(1128, 1130, "Petal01"); rng(1131, 1133, "Marble01"); rng(1134, 1136, "Iron01")
    for i in (1137, 1140, 1141, 1142, 1143, 1144, 1145, 1147, 1168): m[i] = "UI_Item_TradeGoods_Type_Looting01"
    for i in (1152, 1155, 1166): m[i] = "UI_Item_TradeGoods_Type_WeaponArtifact01"
    for i in (1154, 1156, 1167): m[i] = "UI_Item_TradeGoods_Type_ArmorArtifact01"
    for i in (1157, 1158, 1159, 1160, 1161, 1165): m[i] = "UI_Item_TradeGoods_Type_Looting02"
    return {k: "/Game/UI/Graphic/Texture/Item/Trade/%s.%s" % (v, v) for k, v in m.items()}


def rd(cms, name):
    t = open(os.path.join(cms, name + ".csv"), "rb").read().replace(b"\x00", b"").decode("utf-8", "replace")
    return list(csv.DictReader(io.StringIO(t)))


def fetch(api, game_path, out):
    # /Game/UI/x/y.y -> X5/Content/UI/x/y.uasset
    p = game_path.split(".")[0].replace("/Game/", "X5/Content/", 1) + ".uasset"
    data = urllib.request.urlopen(api + "/api/texture?path=" + urllib.request.quote(p), timeout=120).read()
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    im.thumbnail((64, 64), Image.LANCZOS)
    im.save(out, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cms", default=AA + r"\game-data-26495283\X5\Content\Design\CMS")
    ap.add_argument("--api", default="http://127.0.0.1:8766")
    a = ap.parse_args()
    out_dir = os.path.join(ROOT, "assets", "trade", "icons"); os.makedirs(out_dir, exist_ok=True)
    src = json.load(open(os.path.join(ROOT, "data", "trade", "manual", "trade-goods.json"), encoding="utf-8"))["goods"]
    items = set()
    for r in src.values():
        for m in r[5]: items.add(m[0])
        for v in r[4].values():
            if isinstance(v, list): items.add(v[0])
    item_tbl = {r["id"]: r for r in rd(a.cms, "Item")}
    icon_tbl = {r["id"]: r["icon"] for r in rd(a.cms, "Icon")}
    ok = bad = 0
    for iid in sorted(items):
        r = item_tbl.get(str(iid)); path = r and icon_tbl.get(r["FK_iconId"])
        out = os.path.join(out_dir, "i%d.png" % iid)
        if os.path.exists(out): ok += 1; continue
        try:
            if not path: raise ValueError("нет иконки в Icon.csv")
            fetch(a.api, path, out); ok += 1
        except Exception as e:
            bad += 1; print("предмет", iid, e)
    cache = {}
    for gid, path in sorted(good_icons().items()):
        out = os.path.join(out_dir, "g%d.png" % gid)
        if os.path.exists(out): ok += 1; continue
        try:
            if path in cache: Image.open(cache[path]).save(out)
            else: fetch(a.api, path, out); cache[path] = out
            ok += 1
        except Exception as e:
            bad += 1; print("товар", gid, e)
    print("иконок:", ok, "ошибок:", bad)


if __name__ == "__main__":
    main()
