#!/usr/bin/env python3
"""Сборка data/tradedata.json и data/tradedata.js из выгрузки данных игры.

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

    def tx(key):
        e = en.get(key)
        r = ru_raw.get(key)
        return {"en": resolve(e, names) if e else None,
                "ru": resolve(r, names) if r else (resolve(e, names) if e else None)}

    posts = read_cms(a.cms, "TradingPost")
    pg = read_cms(a.cms, "TradingPostGoods")
    qual = read_cms(a.cms, "TradeGoodQuality")
    pat = read_cms(a.cms, "TradePatternDesc")
    comp = {c["id"]: c for c in read_cms(a.cms, "Company")}
    # таблицы, которые в клиенте пустые (данные на сервере) — фиксируем для README/страницы
    empty = [t for t in ("TradeGood", "MakeTradeGood", "TradeBonusReward", "TradingPostPurchase", "Zone", "Shop",
                         "Portal", "MapMarker", "OriginMap") if read_cms(a.cms, t) is None]

    goods_by_post = {}
    for r in pg:
        goods_by_post.setdefault(r["FK_tradingPostId"], []).append((int(r["uiOrder"]), r["FK_tradeGoodId"]))

    out_posts, goods = [], {}
    for p in posts:
        pid = p["id"]
        gl = [g for _, g in sorted(goods_by_post.get(pid, []))]
        if not gl:
            continue  # посты 4000/4100/7000 без товаров и без названия — служебные
        zone = comp.get(p["company"], {}).get("zoneKey", "")
        zm = re.match(r"Zone_(\d+)", zone)
        out_posts.append({
            "id": int(pid), "group": int(p["group"]), "company": p["company"],
            "name": tx("TXT_TRADINGPOST_%010d_NAME" % int(pid)),
            "goods": [int(g) for g in gl]})
        for g in gl:
            gid = int(g)
            goods[gid] = {"id": gid, "origin": int(pid),
                          "name": tx("TXT_TRADEGOOD_%010d_NAME" % gid),
                          "voucher": tx("TXT_TRADEGOOD_%010d_VOUCHERNAME" % gid)}

    # экономика товаров — НЕ из клиента (там таблицы пустые), а из data/trade/manual/trade-goods.json
    # (снято с questlog.gg по решению пользователя). Игровые данные остаются главным источником, этот файл только дополняет.
    src_path = os.path.join(ROOT, "data", "trade", "manual", "trade-goods.json")
    econ_n = 0
    if os.path.exists(src_path):
        src = json.load(open(src_path, encoding="utf-8"))["goods"]
        def item(iid):
            return {"id": iid, "name": tx("TXT_ITEM_%010d_NAME" % iid)}
        for gid, g in goods.items():
            r = src.get(str(gid))
            if not r:
                continue
            base, valid, pack, weight, pay, mats = r
            g["econ"] = {"base": base, "freshMin": valid, "pack": pack, "weight": weight,
                         "mats": [dict(item(m[0]), count=m[1]) for m in mats],
                         "pay": {pid: ({"rate": v} if not isinstance(v, list) else {"item": dict(item(v[0]), count=v[1])})
                                 for pid, v in pay.items()}}
            econ_n += 1
        print("экономика (внешний источник):", econ_n, "товаров")

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
