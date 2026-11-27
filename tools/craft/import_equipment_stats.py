"""Build offline equipment tooltips from QuestLog public item IDs.

Run: python tools/craft/import_equipment_stats.py [--cache-dir DIR] [--offline]
Online runs refresh all catalog equipment. --offline replays a complete saved import.
"""
import argparse
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://questlog.gg/archeage-chronicles/api/trpc/"


def request(method, payload, batch=False):
    params = {"input": json.dumps(payload, separators=(",", ":"))}
    if batch:
        params["batch"] = "1"
    url = BASE + method + "?" + urlencode(params)
    for attempt in range(4):
        try:
            with urlopen(url, timeout=40) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
            sleep(max(2 ** attempt, int(exc.headers.get("Retry-After", 0))))
        except URLError:
            if attempt == 3:
                raise
            sleep(2 ** attempt)


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def numeric(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"Invalid numeric attribute: {value!r}")
    return value


def build(cache, offline):
    ids = [i["id"] for i in read(ROOT / "data/craft/craftdata.json")["items"] if i["cat"] == "Equipment"]
    if not offline:
        cache.mkdir(parents=True, exist_ok=True)
        formats = request("statFormat.getStatFormat", {"language":"en"})["result"]["data"]
        save(cache / "formats.json", formats)
        for start in range(0, len(ids), 12):
            batch = ids[start:start + 12]
            inputs = {str(n): {"id": str(i), "language": "en"} for n, i in enumerate(batch)}
            results = request(",".join(["database.getItem"] * len(batch)), inputs, batch=True)
            for i, result in zip(batch, results, strict=True):
                row = result["result"]["data"]
                if row is not None and str(row["id"]) != str(i):
                    raise ValueError(f"ID mismatch for {i}")
                save(cache / f"{i}.json", result)
    formats = read(cache / "formats.json")
    entries, labels = {}, {}
    matched = 0
    for i in ids:
        row = read(cache / f"{i}.json")["result"]["data"]
        if row is None:
            continue
        if str(row["id"]) != str(i):
            raise ValueError(f"Wrong item in cache for {i}")
        matched += 1
        entry = {}
        attrs = row.get("itemAttributes") or {}
        for key, records in (("stats", [v for g in ("stats","armor","damage") for v in attrs.get(g, [])]),
                             ("requirements", row.get("itemStatRequirements") or [])):
            if not records:
                continue
            entry[key] = []
            for r in records:
                code = r["stat"]
                fmt = formats[code]
                icon = (fmt.get("icon") or "").split(".")[-1]
                labels[code] = {"en":fmt["name"], "format":fmt["valueFormat"], "multiplier":numeric(fmt["multiplier"])}
                if icon and (ROOT / "assets/craft/tooltip" / (icon + ".png")).is_file():
                    labels[code]["icon"] = icon
                entry[key].append([code, numeric(r["value"])])
        sockets = row.get("itemSockets")
        if sockets:
            entry["chances"] = [[numeric(x["count"]), numeric(x["chance"])] for x in sockets["countChances"]]
            if sockets.get("initialStone"):
                entry["stone"] = int(sockets["initialStone"]["id"])
            if sockets.get("openChance"):
                entry["openChance"] = numeric(sockets["openChance"])
            if sockets.get("shape"):
                entry["shape"] = sockets["shape"]
        if entry:
            entries[i] = entry
    if not matched or not entries:
        raise ValueError("Empty equipment import")
    out = ROOT / "data/craft/equipment-stats.js"
    tmp = out.with_suffix(".tmp")
    tmp.write_text("window.CRAFT_EQUIPMENT_STATS=" + json.dumps({"labels":labels,"items":entries},
                   ensure_ascii=False,separators=(",", ":")) + ";\n", encoding="utf-8")
    tmp.replace(out)
    print(f"{matched}/{len(ids)} matched; " + ", ".join(f"{k}: {sum(k in e for e in entries.values())}" for k in ("stats","chances","stone","requirements")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if args.offline and not args.cache_dir:
        parser.error("--offline requires --cache-dir")
    with TemporaryDirectory() as temp:
        build(args.cache_dir or Path(temp), args.offline)
