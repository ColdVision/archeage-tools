"""Export tooltip details from the game's Item.csv to the offline craft catalog."""
import argparse
import csv
import io
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("cms", type=Path, help="Directory containing Item.csv")
args = parser.parse_args()
rows = (args.cms / "Item.csv").read_bytes().replace(b"\0", b"").decode("utf-8-sig")
details = {}
for row in csv.DictReader(io.StringIO(rows)):
    entry = {k: row[k] for k in ("equipSlot", "equipMaterial") if row[k] and row[k] != "None"}
    for key in ("weight", "maxDurability", "refundValue"):
        if row[key] and float(row[key]) > 0:
            entry[key] = float(row[key])
    if "refundValue" in entry:
        entry["refundType"] = row["refundType"]
    if entry:
        details[row["id"]] = entry
out = Path(__file__).resolve().parents[2] / "data/craft/item-details.js"
out.write_text("window.CRAFT_ITEM_DETAILS=" + json.dumps(details, separators=(",", ":")) + ";\n", encoding="utf-8")
