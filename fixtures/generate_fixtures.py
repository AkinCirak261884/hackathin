"""Generate all mock JSON in fixtures/ from the real R1043 row + a synthetic Chad panel.

Run from the repo root:  python3 fixtures/generate_fixtures.py
Stdlib only (Python 3.9+). Deterministic: same output every run.
All experts, names, answers and free text are SYNTHETIC.
"""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fixtures"
CSV = ROOT / "data" / "risk-radar-export.csv"

ROUND_ID = "RD-R1043-1"
OPENED_AT = "2026-11-06T18:00:00Z"
ROUND_CLOSES_AT = "2026-11-13T18:00:00Z"
FORECAST_CLOSES_AT = "2027-05-06T23:59:59Z"  # 6 months after the round opens
PROB_MAP = {"Very Low": 0.10, "Low": 0.30, "Medium": 0.50, "High": 0.70, "Very High": 0.90}


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def write(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_rows():
    with open(CSV, encoding="utf-8") as f:
        return {r["Risk ID"]: r for r in csv.DictReader(f)}


def parse_triggers(risk_id, text):
    out = []
    for block in re.split(r"\n(?=Trigger ID:)", text.strip()):
        def grab(label, nxt):
            m = re.search(label + r":\s*\n?(.*?)\n" + nxt, block, re.S)
            return re.sub(r"\s+", " ", m.group(1)).strip(" :") if m else ""
        tid = re.search(r"Trigger ID:\s*\S+\s*-\s*(T\d+)", block).group(1)
        rate = re.search(r"Completion rate:\s*(\d+)%", block)
        objective = grab(r"Quantitative objective to meet 100%", r"Trend:")
        objective = re.sub(r"^Yes\.\s*100% completion would be reached if\s*", "", objective)
        out.append({
            "trigger_id": tid,
            "risk_id": risk_id,
            "title": grab("Title", "Description:"),
            "description": grab("Description", "Sources:"),
            "completion_rate": int(rate.group(1)) / 100 if rate else 0,
            "objective": objective,
        })
    return out


def first_sentences(text, n=2):
    parts = re.split(r"(?<=\.)\s+", text.strip())
    return " ".join(parts[:n])


def pct(values, q):
    v = sorted(values)
    k = (len(v) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return round(v[lo] + (v[hi] - v[lo]) * (k - lo), 3)


def r05(x):
    return round(round(x * 20) / 20, 2)


# ---------------------------------------------------------------- synthetic panel
EXPERTS = [
    # id, pseudonym, profile, macro_region, tier, lang, bias
    ("E01", "Kestrel", "Local NGO director", "East", "known", "fr", "well_calibrated"),
    ("E02", "Linden", "Anticipatory-action officer", "N'Djamena", "known", "en", "anchored_on_acaps"),
    ("E03", "Osprey", "Conflict analyst, active on social media", "Abroad", "pseudonymous", "en", "alarmist"),
    ("E04", "Birch", "University researcher", "Abroad", "pseudonymous", "fr", "underconfident"),
    ("E05", "Heron", "UN regional office", "Abroad", "pseudonymous", "en", "well_calibrated"),
    ("E06", "Wren", "MEAL officer", "East", "pseudonymous", "fr", "noisy"),
    ("E07", "-", "Community responder", "East", "anonymous", "fr", "alarmist"),
    ("E08", "Alder", "Donor-agency methodologist", "Abroad", "known", "en", "anchored_on_acaps"),
]
# v1 answers: (T0618, T0619, T0620), rating_prob, rating_impact, seeing, ranking, ranking_other, missing
ANSWERS = {
    "E01": ((0.65, 0.20, 0.45), "agree", "agree", {"T0618", "T0620"},
            ["R1043", "SYN-TCD-03", "SYN-TCD-01"], "Affrontements intercommunautaires autour des points d'eau (Ouaddaï)",
            "Les tensions entre réfugiés et communautés hôtes autour des points d'eau à Adré ne sont pas dans l'analyse ; elles montent depuis septembre."),
    "E02": ((0.70, 0.30, 0.35), "agree", "agree", {"T0618"},
            ["R1043", "SYN-TCD-01", "SYN-TCD-02"], None,
            "Funding cuts to refugee food rations from January would amplify every trigger."),
    "E03": ((0.90, 0.55, 0.70), "too_low", "too_low", {"T0618", "T0619", "T0620"},
            ["R1043", "R0233", "SYN-TCD-03"], None,
            "Fuel smuggling routes through Ennedi-Est are shifting north after the August strike; watch the Amdjarass airstrip."),
    "E04": ((0.55, 0.40, 0.45), "agree", "too_high", set(),
            ["SYN-TCD-01", "R1043", "SYN-TCD-03"], None,
            "Le rôle des réseaux zaghawa dans l'armée tchadienne mérite plus de poids : risque de défections."),
    "E05": ((0.60, 0.15, 0.35), "agree", "agree", {"T0618"},
            ["R1043", "SYN-TCD-03", "SYN-TCD-01"], None, None),
    "E06": ((0.45, 0.35, 0.75), "too_high", "agree", {"T0620"},
            ["SYN-TCD-01", "SYN-TCD-03", "R1043"], "Choléra / hépatite E dans les sites surpeuplés",
            "Health: hepatitis E and cholera risk in overcrowded sites around Adré is missing from the priority needs."),
    "E07": ((0.85, 0.45, 0.60), "too_low", "agree", {"T0618", "T0620"},
            ["R1043", "SYN-TCD-01", "SYN-TCD-03"], None,
            "Les gens évitent la route du marché à cause des drones ; les femmes vont plus loin pour chercher de l'eau."),
    # E08 invited but has not answered yet
}
REVISIONS = {"E03": (0.80, 0.40, 0.60), "E04": (0.60, 0.30, 0.40), "E06": (0.55, 0.25, 0.60)}

RANK_OPTIONS = [
    ("R1043", "Cross-border insecurity from the Sudan conflict (eastern Chad)",
     "Insécurité transfrontalière liée au conflit soudanais (est du Tchad)", False),
    ("R0233", "Protests and violent clashes with security forces in urban areas",
     "Manifestations et affrontements violents avec les forces de sécurité en zone urbaine", False),
    ("SYN-TCD-01", "Lean-season food insecurity worsens as refugee arrivals rise",
     "L'insécurité alimentaire de soudure s'aggrave avec l'afflux de réfugiés", True),
    ("SYN-TCD-02", "Rainy-season flooding in N'Djamena and the south",
     "Inondations de saison des pluies à N'Djamena et dans le sud", True),
    ("SYN-TCD-03", "Funding shortfalls force cuts to refugee assistance in the east",
     "Le manque de financement réduit l'assistance aux réfugiés dans l'est", True),
]

QUESTION_TEXT = {
    "T0618": ("Will cross-border attacks become sustained and recurrent, affecting multiple border localities in eastern Chad and causing significant civilian casualties, displacement or humanitarian access disruptions, before 6 May 2027?",
              "Les attaques transfrontalières deviendront-elles durables et récurrentes, touchant plusieurs localités frontalières de l'est du Tchad et causant d'importantes victimes civiles, des déplacements ou des perturbations de l'accès humanitaire, avant le 6 mai 2027 ?"),
    "T0619": ("Will attacks directly target strategic infrastructure in Chad (airports, military facilities, border posts or major transport corridors), causing significant disruption, before 6 May 2027?",
              "Des attaques viseront-elles directement des infrastructures stratégiques au Tchad (aéroports, installations militaires, postes frontières ou grands corridors de transport), causant d'importantes perturbations, avant le 6 mai 2027 ?"),
    "T0620": ("Will armed groups, militias or proxy actors operating across the Chad–Sudan border become actively involved in cross-border hostilities, causing sustained violence, retaliatory attacks or territorial insecurity in eastern Chad, before 6 May 2027?",
              "Des groupes armés, milices ou acteurs par procuration opérant de part et d'autre de la frontière Tchad–Soudan participeront-ils activement à des hostilités transfrontalières, causant une violence durable, des représailles ou une insécurité territoriale dans l'est du Tchad, avant le 6 mai 2027 ?"),
}

# Kestrel's synthetic past forecasts on REAL resolved risks (outcomes from the CSV)
TRACK_RECORD_PAST = {"R1014": 0.80, "R0094": 0.30, "R0248": 0.75, "R1028": 0.20, "R0073": 0.35}


def main():
    rows = load_rows()
    r = rows["R1043"]
    triggers = parse_triggers("R1043", r["Triggers"])
    assert [t["trigger_id"] for t in triggers] == ["T0618", "T0619", "T0620"], triggers

    risk = {
        "risk_id": "R1043", "title": r["Risk Title"], "country": r["Country"], "iso": r["ISO"],
        "probability": r["Probability"], "impact": int(r["Impact"]), "level": r["Risk Level"],
        "status": r["Status"], "trend": r["Risk trend"],
        "rationale_short": first_sentences(r["Rationale"], 2),
        "expected_exposure": r["Expected exposure"],
        "priority_needs": [s.strip() for s in r["Expected priority needs"].split(",")],
        "triggers": triggers,
    }

    questions = [{
        "question_id": "Q-R1043-RATING", "risk_id": "R1043", "trigger_id": None, "kind": "rating",
        "text": f"ACAPS rates this risk {r['Probability']} probability and impact {r['Impact']}/5. Do you agree?",
        "text_fr": f"ACAPS évalue ce risque à une probabilité {'élevée' if r['Probability'] == 'High' else r['Probability']} et un impact de {r['Impact']}/5. Êtes-vous d'accord ?",
        "closes_at": ROUND_CLOSES_AT, "acaps_baseline": PROB_MAP[r["Probability"]], "outcome": None,
    }]
    for t in triggers:
        en, fr = QUESTION_TEXT[t["trigger_id"]]
        questions.append({
            "question_id": f"Q-R1043-{t['trigger_id']}", "risk_id": "R1043", "trigger_id": t["trigger_id"],
            "kind": "forecast", "text": en, "text_fr": fr, "closes_at": FORECAST_CLOSES_AT,
            "acaps_baseline": None, "outcome": None,
        })
    questions.append({
        "question_id": "Q-TCD-TOP3", "risk_id": "R1043", "trigger_id": None, "kind": "ranking",
        "text": "What are the three biggest risks in Chad that might worsen humanitarian outcomes in the next six months?",
        "text_fr": "Quels sont les trois plus grands risques au Tchad susceptibles d'aggraver la situation humanitaire dans les six prochains mois ?",
        "closes_at": ROUND_CLOSES_AT, "acaps_baseline": None, "outcome": None,
        "options": [{"option_id": o, "label": en, "label_fr": fr, "synthetic": s} for o, en, fr, s in RANK_OPTIONS],
    })
    fq = [q for q in questions if q["kind"] == "forecast"]

    round_obj = {"round_id": ROUND_ID, "panel": "TCD", "stage": "blind", "opened_at": OPENED_AT,
                 "closes_at": ROUND_CLOSES_AT, "risk": risk, "questions": questions}
    write(f"round_{ROUND_ID}.json", round_obj)
    write("rounds_open_TCD.json", [{
        "round_id": ROUND_ID, "risk_id": "R1043", "title": risk["title"], "stage": "blind",
        "closes_at": ROUND_CLOSES_AT, "n_questions": len(questions), "est_minutes": 3, "answered": False}])

    # experts + vault
    experts, vault, token_of = [], [], {}
    for eid, pseu, prof, reg, tier, lang, bias in EXPERTS:
        experts.append({"expert_id": eid, "pseudonym": pseu, "country_panel": "TCD", "lang": lang,
                        "default_tier": tier, "macro_region": reg, "profile": prof,
                        "invite_token": "inv_" + sha("invite-" + eid)[:12], "bias": bias})
        vault.append({"expert_id": eid, "name": f"Synthetic Expert {eid[1:]}", "email": f"expert{eid[1:]}@example.org"})
        token_of[eid] = ("anon_" + sha("demo-device-secret-" + eid)) if tier == "anonymous" else eid
    write("experts.json", experts)
    write("identity_vault.json", vault)
    exp = {e["expert_id"]: e for e in experts}

    # contributions (one row per author x question x version)
    contribs, n = [], 0
    def add(eid, version, qid, **fields):
        nonlocal n
        n += 1
        row = {"id": f"C-{n:04d}", "round_id": ROUND_ID, "question_id": qid, "author_token": token_of[eid],
               "tier": exp[eid]["default_tier"], "version": version, "prob": None, "seeing": None,
               "rating_probability": None, "rating_impact": None, "ranking": None, "ranking_other": None,
               "missing_text": None, "created_at": f"2026-11-0{7 if version == 1 else 8}T{8 + n % 10:02d}:{n * 7 % 60:02d}:00Z"}
        row.update(fields)
        contribs.append(row)
        return row["id"]

    missing_ids = {}
    for eid, (probs, rp, ri, seeing, ranking, other, missing) in ANSWERS.items():
        missing_ids[eid] = add(eid, 1, "Q-R1043-RATING", rating_probability=rp, rating_impact=ri, missing_text=missing)
        for q, p in zip(fq, probs):
            add(eid, 1, q["question_id"], prob=p, seeing=q["trigger_id"] in seeing)
        add(eid, 1, "Q-TCD-TOP3", ranking=ranking, ranking_other=other)
    for eid, probs in REVISIONS.items():
        seeing = ANSWERS[eid][3]
        for q, p in zip(fq, probs):
            add(eid, 2, q["question_id"], prob=p, seeing=q["trigger_id"] in seeing)
    write(f"contributions_{ROUND_ID}.json", contribs)

    def latest(eid, qi):
        return (REVISIONS.get(eid) or ANSWERS[eid][0])[qi]

    def stats(vals):
        return {"n": len(vals), "median": pct(vals, 0.5), "p25": pct(vals, 0.25), "p75": pct(vals, 0.75),
                "values": sorted(r05(v) for v in vals)}

    def rating_counts(idx):
        c = {"too_low": 0, "agree": 0, "too_high": 0}
        for a in ANSWERS.values():
            c[a[idx]] += 1
        return c

    def ranking_points():
        pts = {o[0]: [0, 0] for o in RANK_OPTIONS}
        for a in ANSWERS.values():
            for i, oid in enumerate(a[4]):
                pts[oid][0] += 3 - i
                pts[oid][1] += 1 if i == 0 else 0
        return sorted(({"option_id": k, "points": v[0], "first_choice": v[1]} for k, v in pts.items()),
                      key=lambda x: -x["points"])

    viewer = "E01"
    agg_forecasts = []
    for qi, q in enumerate(fq):
        v1 = [a[0][qi] for a in ANSWERS.values()]
        s = stats(v1)
        s.update({"question_id": q["question_id"], "acaps_baseline": None,
                  "seeing_count": sum(q["trigger_id"] in a[3] for a in ANSWERS.values()),
                  "you": ANSWERS[viewer][0][qi]})
        agg_forecasts.append({"question_id": s.pop("question_id"), **s})
    write(f"aggregate_{ROUND_ID}.json", {
        "round_id": ROUND_ID, "n_responses": len(ANSWERS), "suppressed": False, "reason": None,
        "rating": {"probability": rating_counts(1), "impact": rating_counts(2),
                   "you": {"probability": ANSWERS[viewer][1], "impact": ANSWERS[viewer][2]}},
        "forecasts": agg_forecasts, "ranking": ranking_points(), "can_revise": True})
    write("aggregate_suppressed.json", {
        "round_id": ROUND_ID, "n_responses": 2, "suppressed": True,
        "reason": "Fewer than 3 responses so far. The group view unlocks at 3 to protect anonymity.",
        "can_revise": False})

    # POST example (Kestrel, v1)
    k = ANSWERS[viewer]
    write("post_response_request.json", {
        "invite_token": exp[viewer]["invite_token"], "tier": "known", "version": 1, "missing_text": k[6],
        "answers": [{"question_id": "Q-R1043-RATING", "rating_probability": k[1], "rating_impact": k[2]}]
        + [{"question_id": q["question_id"], "prob": p, "seeing": q["trigger_id"] in k[3]} for q, p in zip(fq, k[0])]
        + [{"question_id": "Q-TCD-TOP3", "ranking": k[4], "ranking_other": k[5]}]})
    write("post_response_201.json", {"contribution_ids": [c["id"] for c in contribs if c["author_token"] == viewer and c["version"] == 1],
                                     "version": 1})

    # track record (Kestrel)
    resolved = []
    for rid, p in TRACK_RECORD_PAST.items():
        rr = rows[rid]
        outcome = rr["Status"] == "Materialised"
        ap = PROB_MAP[rr["Probability"]]
        resolved.append({"question_id": f"Q-{rid}-BACKTEST", "risk_id": rid,
                         "text": f"Will this risk materialise? {rr['Risk Title'].strip()} ({rr['Country']})",
                         "your_prob": p, "outcome": outcome, "brier": round((p - outcome) ** 2, 4),
                         "acaps_prob": ap, "acaps_brier": round((ap - outcome) ** 2, 4), "backtest": True})
    write("me_track_record.json", {
        "author_token": viewer,
        "mean_brier": round(sum(x["brier"] for x in resolved) / len(resolved), 4),
        "acaps_mean_brier": round(sum(x["acaps_brier"] for x in resolved) / len(resolved), 4),
        "resolved": resolved,
        "pending": [{"question_id": q["question_id"], "text": q["text"], "your_prob": p, "closes_at": q["closes_at"]}
                    for q, p in zip(fq, k[0])],
        "impact": [{"risk_id": "R1043", "date": "2026-11-20",
                    "note": "Your point on refugee–host tensions at water points was added to the R1043 rationale (synthetic example)."}]})

    # moderator view
    forecasts_mod = []
    for qi, q in enumerate(fq):
        v1 = [a[0][qi] for a in ANSWERS.values()]
        v2 = [latest(e, qi) for e in ANSWERS]
        shifts = [abs(REVISIONS[e][qi] - ANSWERS[e][0][qi]) for e in REVISIONS]
        by_region = []
        for reg in ["East", "N'Djamena", "Abroad"]:
            vals = [ANSWERS[e][0][qi] for e in ANSWERS if exp[e]["macro_region"] == reg]
            if len(vals) >= 3:
                by_region.append({"macro_region": reg, "n": len(vals), "median": pct(vals, 0.5)})
        forecasts_mod.append({"question_id": q["question_id"], "trigger_id": q["trigger_id"],
                              "acaps_completion_rate": next(t["completion_rate"] for t in triggers if t["trigger_id"] == q["trigger_id"]),
                              "v1": stats(v1), "v2": stats(v2), "n_revised": len(shifts),
                              "mean_abs_shift": round(sum(shifts) / len(shifts), 3),
                              "seeing_count": sum(q["trigger_id"] in a[3] for a in ANSWERS.values()),
                              "by_region": by_region, "by_region_dropped": ["N'Djamena"]})
    vault_name = {v["expert_id"]: v["name"] for v in vault}
    def shown_as(eid):
        t = exp[eid]["default_tier"]
        return vault_name[eid] if t == "known" else exp[eid]["pseudonym"] if t == "pseudonymous" else "Anonymous"
    tiers = {}
    for e in ANSWERS:
        tiers[exp[e]["default_tier"]] = tiers.get(exp[e]["default_tier"], 0) + 1
    write(f"moderator_round_{ROUND_ID}.json", {
        "round": {**round_obj, "stage": "reveal"},
        "n_invited": len(EXPERTS), "n_responses": len(ANSWERS), "tiers": tiers,
        "rating": {"probability": rating_counts(1), "impact": rating_counts(2), "acaps": {"probability": r["Probability"], "impact": int(r["Impact"])}},
        "forecasts": forecasts_mod,
        "missing": [{"contribution_id": missing_ids[e], "shown_as": shown_as(e), "tier": exp[e]["default_tier"], "text": a[6]}
                    for e, a in ANSWERS.items() if a[6]],
        "synthesis": {
            "generated_by": "mock (Claude API in Lane B, moderator side only)",
            "clusters": [
                {"theme": "Refugee–host tensions and water access", "summary": "Two field experts in the East report rising tensions and longer, riskier trips to water points.", "contribution_ids": [missing_ids["E01"], missing_ids["E07"]]},
                {"theme": "Health risks in overcrowded sites", "summary": "Disease outbreak risk (hepatitis E, cholera) around Adré is absent from priority needs.", "contribution_ids": [missing_ids["E06"]]},
                {"theme": "Shifting smuggling routes and infrastructure", "summary": "Fuel routes moving north after the August strike; Amdjarass airstrip flagged (relates to T0619).", "contribution_ids": [missing_ids["E03"]]},
                {"theme": "Security-force cohesion", "summary": "Zaghawa networks in the army raise defection risk (relates to T0620).", "contribution_ids": [missing_ids["E04"]]},
                {"theme": "Funding cuts", "summary": "Ration cuts from January would amplify all triggers.", "contribution_ids": [missing_ids["E02"]]},
            ],
            "suggested_rating_change": "Keep probability High and impact 4. Consider adding Health and WASH to priority needs. Experts are split on T0620 (proxy mobilisation).",
        },
        "ranking": ranking_points(),
        "ranking_other": [a[5] for a in ANSWERS.values() if a[5]],
    })

    # public summary: aggregates only
    pub = [{
        "round_id": ROUND_ID, "risk_id": "R1043", "risk_title": risk["title"], "published_at": "2026-11-14T10:00:00Z",
        "n_responses": len(ANSWERS),
        "headline": "Panel broadly agrees with ACAPS's High rating; sustained cross-border attacks seen as most likely",
        "summary_text": "Most of the Chad panel agrees with the High probability and impact 4 rating, with a minority seeing it as too low. Experts flag refugee–host tensions over water and health risks in overcrowded sites as gaps in the current analysis.",
        "rating_agreement": {"probability": rating_counts(1), "impact": rating_counts(2)},
        "forecasts": [{"question_id": q["question_id"], "text": q["text"], "median": pct([latest(e, qi) for e in ANSWERS], 0.5), "n": len(ANSWERS)}
                      for qi, q in enumerate(fq)],
    }]
    dump = json.dumps(pub, ensure_ascii=False)
    for e in EXPERTS:
        assert token_of[e[0]] not in dump and (e[1] == "-" or e[1] not in dump), f"public summary leaks {e[0]}"
    for a in ANSWERS.values():
        assert not a[6] or a[6] not in dump, "public summary contains verbatim free text"
    write("public_summaries.json", pub)

    print(f"wrote fixtures for {ROUND_ID}: {len(contribs)} contributions, {len(experts)} experts")


if __name__ == "__main__":
    main()
