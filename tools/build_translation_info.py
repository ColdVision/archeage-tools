# -*- coding: utf-8 -*-
r"""Снимок состояния перевода для сайта: data/translation.json + data/translation.js.
Читает manifest-A/B.json и SHA256SUMS.txt из папки релиза ru-translation\releases\<версия>\github.
Запасной вариант для страниц «Главная» и «Локализация», если GitHub API недоступен.
Ничего не скачивает, AES-ключа не знает.

  python tools/build_translation_info.py [--release DIR]   (по умолчанию — самая новая версия)
"""
import argparse, glob, json, os, re

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AA = os.path.dirname(SITE)
REPO = "ColdVision/ArcheAge-Chronicles-russian-translate"


def vkey(p):
    return tuple(int(x) for x in re.findall(r"\d+", os.path.basename(os.path.dirname(p))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", help="папка .../releases/<версия>/github")
    a = ap.parse_args()
    if a.release:
        gh = a.release
    else:
        cands = [p for p in glob.glob(os.path.join(AA, "ru-translation", "releases", "*", "github")) if re.search(r"\d+\.\d+\.\d+", p)]
        gh = max(cands, key=vkey)
    man = json.load(open(os.path.join(gh, "manifest-A.json"), encoding="utf-8"))
    manb = json.load(open(os.path.join(gh, "manifest-B.json"), encoding="utf-8"))
    sums = {}
    for line in open(os.path.join(gh, "SHA256SUMS.txt"), encoding="utf-8"):
        m = re.match(r"([0-9a-fA-F]{64})\s+\*?(.+?)\s*$", line)
        if m:
            sums[m.group(2)] = m.group(1).lower()
    files = []
    for name in sorted(os.listdir(gh)):
        p = os.path.join(gh, name)
        if os.path.isfile(p) and name != "SHA256SUMS.txt":
            files.append({"name": name, "size": os.path.getsize(p), "sha256": sums.get(name, "")})
    files.append({"name": "SHA256SUMS.txt", "size": os.path.getsize(os.path.join(gh, "SHA256SUMS.txt")), "sha256": ""})
    ver = man["version"]
    out = {
        "_comment": "Снимок последнего релиза перевода (tools/build_translation_info.py). Живые данные страница берёт из GitHub API.",
        "repo": REPO, "version": ver, "tag": "v" + ver, "game_build": man.get("game_build"),
        "steam_app_id": man.get("steam_app_id"), "built_utc": man.get("built_utc"),
        "coverage": man["coverage"], "coverage_B": manb.get("coverage"), "files": files,
        "release_page": "https://github.com/%s/releases/tag/v%s" % (REPO, ver),
        "download_base": "https://github.com/%s/releases/download/v%s/" % (REPO, ver),
    }
    js = json.dumps(out, ensure_ascii=False, indent=1)
    open(os.path.join(SITE, "data", "translation.json"), "w", encoding="utf-8").write(js + "\n")
    open(os.path.join(SITE, "data", "translation.js"), "w", encoding="utf-8").write("window.AA_TRANSLATION = " + js + ";\n")
    print("версия %s, сборка игры %s, переведено %s из %s" % (ver, out["game_build"], out["coverage"]["translated"], out["coverage"]["total"]))


if __name__ == "__main__":
    main()
