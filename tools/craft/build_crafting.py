#!/usr/bin/env python3
"""Сборка data/crafting.js (вкладки и подкатегории крафта как в игре) и data/recipes.js (рецепты).

Источники (сети не касается):
  1) data/source/screens.json — вкладки, подкатегории и списки рецептов, перенесённые со скриншотов игры
     (D:\\Claude\\aa-tools\\recipes\\*.jpg) + состав первого (выбранного) рецепта в каждом списке; материалы
     опознаны по иконкам (сопоставление иконок скриншота с иконками предметов игры), названия — по Item/locres;
  2) data/source/questlog_recipes.json — состав ремесленных рецептов (Кузнечное дело, Портняжное дело, Инженерия,
     Алхимия: аксессуары и метательное оружие) со стороннего сайта questlog.gg, получен один раз с разрешения
     владельца проекта; id предметов совпали с игровыми. Подкатегории задаются диапазонами id рецептов.
  3) data/craftdata.json — каталог предметов игры (id по английскому названию).
Состав остальных рецептов клиент игры не содержит (серверные данные), на скриншотах он виден только у выбранного
рецепта — поэтому у остальных записей списка рецепта нет (r = null): калькулятор покажет только сам предмет.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # корень сайта (Site)
J = lambda *p: os.path.join(ROOT, *p)
data = json.load(open(J("data", "craft", "craftdata.json"), encoding="utf-8"))
scr = json.load(open(J("data", "craft", "manual", "screens.json"), encoding="utf-8"))
ql = json.load(open(J("data", "craft", "manual", "recipes-manual.json"), encoding="utf-8"))

PREF = {"CraftMaterial": 0, "Consumable": 1, "Equipment": 2, "Jewel": 3, "Etc": 4}
by_name = {}
for it in data["items"]:
    if it["en"]:
        cur = by_name.get(it["en"])
        if cur is None or PREF.get(it["cat"], 9) < PREF.get(cur["cat"], 9):
            by_name[it["en"]] = it
ids = {i["id"] for i in data["items"]}


def iid(name):
    if name not in by_name:
        sys.exit("нет предмета в каталоге: " + name)
    return by_name[name]["id"]


recipes, tabs = [], []

# ---------- 1. скриншоты + состав из questlog (data/source/questlog_materials.json) ----------
known = scr["known"]
mats = json.load(open(J("data", "craft", "manual", "materials-manual.json"), encoding="utf-8"))
mats_by_out = {}
for rid, (nm_, mc, sc, outc, cost, ing, outs) in sorted(mats.items()):
    mats_by_out.setdefault((outs[0][0], outc), []).append((rid, ing, cost))
used_m = set()
for t in scr["tabs"]:
    tab = {"key": t["key"], "ru": t["ru"], "subs": []}
    for s in t["subs"]:
        subs_by = {}
        def kind(name, qty):
            if qty == 1:
                if t["key"] == "food":
                    return ("meat", "Мясо") if "Meat" in name else ("dish", "Блюда и приправы")
                return ("single", s["ru"])
            if qty == 10: return ("chest", "Сундуки")
            if qty in (3, 6): return ("batch", s["ru"] + " · партии ×3/×6" if t["key"] != "food" else "Партии мяса")
            return ("pack", s["ru"] + " · паки ×15/×30" if t["key"] != "food" else "Паки мяса")
        for name, qty, locked in s["list"]:
            item = iid(name)
            rid = None
            for cid, ing, cost in mats_by_out.get((item, qty), []):
                if cid in used_m:
                    continue
                used_m.add(cid)
                rid = "q" + cid
                recipes.append({"id": rid, "craft": int(cid), "out": item, "outQty": qty,
                                "ing": [{"item": a, "qty": b} for a, b in ing], "fee": cost, "src": "questlog"})
                break
            k, kru = kind(name, qty)
            sub = subs_by.get(k)
            if sub is None:
                sub = subs_by[k] = {"key": s["key"] + "-" + k, "ru": kru, "items": []}
                tab["subs"].append(sub)
            sub["items"].append({"i": item, "q": qty, "l": locked, "r": rid})
    tabs.append(tab)

# ---------- 2. questlog: подкатегории по типу предмета (id предмета: GG CCC T SS -> класс/тип/слот) ----------
WEAPON = {  # (код класса, тип) -> название
    ("101", "1"): "Одноручные мечи", ("101", "2"): "Двуручные мечи", ("101", "5"): "Короткие мечи",
    ("102", "1"): "Арбалеты", ("102", "2"): "Луки", ("102", "3"): "Топорики",
    ("103", "1"): "Топоры", ("103", "2"): "Молоты", ("103", "3"): "Щиты",
    ("104", "1"): "Посохи", ("104", "3"): "Боевые посохи", ("104", "2"): "Сабли",
}
ARMOR = {"401": "Лёгкая", "501": "Лёгкая", "601": "Лёгкая", "701": "Лёгкая", "402": "Тяжёлая", "502": "Тяжёлая", "602": "Тяжёлая", "702": "Тяжёлая",
         "403": "Тканевая", "503": "Тканевая", "603": "Тканевая", "703": "Тканевая"}
SLOT = {"1": "головные уборы", "2": "нагрудники", "3": "перчатки", "4": "обувь"}
ACC = {"1": "Ожерелья", "2": "Серьги", "3": "Браслеты", "4": "Кольца"}
# порядок подкатегорий внутри вкладки
SUBORDER = {"smithing": [], "tailoring": [], "engineering": ["Рюкзаки", "Дельтапланы"], "alchemy": []}


def qcat(cid, out):
    c = int(cid); o = str(out)
    if 60203000 <= c < 60204000:
        return ("alchemy", {"020": "Усиленные метательные", "030": "Мастерские метательные", "105": "Источники жизни"}[o[2:5]])
    if 60431000 <= c < 60435000: return ("alchemy", ACC[o[5]])
    if c in (60313701, 60413701): return ("engineering", "Дельтапланы")
    if 60400000 <= c < 60400100: return ("engineering", "Рюкзаки")
    if 60212101 <= c <= 60212148: return ("tailoring", ARMOR[o[2:5]] + " · " + SLOT[o[5]])
    if 60211000 <= c < 60212000:
        return ("smithing", WEAPON.get((o[2:5], o[5]), "Особое оружие"))
    sys.exit("нет категории для рецепта %s" % cid)

tabmap = {t["key"]: t for t in tabs}
for key, ru in [("smithing", "Кузнечное дело"), ("tailoring", "Портняжное дело"), ("engineering", "Инженерия"), ("alchemy", "Алхимия")]:
    if key not in tabmap:
        tabmap[key] = {"key": key, "ru": ru, "subs": []}; tabs.append(tabmap[key])
for cid, (o, ing, skill, lvl, cost, ctype) in sorted(ql.items()):
    tk, sru = qcat(cid, o[0][0])
    tab = tabmap[tk]
    sub = next((x for x in tab["subs"] if x["ru"] == sru), None)
    if sub is None:
        sub = {"key": "%s-%d" % (tk, len(tab["subs"])), "ru": sru, "items": []}; tab["subs"].append(sub)
    rid = "q" + cid
    recipes.append({"id": rid, "craft": int(cid), "out": o[0][0], "outQty": o[0][1], "ing": [{"item": a, "qty": b} for a, b in ing],
                    "fee": 0, "learnCost": cost, "src": "questlog"})
    # November 25: exact Fine material quantities for finished throwing weapons are pending.
    if 60203031 <= int(cid) <= 60203044 and any(item in (70308003, 70303002, 70303004) for item, qty in ing):
        recipes[-1]["pendingQuantities"] = True
    sub["items"].append({"i": o[0][0], "q": o[0][1], "l": 0, "r": rid})

# порядок вкладок как в игре
ORDER = ["smithing", "tailoring", "engineering", "alchemy", "food", "forestry", "cloth", "processing", "smelting"]
tabs.sort(key=lambda t: ORDER.index(t["key"]))
for t in tabs:
    for s in t["subs"]:
        for e in s["items"]:
            assert e["i"] in ids, e
for r in recipes:
    for g in r["ing"]:
        assert g["item"] in ids, (r["id"], g)

open(J("data", "craft", "crafting.js"), "w", encoding="utf-8").write("window.CRAFTING=" + json.dumps({"tabs": tabs}, ensure_ascii=False, separators=(",", ":")) + ";\n")
hdr = ("// Рецепты (собирается tools/build_crafting.py). Источники: скриншоты игры (src=screenshot, состав первого рецепта в списке;\n"
       "// материалы опознаны по иконкам) и сторонний сайт questlog.gg (src=questlog; получено один раз с разрешения владельца проекта).\n"
       "// Клиент игры состав рецептов не содержит (серверные данные). Формат: { id, out, outQty, ing:[{item,qty}], fee, src }\n")
open(J("data", "craft", "recipes.js"), "w", encoding="utf-8").write(hdr + "window.CRAFT_RECIPES = " + json.dumps(recipes, ensure_ascii=False, separators=(",", ":")) + ";\n")
print("вкладок %d, подкатегорий %d, записей %d, рецептов %d (скриншоты %d, questlog %d)" % (
    len(tabs), sum(len(t["subs"]) for t in tabs), sum(len(s["items"]) for t in tabs for s in t["subs"]), len(recipes),
    sum(r["src"] == "screenshot" for r in recipes), sum(r["src"] == "questlog" for r in recipes)))
