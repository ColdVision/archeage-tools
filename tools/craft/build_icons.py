#!/usr/bin/env python3
"""Иконки предметов -> assets/icons/<FK_iconId>.png (48x48, только чтение игры).

Источник — файлы игры через HTTP-API X5Viewer (запустить: X5Viewer.exe --no-browser, порт 8766):
  /api/texture?path=X5/Content/UI/....uasset
Соответствие: Item.csv (FK_iconId) -> Icon.csv (icon) -> путь текстуры. Ничего не скачивается из сети.
Использование: python tools/craft/build_icons.py [--cms DIR] [--api http://127.0.0.1:8766] [--size 48]
"""
import argparse, csv, io, os, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # корень сайта (Site)
AA = r"D:\Claude\aa-tools"


def rd(cms, name):
    t = open(os.path.join(cms, name + ".csv"), "rb").read().replace(b"\x00", b"").decode("utf-8-sig", "replace")
    return list(csv.DictReader(io.StringIO(t, newline="")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cms", default=AA + r"\game-data-26495283\X5\Content\Design\CMS")
    ap.add_argument("--api", default="http://127.0.0.1:8766")
    ap.add_argument("--size", type=int, default=48)
    a = ap.parse_args()
    out_dir = os.path.join(ROOT, "assets", "craft", "icons"); os.makedirs(out_dir, exist_ok=True)
    icon_tbl = {r["id"]: r["icon"] for r in rd(a.cms, "Icon")}
    ids = sorted({r["FK_iconId"] for r in rd(a.cms, "Item") if r["FK_iconId"]}, key=int)

    def job(iid):
        out = os.path.join(out_dir, iid + ".png")
        if os.path.exists(out):
            return True, iid, ""
        path = icon_tbl.get(iid)
        if not path:
            return False, iid, "нет в Icon.csv"
        try:
            p = path.split(".")[0].replace("/Game/", "X5/Content/", 1) + ".uasset"
            data = urllib.request.urlopen(a.api + "/api/texture?path=" + urllib.parse.quote(p), timeout=120).read()
            im = Image.open(io.BytesIO(data)).convert("RGBA")
            im.thumbnail((a.size, a.size), Image.LANCZOS)
            im.save(out, optimize=True)
            return True, iid, ""
        except Exception as e:
            return False, iid, str(e)[:80]

    ok = bad = 0
    with ThreadPoolExecutor(4) as ex:
        for good, iid, err in ex.map(job, ids):
            if good: ok += 1
            else:
                bad += 1
                if bad <= 10: print("иконка", iid, err)
    print("иконок: %d, ошибок: %d" % (ok, bad))


if __name__ == "__main__":
    main()
