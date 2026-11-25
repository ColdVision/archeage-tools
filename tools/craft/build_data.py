#!/usr/bin/env python3
"""Сборка data/craftdata.json и data/craftdata.js из выгрузки данных игры.

Использование (пути по умолчанию подходят для D:\\Claude\\aa-tools):
  python tools/craft/build_data.py [--cms DIR] [--locres en/String.locres] [--project aa.x5tr]
                             [--names names.tsv] [--x5tr x5tr.exe] [--build 26495283]

Читает только локальные файлы: CMS-таблицы (Design/CMS/*.csv), английский String.locres и
русский перевод проекта (.x5tr, JSON). Ничего не скачивает, сети не касается, AES-ключа не знает.

Как получить свежие CMS-таблицы после патча — см. tools/extract_cms.ps1 (ключ берётся из
%APPDATA%\\X5Viewer\\settings.json во время работы и никуда не записывается).

ВАЖНО: рецептные таблицы (ItemCraft, ItemCraftPack, CookRecipe, MakeTradeGood) в клиенте
забиты нулями (данные лежат на сервере). Скрипт сообщает об этом и, если в будущей сборке
они окажутся заполнены, сам подхватит их (см. ensure_recipes) — ничего перекраивать не надо.
"""
import argparse, csv, io, json, os, re, subprocess, sys, tempfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # корень сайта (Site)
AA = r"D:\Claude\aa-tools"
CASES = {"nom": 3, "gen": 4, "dat": 5, "acc": 6, "ins": 7, "prep": 8}


def read_cms(cms, name):
    """CSV-таблица; None, если файл отсутствует или забит нулями (серверные данные)."""
    p = os.path.join(cms, name + ".csv")
    if not os.path.exists(p):
        return None
    raw = open(p, "rb").read()
    if not raw.strip(b"\x00 \r\n"):
        return None
    text = raw.replace(b"\x00", b"").decode("utf-8-sig", "replace")
    return list(csv.DictReader(io.StringIO(text, newline="")))


def load_names(path):
    tbl = {}
    if not os.path.exists(path):
        return tbl
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        p = line.rstrip("\n").split("\t")
        if len(p) >= 9:
            tbl[p[0]] = p
    return tbl


def resolve(text, names):
    def sub(m):
        row = names.get(m.group(1))
        if not row:
            return m.group(1).replace("_", " ")
        return row[CASES.get(m.group(2) or "nom", 3)]
    return re.sub(r"\{\{n:([^|}]+)(?:\|(\w+))?\}\}", sub, text)


def num(s, default=0.0):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cms", default=AA + r"\game-data-26495283\X5\Content\Design\CMS")
    ap.add_argument("--locres", default=AA + r"\game-data-26495283\X5\Content\Localization\String\en\String.locres")
    ap.add_argument("--project", default=AA + r"\ru-translation\project\aa.x5tr")
    ap.add_argument("--names", default=AA + r"\ru-translation\glossary\names.tsv")
    ap.add_argument("--x5tr", default=AA + r"\X5Tr.Cli\bin\Release\net10.0\x5tr.exe")
    ap.add_argument("--build", default="26495283")
    a = ap.parse_args()

    with tempfile.TemporaryDirectory() as td:
        en_csv = os.path.join(td, "en.csv")
        subprocess.run([a.x5tr, "export-csv", a.locres, en_csv], check=True, stdout=subprocess.DEVNULL)
        en = {r[1]: r[3] for r in list(csv.reader(open(en_csv, encoding="utf-8-sig", newline="")))[1:]}
    ru_raw = {}
    if os.path.exists(a.project):
        proj = json.load(open(a.project, encoding="utf-8"))
        ru_raw = {k: t for _, k, t in proj["Tr"]}
    names = load_names(a.names)

    def tx(key):
        e, r = en.get(key), ru_raw.get(key)
        e = resolve(e, names) if e else None
        r = resolve(r, names) if r else None
        return e, (r or e)

    report = {}
    for t in ("CookRecipe", "ItemCraft", "ItemCraftPack", "MakeTradeGood", "LootPack", "Gathering",
              "GatheringDesign", "Shop", "LootWorld", "ItemPolish", "ItemSocket"):
        rows = read_cms(a.cms, t)
        report[t] = None if rows is None else len(rows)

    # ---------- предметы ----------
    items_raw = read_cms(a.cms, "Item") or []
    src_tbl = {r["id"]: r["sourceType"] for r in (read_cms(a.cms, "ItemSource") or [])}
    items, idx = [], {}
    for r in items_raw:
        iid = int(r["id"])
        ne, nr = tx("TXT_ITEM_%010d_NAME" % iid)
        de, dr = tx("TXT_ITEM_%010d_DESC" % iid)
        o = {"id": iid, "en": ne or "", "ru": nr or "", "cat": r["category"], "sub": r["subCategory"],
             "grade": "Rare" if iid in (70108008, 70108009, 70108010, 70108011, 70108012) and r["grade"] == "Normal" else r["grade"], "lvl": int(num(r["level"], 1)),
             "price": num(r["priceValue"]), "pt": r["priceType"]}
        if r["FK_iconId"]:
            o["ic"] = int(r["FK_iconId"])
        if r["FK_itemCraftId"]:
            o["craft"] = int(r["FK_itemCraftId"])
        if r["FK_disasmPackId"]:
            o["disasm"] = int(r["FK_disasmPackId"])
        if r["Fk_itemSourceId"]:
            o["src"] = src_tbl.get(r["Fk_itemSourceId"], "?")
        if dr:
            o["dru"] = dr
        if de:
            o["den"] = de
        items.append(o)
        idx[iid] = o

    # ---------- разбор предметов (disasm) ----------
    # Item.FK_disasmPackId -> LootCondition.FK_lootPack -> (lootGroupId, rate) -> LootItem.lootGroupId
    lc = read_cms(a.cms, "LootCondition") or []
    li = read_cms(a.cms, "LootItem") or []
    groups = defaultdict(list)
    for r in li:
        groups[r["lootGroupId"]].append(r)
    packs_needed = {o["disasm"] for o in items if "disasm" in o}
    by_pack = defaultdict(list)
    for r in lc:
        if r["FK_lootPack"] and int(r["FK_lootPack"]) in packs_needed:
            by_pack[int(r["FK_lootPack"])].append(r)
    disasm = {}
    for pid, conds in by_pack.items():
        acc = defaultdict(float)
        for c in conds:
            rate = num(c["rate"], 100.0) / 100.0
            g = groups.get(c["lootGroupId"], [])
            tot = sum(num(x["dropWeight"], 1) for x in g) or 1
            for x in g:
                if not x["itemId"]:
                    continue
                avg = (num(x["minAmount"], 1) + num(x["maxAmount"], 1)) / 2
                acc[int(x["itemId"])] += rate * num(x["dropWeight"], 1) / tot * avg
        disasm[pid] = [[k, round(v, 4)] for k, v in sorted(acc.items())]

    # ---------- кулинария (названия рецептов есть, состава нет) ----------
    cook = []
    for k in sorted(en):
        m = re.fullmatch(r"TXT_COOKRECIPE_(\d+)_NAME", k)
        if m:
            e, r = tx(k)
            cook.append({"id": int(m.group(1)), "en": e, "ru": r})
    mats = [{"item": int(r["FK_ItemId"]), "cat": r["materialCategory"], "main": r["useMain"] == "True"}
            for r in (read_cms(a.cms, "ItemCookMaterial") or [])]

    skills = []
    for r in (read_cms(a.cms, "ExpertiseSkill") or []):
        skills.append({"type": r["expertiseType"], "group": r["expertiseGroupType"], "order": int(num(r["viewSequence"]))})

    out = {"build": a.build, "serverOnly": {k: v for k, v in report.items() if v is None},
           "items": items, "disasm": disasm, "cook": cook, "cookMaterials": mats, "skills": skills}

    # ---------- рецепты из клиента (если когда-нибудь появятся) ----------
    out["clientRecipes"] = ensure_recipes(a.cms)

    os.makedirs(os.path.join(ROOT, "data", "craft"), exist_ok=True)
    js = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    open(os.path.join(ROOT, "data", "craft", "craftdata.json"), "w", encoding="utf-8").write(js)
    open(os.path.join(ROOT, "data", "craft", "craftdata.js"), "w", encoding="utf-8").write("window.CRAFTDATA=" + js + ";\n")
    print("предметов %d, наборов разбора %d, рецептов кулинарии (только названия) %d, клиентских рецептов %d"
          % (len(items), len(disasm), len(cook), len(out["clientRecipes"])))
    print("серверные (обнулены в клиенте):", ", ".join(sorted(out["serverOnly"])) or "нет")


def ensure_recipes(cms):
    """Если ItemCraft в клиенте заполнен — прочитать универсально и вернуть строки как есть.
    Сейчас таблица пустая, поэтому возвращается []. Формат колонок неизвестен, поэтому
    сохраняются сырые строки (data.clientRecipes) и калькулятор их пока не использует."""
    rows = read_cms(cms, "ItemCraft")
    return rows or []


if __name__ == "__main__":
    sys.exit(main())
