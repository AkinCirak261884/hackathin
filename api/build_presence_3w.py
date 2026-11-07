"""Build api/data/presence_3w.json from OCHA 3W/5W "operational presence" files on HDX.

Offline, run by hand when OCHA publishes a new 3W. The API itself only reads the JSON.

    uv run --with openpyxl python -m api.build_presence_3w <dir with tcd.xlsx sdn.xlsx ukr.xlsx>

Sources (CC BY, OCHA via HDX, data.humdata.org):
  TCD  chad-operational-presence          TCD_3W_Sep2026.xlsx, sheet "Opérationnelle"
  SDN  sudan-operational-presence         2026 consolidated 3W, January to July
  UKR  ukraine-who-does-what-where-3w     UKR 5W 2026 January to September (counts per oblast)

Output per area: number of distinct organisations, and their acronyms where the file lists them
(organisations only: no people, no contact details).
"""
import json
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

OUT = Path(__file__).parent / "data" / "presence_3w.json"

SOURCES = {
    "TCD": {"file": "tcd.xlsx", "dataset": "https://data.humdata.org/dataset/chad-operational-presence",
            "resource": "TCD_3W_Sep2026.xlsx", "as_of": "2026-09-07", "level": "province"},
    "SDN": {"file": "sdn.xlsx", "dataset": "https://data.humdata.org/dataset/sudan-operational-presence",
            "resource": "2026-consolidated-3w-data-january-to-july.xlsx", "as_of": "2026-07-31", "level": "state"},
    "UKR": {"file": "ukr.xlsx", "dataset": "https://data.humdata.org/dataset/ukraine-who-does-what-where-3w",
            "resource": "UKR - 5W - 2026 - January - September - 2026-09-30.xlsx", "as_of": "2026-09-30",
            "level": "oblast"},
}
COUNTRY = {"TCD": "Chad", "SDN": "Sudan", "UKR": "Ukraine"}


def clean(s) -> str:
    """Strip accents/mojibake differences so 'Guéra' and 'Guera' are one area."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.replace("�", "").split())


def _sets_to_json(areas: dict[str, set]) -> dict:
    return {a: {"n_orgs": len(o), "orgs": sorted(o)} for a, o in sorted(areas.items())}


def build_tcd(path: Path) -> dict:
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = next(w for w in wb.worksheets if w.title.startswith("Op"))   # "Opérationnelle"
    areas: dict[str, set] = defaultdict(set)
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[1] and r[4]:   # Province, Acronyme
            areas[clean(r[1])].add(clean(r[4]).upper())
    return {"areas": _sets_to_json(areas), "n_orgs_country": len(set().union(*areas.values()))}


def build_sdn(path: Path) -> dict:
    import openpyxl
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0]
    areas: dict[str, set] = defaultdict(set)
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[1] and r[4]:   # State, Org name
            areas[clean(r[1])].add(clean(r[4]).upper())
    return {"areas": _sets_to_json(areas), "n_orgs_country": len(set().union(*areas.values()))}


def build_ukr(path: Path) -> dict:
    import openpyxl
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)["# Project Lead & Impl Partners"]
    areas, total = {}, None
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r[0]:
            continue
        n = int(r[-1])   # "Total PL and IP": OCHA's own distinct count per oblast
        if clean(r[0]).lower() == "total":
            total = n
        else:
            areas[clean(r[0])] = {"n_orgs": n}   # no per-org list: some partners are "Anonymized"
    return {"areas": dict(sorted(areas.items())), "n_orgs_country": total}


def main(src_dir: str) -> None:
    d = Path(src_dir)
    out = {"_about": "Organisations with operational presence per area, from OCHA 3W/5W on HDX (CC BY). "
                     "Used by api/comments_policy.py. Rebuild with api/build_presence_3w.py.",
           "built_at": date.today().isoformat(), "countries": {}}
    for iso, fn in (("TCD", build_tcd), ("SDN", build_sdn), ("UKR", build_ukr)):
        meta = {k: v for k, v in SOURCES[iso].items() if k != "file"}
        out["countries"][iso] = {"country": COUNTRY[iso], **meta, "licence": "CC BY 4.0 (OCHA, via HDX)",
                                 **fn(d / SOURCES[iso]["file"])}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for iso, c in out["countries"].items():
        print(iso, c["n_orgs_country"], "orgs,", len(c["areas"]), "areas")


if __name__ == "__main__":
    main(sys.argv[1])
