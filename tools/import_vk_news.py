# -*- coding: utf-8 -*-
r"""Импорт постов группы ВКонтакте в data/news.json (и data/news.js) через официальный API ВК (wall.get).

Токен НЕ хранится в сайте и не записывается в файлы проекта. Передайте его одним из способов:
  1) переменная окружения VK_TOKEN                     (PowerShell:  $env:VK_TOKEN = "..." )
  2) файл %APPDATA%\aa-site\vk_token.txt  (одна строка, лежит вне папки сайта)
Подойдёт сервисный ключ доступа приложения (vk.com/apps?act=manage -> своё Standalone-приложение -> «Сервисный ключ доступа»):
для чтения стены открытой группы пользовательский токен не нужен.

Примеры:
  python tools\import_vk_news.py                       # последние 20 постов группы archeagechronicles
  python tools\import_vk_news.py --count 50 --dry-run  # только показать, ничего не писать
  python tools\import_vk_news.py --patch-words "патч,обновлени,patch"   # посты с такими словами пометить как patch
Записи получают id "vk-<id поста>", поле source="vk" и ссылку на пост; повторный запуск обновляет их, ручные записи не трогает.
Запрос идёт на https://api.vk.ru (метод wall.get, версия API 5.199); сторонних сервисов нет.
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request, datetime

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS = os.path.join(SITE, "data", "news.json")
API = "https://api.vk.ru/method/wall.get"
VER = "5.199"


def token():
    t = os.environ.get("VK_TOKEN", "").strip()
    if not t:
        p = os.path.join(os.environ.get("APPDATA", ""), "aa-site", "vk_token.txt")
        if os.path.isfile(p):
            t = open(p, encoding="utf-8").read().strip()
    return t


def fetch(domain, count, tok):
    q = urllib.parse.urlencode({"domain": domain, "count": count, "v": VER, "access_token": tok})
    req = urllib.request.Request(API + "?" + q, headers={"User-Agent": "aa-site-news-import/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.loads(r.read().decode("utf-8"))
    if "error" in j:
        sys.exit("Ошибка VK API: %s (код %s)" % (j["error"].get("error_msg"), j["error"].get("error_code")))
    return j["response"]["items"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--domain", default="archeagechronicles")
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--patch-words", default="патч,обновлени,patch,update", help="через запятую; пост со словом -> type=patch")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    tok = token()
    if not tok:
        sys.exit("Нет токена: задайте VK_TOKEN или файл %APPDATA%/aa-site/vk_token.txt (см. описание в начале скрипта).")
    words = [w.strip().lower() for w in a.patch_words.split(",") if w.strip()]
    posts = fetch(a.domain, a.count, tok)
    doc = json.load(open(NEWS, encoding="utf-8"))
    items = doc["items"]
    by_id = {i["id"]: i for i in items}
    added = 0
    for p in posts:
        if p.get("marked_as_ads"):
            continue
        txt = (p.get("text") or "").strip()
        if not txt and p.get("copy_history"):
            txt = (p["copy_history"][0].get("text") or "").strip()
        if not txt:
            txt = "Публикация сообщества ВКонтакте"
        lines = [l for l in txt.split("\n") if l.strip()]
        title = re.sub(r"\s+", " ", lines[0]).strip()
        body = "\n\n".join(lines[1:]) if len(lines) > 1 else ""
        if len(title) > 90:
            title, body = title[:87].rstrip() + "…", txt
        if len(body) > 1500:
            body = body[:1497].rstrip() + "…"
        low = txt.lower()
        rec = {
            "id": "vk-%s" % p["id"],
            "date": datetime.datetime.fromtimestamp(p["date"], datetime.timezone.utc).strftime("%Y-%m-%d"),
            "type": "patch" if any(w in low for w in words) else "news",
            "title": {"ru": title, "en": "VK community post" if title == "Публикация сообщества ВКонтакте" else title}, "text": {"ru": body, "en": body},
            "version": "", "build": "",
            "url": "https://vk.ru/wall%s_%s" % (p["owner_id"], p["id"]), "source": "vk",
        }
        if rec["id"] not in by_id:
            added += 1
        if a.dry_run:
            print(rec["date"], rec["type"], title[:70])
            continue
        if rec["id"] in by_id:
            items[items.index(by_id[rec["id"]])] = rec
        else:
            items.append(rec)
    if a.dry_run:
        print("Найдено постов: %d, новых: %d (ничего не записано)" % (len(posts), added)); return
    items.sort(key=lambda i: i["date"], reverse=True)
    js = json.dumps(doc, ensure_ascii=False, indent=2)
    open(NEWS, "w", encoding="utf-8").write(js + "\n")
    open(os.path.join(SITE, "data", "news.js"), "w", encoding="utf-8").write("window.AA_NEWS = " + js + ";\n")
    print("Постов получено: %d, новых: %d, всего записей: %d" % (len(posts), added, len(items)))


if __name__ == "__main__":
    main()
