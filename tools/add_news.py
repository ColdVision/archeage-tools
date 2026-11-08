# -*- coding: utf-8 -*-
r"""Добавить новость или описание патча в data/news.json (и в копию data/news.js).

Пример:
  python tools/add_news.py --type patch --date 2026-11-20 --version 1.2.3 --build 26500000 ^
      --title-ru "Обновление 1.2.3" --title-en "Update 1.2.3" ^
      --text-ru "Исправления и новый контент." --text-en "Fixes and new content." --url https://...

Без аргументов — спросит поля в консоли. Записи сортируются по дате (новые сверху). id генерируется из даты и типа.
Пробные записи (sample: true) удаляйте вручную из data/news.json или ключом --drop-samples.
"""
import argparse, json, os, re, sys, datetime

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(SITE, "data", "news.json")


def ask(label, default=""):
    v = input("%s%s: " % (label, " [%s]" % default if default else "")).strip()
    return v or default


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--type", choices=["news", "patch"])
    ap.add_argument("--date")
    ap.add_argument("--title-ru"); ap.add_argument("--title-en")
    ap.add_argument("--text-ru"); ap.add_argument("--text-en")
    ap.add_argument("--version", default=None); ap.add_argument("--build", default=None); ap.add_argument("--url", default=None)
    ap.add_argument("--sync", action="store_true", help="только пересоздать news.js из news.json (после ручной правки)")
    ap.add_argument("--drop-samples", action="store_true", help="удалить пробные записи")
    a = ap.parse_args()
    doc = json.load(open(P, encoding="utf-8"))
    items = doc["items"]
    if a.drop_samples:
        items[:] = [i for i in items if not i.get("sample")]
    if a.type or a.title_ru or not (a.drop_samples or a.sync):
        interactive = not (a.type and a.title_ru)
        t = a.type or ask("Тип (news/patch)", "news")
        date = a.date or (ask("Дата YYYY-MM-DD", datetime.date.today().isoformat()) if interactive else datetime.date.today().isoformat())
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            sys.exit("Дата должна быть в формате YYYY-MM-DD")
        tr = a.title_ru or ask("Заголовок (рус.)"); te = a.title_en or (ask("Заголовок (англ.)", tr) if interactive else tr)
        xr = a.text_ru or (ask("Текст (рус.)") if interactive else ""); xe = a.text_en or (ask("Текст (англ.)", xr) if interactive else xr)
        ver = a.version if a.version is not None else (ask("Версия игры (необязательно)") if interactive else "")
        bld = a.build if a.build is not None else (ask("Сборка/buildid (необязательно)") if interactive else "")
        url = a.url if a.url is not None else (ask("Ссылка (необязательно)") if interactive else "")
        if not tr:
            sys.exit("Нужен заголовок")
        base = "%s-%s" % (t, date); n, nid = 1, base
        while any(i["id"] == nid for i in items):
            n += 1; nid = "%s-%d" % (base, n)
        items.append({"id": nid, "date": date, "type": t, "title": {"ru": tr, "en": te}, "text": {"ru": xr, "en": xe},
                      "version": ver, "build": int(bld) if str(bld).isdigit() else bld, "url": url})
    items.sort(key=lambda i: i["date"], reverse=True)
    js = json.dumps(doc, ensure_ascii=False, indent=2)
    open(P, "w", encoding="utf-8").write(js + "\n")
    open(os.path.join(SITE, "data", "news.js"), "w", encoding="utf-8").write("window.AA_NEWS = " + js + ";\n")
    print("Записей в ленте: %d" % len(items))


if __name__ == "__main__":
    main()
