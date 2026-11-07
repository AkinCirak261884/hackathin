"""Mock for GET /acaps/risks?panel=TCD (Lane B proxy to the ACAPS API, see BOARD.md).
Builds web/src/mock/acaps_risks_TCD.json from the Risk Radar CSV: active risks in the panel country and neighbours.
Run from repo root: python3 web/scripts/snapshot_acaps_risks.py
"""
import csv, json, os

PANEL = {"TCD": ["TCD", "SDN"]}  # panel -> ISO codes whose active risks the panel sees
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "risk-radar-export.csv"), encoding="utf-8-sig")))
for panel, isos in PANEL.items():
    out = []
    for r in rows:
        if r["Status"] != "Active" or not any(i in r["ISO"] for i in isos):
            continue
        out.append({
            "risk_id": r["Risk ID"], "title": r["Risk Title"].strip(), "country": r["Country"], "iso": r["ISO"],
            "risk_type": r["Risk Type"] or None, "probability": r["Probability"] or None,
            "impact": int(r["Impact"]) if r["Impact"].isdigit() else None,
            "risk_level": r["Risk Level"] or None, "trend": r["Risk trend"] or None, "status": r["Status"],
        })
    out.sort(key=lambda x: ({"High": 0, "Medium": 1, "Low": 2}.get(x["risk_level"], 3), -(x["impact"] or 0)))
    path = os.path.join(ROOT, "web", "src", "mock", f"acaps_risks_{panel}.json")
    json.dump({"source": "snapshot", "panel": panel, "risks": out}, open(path, "w"), ensure_ascii=False, indent=1)
    print(path, len(out))
