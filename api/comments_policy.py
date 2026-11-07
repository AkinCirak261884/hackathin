"""Should peer comments be on for a round? Decided from OCHA 3W operational presence (HDX).

Team decision (7 Nov): if few organisations work in the area a risk affects, every comment is
easier to trace to a person, and one organisation can steer the discussion. So comments are
off there, and on where many actors are present.

Rule: count distinct organisations in the risk's affected area (api/data/presence_3w.json).
  n_orgs >= COMMENTS_MIN_ORGS (default 30)  -> comments on
  n_orgs <  COMMENTS_MIN_ORGS               -> comments off
  no 3W data for the country                -> comments off (fail closed)

Affected area = province/state/oblast names found in the risk title (only areas of the risk's own
country), regional phrases like "eastern Chad" or "Darfur region", otherwise the whole country.
"""
import json
import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

PRESENCE = Path(__file__).parent / "data" / "presence_3w.json"
DEFAULT_MIN_ORGS = 30

# Regional phrases in risk titles -> the areas they cover (used only if no named area matched).
REGIONS = {
    "TCD": {"eastern chad": ["Ouaddai", "Sila", "Wadi Fira", "Ennedi Est"],
            "east of chad": ["Ouaddai", "Sila", "Wadi Fira", "Ennedi Est"]},
    "SDN": {"darfur": ["North Darfur", "South Darfur", "East Darfur", "West Darfur", "Central Darfur"],
            "kordofan": ["North Kordofan", "South Kordofan", "West Kordofan"]},
    "UKR": {},
}
# Other spellings of an area as it appears in risk titles.
ALIASES = {
    "SDN": {"Northern": ["northern state"], "Aj Jazirah": ["gezira", "al jazirah", "jazirah"],
            "Abyei PCA": ["abyei"]},
    "UKR": {"Donetska": ["donetsk"], "Kharkivska": ["kharkiv"], "Khersonska": ["kherson"],
            "Zaporizka": ["zaporizhzhia", "zaporizhia"], "Sumska": ["sumy"], "Dnipropetrovska": ["dnipro"],
            "Odeska": ["odesa", "odessa"], "Mykolaivska": ["mykolaiv"], "Chernihivska": ["chernihiv"],
            "Luhanska": ["luhansk"]},
}
# Area names that are also ordinary words: only match them through ALIASES.
ALIAS_ONLY = {"SDN": {"Northern"}}


def min_orgs() -> int:
    try:
        return int(os.environ.get("COMMENTS_MIN_ORGS", DEFAULT_MIN_ORGS))
    except ValueError:
        return DEFAULT_MIN_ORGS


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " " + re.sub(r"[^a-z0-9]+", " ", s).strip() + " "


@lru_cache(maxsize=1)
def presence() -> dict:
    if not PRESENCE.exists():
        return {"countries": {}}
    return json.loads(PRESENCE.read_text(encoding="utf-8"))


def iso_for(country: str) -> str | None:
    c = _norm(country)
    for iso, data in presence()["countries"].items():
        if _norm(data["country"]) == c or _norm(iso) == c:
            return iso
    return None


def affected_areas(iso: str, title: str) -> tuple[list[str], str]:
    """(areas, how): named areas in the title, else a regional phrase, else the whole country."""
    areas = presence()["countries"][iso]["areas"]
    t = _norm(title)
    found = []
    for a in areas:
        names = list(ALIASES.get(iso, {}).get(a, []))
        if a not in ALIAS_ONLY.get(iso, set()):
            names.append(a)
        if any(_norm(n) in t for n in names):
            found.append(a)
    if found:
        return sorted(found), "named in risk title"
    for phrase, region in REGIONS.get(iso, {}).items():
        if _norm(phrase) in t:
            return [a for a in region if a in areas], f'region "{phrase}" in risk title'
    return [], "whole country"


def decide(risk: dict) -> dict:
    """risk: {risk_id, title, country}. Returns the `comments` block served with a round."""
    threshold = min_orgs()
    iso = iso_for(risk.get("country", ""))
    if iso is None:
        return {"enabled": False, "n_orgs": None, "min_orgs": threshold, "areas": [], "area_basis": None,
                "reason": f"no OCHA 3W presence data for {risk.get('country') or 'this country'}: "
                          "comments off by default", "source": None}
    c = presence()["countries"][iso]
    areas, how = affected_areas(iso, risk.get("title", ""))
    if not areas:
        n = c["n_orgs_country"]
    else:
        rows = [c["areas"][a] for a in areas]
        if all("orgs" in r for r in rows):
            n = len(set().union(*(r["orgs"] for r in rows)))   # an org in two provinces counts once
        else:
            n = max(r["n_orgs"] for r in rows)   # no org lists (UKR): lower bound, never overcounts
    where = ", ".join(areas) if areas else c["country"]
    enabled = n >= threshold
    reason = (f"{n} organisations operate in {where} (≥ {threshold}): comments on"
              if enabled else
              f"only {n} organisations operate in {where} (< {threshold}): comments off, because with "
              "few actors a comment is easier to trace back and easier to steer")
    return {"enabled": enabled, "n_orgs": n, "min_orgs": threshold, "areas": areas, "area_basis": how,
            "reason": reason,
            "source": {"title": f"OCHA 3W/5W {c['country']} via HDX", "url": c["dataset"],
                       "as_of": c["as_of"], "licence": c["licence"]}}
