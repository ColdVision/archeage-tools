#!/usr/bin/env python3
"""Сборка data/trade/tradedata.json и data/trade/tradedata.js из выгрузки данных игры.

Использование (пути по умолчанию подходят для D:\\Claude\\aa-tools):
  python tools/trade/build_data.py [--cms DIR] [--locres en/String.locres] [--project aa.x5tr]
                             [--names names.tsv] [--x5tr x5tr.exe] [--build 26495283]

Берёт только локальные файлы: CMS-таблицы (Design/CMS/*.csv), английский String.locres,
русский перевод проекта (.x5tr, JSON) и таблицу склонений имён (names.tsv).
Ничего не скачивает и не обращается к сети.
"""
import argparse, csv, io, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # корень сайта (Site)
AA = r"D:\Claude\aa-tools"
CASES = {"nom": 3, "gen": 4, "dat": 5, "acc": 6, "ins": 7, "prep": 8}
# Трофеи и наборы камней из обновления от 25 ноября 2026.
NEW_GOOD_IDS = range(1169, 1187)


def read_cms(cms, name):
    """CMS-таблицы читаются как CSV; пустые (забитые нулями) возвращают None."""
    raw = open(os.path.join(cms, name + ".csv"), "rb").read()
    if not raw.strip(b"\x00 \r\n"):
        return None
    text = raw.replace(b"\x00", b"").decode("utf-8", "replace")
    return list(csv.DictReader(io.StringIO(text)))


def load_names(path):
    tbl = {}
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


def client_economy(goods, posts, trade_rows, recipes, purchases):
    trade_by_id = {int(r["id"]): r for r in trade_rows}
    recipe_by_id = {int(r["FK_TradeGood"]): r for r in recipes}
    post_ids = {p["id"] for p in posts}
    payouts = {gid: {} for gid in goods}
    for r in purchases:
        gid, dest = int(r["FK_tradeGoodId"]), int(r["tradingPostId"])
        good = goods.get(gid)
        if not good or dest not in post_ids or good["origin"] != int(r["startTradingPostId"]):
            continue
        if r["FK_Item"]:
            reward = [int(r["FK_Item"]), int(r["rewardItemAmount"])]
        elif r["moneyType"] == "Gold":
            reward = int(r["rewardBasisPoints"]) / 100
            if reward.is_integer():
                reward = int(reward)
        else:
            raise ValueError(f"Неизвестная награда за товар {gid} в посте {dest}")
        payouts[gid][dest] = reward

    economy = {}
    for gid in goods:
        trade, recipe = trade_by_id[gid], recipe_by_id.get(gid)
        packing, materials = None, []
        if recipe:
            if recipe["costType"] != "Gold":
                raise ValueError(f"Неизвестная валюта упаковки товара {gid}")
            packing = int(recipe["costValue"])
            for slot in range(1, 6):
                iid = recipe[f"materialId{slot:02}"]
                if iid:
                    materials.append([int(iid), int(recipe[f"materialCount{slot:02}"])])
        economy[str(gid)] = (
            int(trade["basicValue"]), int(trade["validPeriod"]), packing,
            int(trade["weight"]), payouts[gid], materials,
        )
    return economy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cms", default=AA + r"\game-data-26495283\X5\Content\Design\CMS")
    ap.add_argument("--locres", default=AA + r"\game-data-26495283\X5\Content\Localization\String\en\String.locres")
    ap.add_argument("--project", default=AA + r"\ru-translation\project\aa.x5tr")
    ap.add_argument("--names", default=AA + r"\ru-translation\glossary\names.tsv")
    ap.add_argument("--x5tr", default=AA + r"\X5Tr.Cli\bin\Release\net10.0\x5tr.exe")
    ap.add_argument("--build", default="26495283")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    with tempfile.TemporaryDirectory() as td:
        en_csv = os.path.join(td, "en.csv")
        subprocess.run([a.x5tr, "export-csv", a.locres, en_csv], check=True, stdout=subprocess.DEVNULL)
        en = {r[1]: r[3] for r in list(csv.reader(open(en_csv, encoding="utf-8-sig")))[1:]}
    proj = json.load(open(a.project, encoding="utf-8"))
    ru_raw = {k: t for _, k, t in proj["Tr"]}
    names = load_names(a.names)
    manual_dir = os.path.join(ROOT, "data", "trade", "manual")
    with open(os.path.join(manual_dir, "pack-labels-ru.json"), encoding="utf-8") as f:
        ru_fallback = json.load(f)

    def tx(key):
        e = en.get(key)
        r = ru_raw.get(key) or ru_fallback.get(key)
        if not r and key.endswith("_VOUCHERNAME"):
            label = ru_fallback.get(key.removesuffix("_VOUCHERNAME") + "_NAME")
            if label and e:
                r = "[Свидетельство] " + label
        return {"en": resolve(e, names) if e else None,
                "ru": resolve(r, names) if r else (resolve(e, names) if e else None)}

    posts = read_cms(a.cms, "TradingPost")
    pg = read_cms(a.cms, "TradingPostGoods")
    qual = read_cms(a.cms, "TradeGoodQuality")
    pat = read_cms(a.cms, "TradePatternDesc")
    comp = {c["id"]: c for c in read_cms(a.cms, "Company")}
    economy_names = ("TradeGood", "MakeTradeGood", "TradingPostPurchase")
    economy_tables = [read_cms(a.cms, t) for t in economy_names]
    empty = [t for t, rows in zip(economy_names, economy_tables) if rows is None]
    empty.extend(t for t in ("TradeBonusReward", "Zone", "Shop", "Portal", "MapMarker", "OriginMap")
                 if read_cms(a.cms, t) is None)

    goods_by_post = {}
    for r in pg:
        goods_by_post.setdefault(r["FK_tradingPostId"], []).append((int(r["uiOrder"]), r["FK_tradeGoodId"]))

    out_posts, goods = [], {}
    for p in posts:
        pid = p["id"]
        gl = [g for _, g in sorted(goods_by_post.get(pid, []))]
        if not gl:
            continue  # посты 4000/4100/7000 без товаров и без названия — служебные
        out_posts.append({
            "id": int(pid), "group": int(p["group"]), "company": p["company"],
            "name": tx("TXT_TRADINGPOST_%010d_NAME" % int(pid)),
            "goods": [int(g) for g in gl]})
        for g in gl:
            gid = int(g)
            goods[gid] = {"id": gid, "origin": int(pid),
                          "name": tx("TXT_TRADEGOOD_%010d_NAME" % gid),
                          "voucher": tx("TXT_TRADEGOOD_%010d_VOUCHERNAME" % gid)}

            if gid in NEW_GOOD_IDS:
                goods[gid]["new"] = True

    if all(rows is not None for rows in economy_tables):
        src = client_economy(goods, out_posts, *economy_tables)
        economy_source = "client"
    else:
        with open(os.path.join(manual_dir, "trade-goods.json"), encoding="utf-8") as f:
            src = json.load(f)["goods"]
        economy_source = "questlog"

    def item(iid, count):
        return {"id": iid, "name": tx("TXT_ITEM_%010d_NAME" % iid), "count": count}

    for gid, g in goods.items():
        if str(gid) not in src:
            continue
        base, valid, pack, weight, pay, mats = src[str(gid)]
        g["econ"] = {"base": base, "freshMin": valid, "pack": pack, "weight": weight,
                     "mats": [item(*m) for m in mats],
                     "pay": {pid: ({"item": item(*v)} if isinstance(v, list) else {"rate": v})
                             for pid, v in pay.items()}}
    print("экономика:", economy_source, sum("econ" in g for g in goods.values()), "товаров")

    # группы качества: состояние по времени (мс от начала доставки) и коэффициент (б.п.)
    order = {"Better": 0, "Good": 1, "Normal": 2, "Bad": 3}
    qg = {}
    for q in qual:
        qg.setdefault(int(q["id"]), []).append({
            "state": q["qualityType"],
            "afterMs": int(q["overTime"]) if q["overTime"] else None,
            "bp": int(q["qualityFactorBasisPoints"])})
    for v in qg.values():
        v.sort(key=lambda s: order.get(s["state"], 9))

    # шаблоны спроса: 1xxx..5xxx — сильный рост / рост / стабильно / падение / сильное падение (по иконкам и описанию)
    patterns = []
    for p in pat:
        pid = int(p["id"])
        t = tx("TXT_TRADEPATTERNDESC_%010d_DESC" % pid)
        if t["en"] and re.search(r"[\uac00-\ud7a3]", t["en"]):
            t = {"en": None, "ru": None}  # служебные корейские заглушки
        patterns.append({"id": pid, "class": pid // 1000, "icon": int(p["icon"]), "desc": t})

    data = {
        "build": a.build,
        "economySource": economy_source,
        "posts": out_posts,
        "goods": sorted(goods.values(), key=lambda g: g["id"]),
        "quality": {str(k): v for k, v in sorted(qg.items())},
        "patterns": patterns,
        "emptyTables": empty,
        "companyZones": {k: v["zoneKey"] for k, v in comp.items()},
    }
    os.makedirs(os.path.join(ROOT, "data", "trade"), exist_ok=True)
    js = json.dumps(data, ensure_ascii=False, indent=1)
    open(os.path.join(ROOT, "data", "trade", "tradedata.json"), "w", encoding="utf-8").write(js)
    open(os.path.join(ROOT, "data", "trade", "tradedata.js"), "w", encoding="utf-8").write("window.TR_DATA = " + js + ";\n")
    print("посты:", len(out_posts), "товары:", len(goods), "группы качества:", len(qg), "шаблоны спроса:", len(patterns))
    print("пустые таблицы (данные на сервере):", ", ".join(empty))


if __name__ == "__main__":
    main()
