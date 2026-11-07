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

Area size (decided 7 Nov by the team owner while Lane B was offline): comments are on only for a large area.
  risk title names a town or village      -> comments off  (api/data/settlements.json, HDX Populated Places / OSM)
  few people affected (ACAPS "Expected exposure" <= COMMENTS_MIN_PEOPLE, default 100,000) -> comments off
  exposure unknown                         -> this check doesn't block (the others still apply)
Order of checks: no 3W data -> town/village named -> few people -> few organisations -> on.
"""
import csv
import json
import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

PRESENCE = Path(__file__).parent / "data" / "presence_3w.json"
SETTLEMENTS = Path(__file__).parent / "data" / "settlements.json"
RISK_RADAR = Path(__file__).resolve().parent.parent / "data" / "risk-radar-export.csv"
DEFAULT_MIN_ORGS = 30
DEFAULT_MIN_PEOPLE = 100_000
# Capitalised words in risk titles that are never a town/village name here (actors, acronyms, regions, months).
NOT_PLACES = {"rsf", "saf", "acaps", "un", "ocha", "unhcr", "wfp", "darfur", "kordofan", "lake chad", "blue nile",
              "nile", "sahel", "red sea", "january", "february", "march", "april", "may", "june", "july", "august",
              "september", "october", "november", "december", "russian", "russia", "ukrainian", "sudanese", "chadian"}

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


def min_people() -> int:
    try:
        return int(os.environ.get("COMMENTS_MIN_PEOPLE", DEFAULT_MIN_PEOPLE))
    except ValueError:
        return DEFAULT_MIN_PEOPLE


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " " + re.sub(r"[^a-z0-9]+", " ", s).strip() + " "


@lru_cache(maxsize=1)
def presence() -> dict:
    if not PRESENCE.exists():
        return {"countries": {}}
    return json.loads(PRESENCE.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def settlements() -> dict:
    if not SETTLEMENTS.exists():
        return {"countries": {}}
    return json.loads(SETTLEMENTS.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _radar() -> tuple[dict, frozenset]:
    """(risk_id -> "Expected exposure" bucket, all country names in the Risk Radar)."""
    if not RISK_RADAR.exists():
        return {}, frozenset()
    with RISK_RADAR.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    exposure = {r["Risk ID"]: (r.get("Expected exposure") or "").strip() for r in rows}
    countries = frozenset(_norm(c).strip() for r in rows for c in (r.get("Country") or "").split(","))
    return exposure, countries


def people_upper(bucket: str) -> float | None:
    """Upper bound of an exposure bucket: "<20,000" -> 20000, "20,000-100,000" -> 100000, ">500,000" -> inf."""
    nums = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", bucket or "")]
    if not nums:
        return None
    return float("inf") if bucket.strip().startswith(">") else max(nums)


def small_place_in_title(iso: str, title: str) -> dict | None:
    """A town or village named in the title (proper-noun phrases only, never admin areas or countries)."""
    places = settlements()["countries"].get(iso, {}).get("places", {})
    if not places:
        return None
    words = re.findall(r"[A-Za-zÀ-ÿ'’-]+", title or "")
    caps = [i for i, w in enumerate(words) if i > 0 and w[:1].isupper() and not w.isupper()]  # skip sentence start, acronyms
    skip = {_norm(a).strip() for a in presence()["countries"].get(iso, {}).get("areas", {})}
    skip |= {_norm(n).strip() for names in ALIASES.get(iso, {}).values() for n in names}
    skip |= {_norm(p).strip() for p in REGIONS.get(iso, {})} | set(_radar()[1]) | NOT_PLACES
    for size in (3, 2, 1):                                   # longest phrase first: "Port Sudan" before "Sudan"
        for i in caps:
            phrase = words[i:i + size]
            if len(phrase) < size or not all(w[:1].isupper() for w in phrase):
                continue
            key = _norm(" ".join(phrase)).strip()
            key_noart = re.sub(r"^(al|el|ad|ar|as|ash) ", "", key)
            for k in (key, key_noart):
                if len(k) >= 4 and k not in skip and k in places:
                    kind, display, adm1 = places[k]
                    return {"name": display or " ".join(phrase), "type": kind, "admin1": adm1}
    return None


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
    sources = [{"title": f"OCHA 3W/5W {c['country']} via HDX", "url": c["dataset"], "as_of": c["as_of"], "licence": c["licence"]}]
    town = small_place_in_title(iso, risk.get("title", ""))
    st = settlements()["countries"].get(iso, {}).get("source")
    if st:
        sources.append(st)
    bucket = _radar()[0].get(risk.get("risk_id") or "", "")
    upper = people_upper(bucket)
    if not areas:
        n = c["n_orgs_country"]
    else:
        rows = [c["areas"][a] for a in areas]
        if all("orgs" in r for r in rows):
            n = len(set().union(*(r["orgs"] for r in rows)))   # an org in two provinces counts once
        else:
            n = max(r["n_orgs"] for r in rows)   # no org lists (UKR): lower bound, never overcounts
    where = ", ".join(areas) if areas else c["country"]
    people_min = min_people()
    if bucket:
        sources.append({"title": "ACAPS Risk Radar, expected exposure", "url": None, "as_of": None, "licence": "ACAPS terms of use"})
    if town:
        basis, enabled = "small_place", False
        reason = (f"the risk names a {town['type']} ({town['name']}): a small area, so comments off, because there a "
                  "comment is easier to trace back, harder to cross-check and easier to steer")
    elif upper is not None and upper <= people_min:
        basis, enabled = "few_people", False
        reason = (f"few people affected ({bucket} expected exposure, ≤ {people_min:,}): comments off, because in a small "
                  "affected group a comment is easier to trace back and harder to cross-check")
    elif n < threshold:
        basis, enabled = "few_orgs", False
        reason = (f"only {n} organisations operate in {where} (< {threshold}): comments off, because with "
                  "few actors a comment is easier to trace back and easier to steer")
    else:
        basis, enabled = "large_area", True
        reason = (f"large area ({where}" + (f", {bucket} people exposed" if bucket else "") +
                  f") and {n} organisations operate there (≥ {threshold}): comments on")
    return {"enabled": enabled, "basis": basis, "n_orgs": n, "min_orgs": threshold, "areas": areas, "area_basis": how,
            "place": town, "people": bucket or None, "min_people": people_min, "reason": reason,
            "source": sources[0], "sources": sources}
