"""Build api/data/settlements.json: towns and villages per country, from HDX "Populated Places" (OSM via HOTOSM).

Used by comments_policy.py: if a risk title names a town or village, the affected area is small, so peer
comments go off (a comment is easier to trace back, harder to cross-check, easier to steer).

Run once from the repo root (needs internet):  python3 api/build_settlements.py
Countries = the ones in api/data/presence_3w.json. Only names are kept (no coordinates).
"""
import io
import json
import sys
import unicodedata
import re
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

DATA = Path(__file__).parent / "data"
OUT = DATA / "settlements.json"
SMALL = {"town", "village"}          # small areas -> comments off; cities fall under the people-affected rule
NAME_FIELDS = ("name", "name_en", "name_fr", "name_latin")
UA = {"User-Agent": "ground-truth-hackathon (HFG8 ACAPS challenge)"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return json.load(r)


def build_country(iso: str) -> dict:
    pkg = fetch_json(f"https://data.humdata.org/api/3/action/package_show?id=hotosm_{iso.lower()}_populated_places")["result"]
    url = next(x["url"] for x in pkg["resources"] if x["format"] == "GeoJSON")
    print(f"{iso}: downloading {url}", file=sys.stderr)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    geo = json.loads(z.read(next(n for n in z.namelist() if n.endswith(".geojson"))))
    places: dict[str, list] = {}
    cities = {norm(f["properties"].get(k) or "") for f in geo["features"] if f["properties"].get("place") == "city"
              for k in NAME_FIELDS}
    for f in geo["features"]:
        p = f["properties"]
        if p.get("place") not in SMALL:
            continue
        display = p.get("name_en") or p.get("name_latin") or p.get("name") or ""
        for field in NAME_FIELDS:
            key = norm(p.get(field) or "")
            # very short names match too much ordinary text; a name that is also a city (e.g. Port Sudan) is not small
            if len(key) >= 4 and key not in places and key not in cities:
                places[key] = [p["place"], display, p.get("adm1_name")]
    return {"source": {"title": pkg["title"] + " (OSM via HDX)",
                       "url": f"https://data.humdata.org/dataset/{pkg['name']}",
                       "as_of": (pkg.get("last_modified") or "")[:10], "licence": pkg.get("license_title")},
            "places": places}


def main() -> None:
    isos = sorted(json.loads((DATA / "presence_3w.json").read_text("utf-8"))["countries"])
    out = {"built": date.today().isoformat(), "small_place_types": sorted(SMALL),
           "countries": {iso: build_country(iso) for iso in isos}}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for iso, c in out["countries"].items():
        print(f"{iso}: {len(c['places'])} town/village names", file=sys.stderr)


if __name__ == "__main__":
    main()
