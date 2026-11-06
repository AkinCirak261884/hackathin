"""Synthetic expert panel for Chad (TCD) and simulated answers to a round on R1043.

All people here are invented. Each expert has a built-in forecasting bias so the backtest and
leaderboard have something to find:

    forecast logit = anchor * logit(ACAPS baseline) + skill * logit(latent truth) + bias + noise

Writes the `experts`, `rounds` and `contributions` tables (schema in BOARD.md) and, with --out,
committed JSON files in analysis/synthetic/:
    experts.json           public profiles (no names)
    vault.json             synthetic names/emails, invite tokens, device secrets (Lane B's vault)
    responses_R1043.json   one POST /rounds/{id}/responses body per expert and version

Usage:
    python3 analysis/synthetic.py --out analysis/synthetic
"""

import argparse
import hashlib
import json
import math
import random
import sqlite3
import statistics
from datetime import date
from pathlib import Path

from ingest import DEFAULT_DB, build_db
from questions import generate_questions, save_questions
from scoring import ACAPS_PROB

SEED = 8
PANEL = "TCD"
RISK_ID = "R1043"
ROUND_ID = f"RND-{RISK_ID}-1"
OPENED = date(2026, 11, 6)


# anchor: pull towards ACAPS · skill: how much of the truth they see · bias: logit shift
# noise: logit std dev · stubborn: 1 = never revises after the reveal, 0 = jumps to the median
# Only "sharp" experts know more than ACAPS. The rest add bias or noise around ACAPS's rating,
# so in the backtest only the two sharp experts should earn the super-estimator badge.
ARCHETYPES = {
    "sharp":           dict(anchor=0.1, skill=1.0,  bias=0.0,  noise=0.25, stubborn=0.8),
    "well_calibrated": dict(anchor=1.0, skill=0.0,  bias=0.0,  noise=0.3,  stubborn=0.6),  # = ACAPS, no extra info
    "anchored":        dict(anchor=1.0, skill=0.0,  bias=0.0,  noise=0.2,  stubborn=0.3),
    "alarmist":        dict(anchor=0.2, skill=0.25, bias=1.0,  noise=0.4,  stubborn=0.7),
    "complacent":      dict(anchor=0.2, skill=0.25, bias=-0.9, noise=0.4,  stubborn=0.5),
    "noisy":           dict(anchor=1.0, skill=-0.2, bias=0.0,  noise=1.0,  stubborn=0.4),  # often misreads signals
    "hedger":          dict(anchor=0.0, skill=0.1,  bias=0.0,  noise=0.2,  stubborn=0.9),
}

EXPERTS = [
    # expert_id, pseudonym, profile, region, tier, lang, archetype (ids/tiers/langs match api/seed.py)
    ("EXP-TCD-01", "Kestrel", "Local NGO director", "East (Abéché)", "known", "fr", "well_calibrated"),
    ("EXP-TCD-02", "Linden", "Food security analyst", "N'Djamena", "pseudonymous", "en", "anchored"),
    ("EXP-TCD-03", "Osprey", "OSINT conflict analyst, active on X/Telegram", "Abroad", "pseudonymous", "en", "alarmist"),
    ("EXP-TCD-04", "Birch", "Anticipatory-action officer", "East (Adré)", "known", "fr", "sharp"),
    ("EXP-TCD-05", "Heron", "Academic researcher", "Abroad", "pseudonymous", "en", "complacent"),
    ("EXP-TCD-06", "Sparrow", "Community responder near the border", "East (Adré)", "anonymous", "fr", "sharp"),
    ("EXP-TCD-07", "Alder", "Shelter/CCCM cluster staff", "East (Ouaddaï)", "known", "fr", "noisy"),
    ("EXP-TCD-08", "Wren", "Donor-agency methodologist", "Abroad", "pseudonymous", "en", "hedger"),
]

# Synthetic "what's missing" answers, written to give Lane B's AI synthesis clusters to find.
MISSING = {
    "EXP-TCD-01": "Rainy season (June to September) will cut road access to the eastern camps; the impact rating does not reflect this.",
    "EXP-TCD-03": "Drone use by armed actors near the border is growing and not mentioned as its own trigger.",
    "EXP-TCD-04": "Seasonal flooding around Adré will limit humanitarian access just as new arrivals peak.",
    "EXP-TCD-05": "Diplomatic mediation between Chad and Sudan could lower the probability; the analysis leaves this out.",
    "EXP-TCD-06": "Sites near Adré are already overcrowded, new arrivals are sleeping outside. Congestion is a driver.",
    "EXP-TCD-07": "Road access in the wet season and overcrowded transit sites, both missing.",
}


# Hidden "truth" for unresolved R1043 questions (synthetic assumption, derived from completion rate).
def latent_truth(completion_rate):
    return min(0.9, 0.2 + 1.2 * (completion_rate or 0) / 100)


def logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def round_prob(p):
    # Humans answer in steps of 5 percentage points.
    return min(0.95, max(0.05, round(p * 20) / 20))


def forecast(archetype, acaps_p, truth_p, rng):
    a = ARCHETYPES[archetype]
    x = a["anchor"] * logit(acaps_p) + a["skill"] * logit(truth_p) + a["bias"] + rng.gauss(0, a["noise"])
    return round_prob(sigmoid(x))


def author_token(expert, secret):
    # Same derivation as Lane B's api/trust.py.
    expert_id, tier = expert[0], expert[4]
    if tier == "anonymous":
        return "anon_" + hashlib.sha256(("groundtruth-anon-v1:" + secret).encode()).hexdigest()[:32]
    return "psd_" + expert_id


def simulate(con, seed=SEED):
    """Simulate round 1 and the post-reveal revision for R1043. Returns a dict of outputs."""
    rng = random.Random(seed)
    con.row_factory = sqlite3.Row
    risk = con.execute("SELECT * FROM risks WHERE risk_id = ?", (RISK_ID,)).fetchone()
    acaps_p = ACAPS_PROB[risk["probability"]]
    questions = generate_questions(con, OPENED, [RISK_ID])
    save_questions(con, questions)
    rates = dict(con.execute("SELECT trigger_id, completion_rate FROM triggers WHERE risk_id = ?", (RISK_ID,)))
    forecasts = [q for q in questions if q["kind"] == "forecast"]

    vault, responses = [], []
    v1 = {}  # expert_id -> {question_id: prob}
    for i, expert in enumerate(EXPERTS, start=1):
        expert_id, _, _, _, tier, _, archetype = expert
        secret = f"device-secret-{rng.getrandbits(64):016x}"
        vault.append({
            "expert_id": expert_id,
            "name": f"Synthetic Expert {i:02d}",
            "email": f"synthetic.expert{i:02d}@example.org",
            "invite_token": f"inv_demo_{i:02d}",
            "device_secret": secret if tier == "anonymous" else None,
            "author_token": author_token(expert, secret),
        })
        probs = {
            q["question_id"]: forecast(archetype, acaps_p, latent_truth(rates[q["trigger_id"]]), rng)
            for q in forecasts
        }
        v1[expert_id] = probs
        view = forecast(archetype, acaps_p, 0.75, rng)  # own view of the risk's overall probability
        observed = [q["trigger_id"] for q in forecasts if probs[q["question_id"]] >= 0.6]
        responses.append(_body(vault[-1], tier, 1, abs(view - acaps_p) <= 0.15, probs, observed, MISSING.get(expert_id)))

    # Delphi step: after the reveal, less stubborn experts move towards the group median once.
    medians = {q["question_id"]: statistics.median(v[q["question_id"]] for v in v1.values()) for q in forecasts}
    for expert, entry, first in zip(EXPERTS, vault, list(responses)):
        stubborn = ARCHETYPES[expert[6]]["stubborn"]
        revised = {
            qid: round_prob(p + (1 - stubborn) * (medians[qid] - p)) for qid, p in v1[expert[0]].items()
        }
        if any(abs(revised[qid] - p) >= 0.05 for qid, p in v1[expert[0]].items()):
            agree = next(a["agree"] for a in first["answers"] if a["question_id"].endswith("AGREE"))
            responses.append(_body(entry, expert[4], 2, agree, revised, first["triggers_observed"], None))

    return {"experts": _profiles(), "vault": vault, "responses": responses}


def _body(vault_entry, tier, version, agree, probs, observed, missing):
    answers = [{"question_id": f"Q-{RISK_ID}-AGREE", "agree": bool(agree)}]
    answers += [{"question_id": qid, "prob": p} for qid, p in probs.items()]
    body = {
        "invite_token": vault_entry["invite_token"],
        "tier": tier,
        "version": version,
        "answers": answers,
        "triggers_observed": observed,
        "missing_text": missing,
        "_author_token": vault_entry["author_token"],  # what Lane B's API should derive; not sent
    }
    if tier == "anonymous":
        body["device_secret"] = vault_entry["device_secret"]
    return body


def _profiles():
    return [
        {"expert_id": e[0], "pseudonym": e[1], "profile": e[2], "region": e[3], "country_panel": PANEL,
         "lang": e[5], "default_tier": e[4], "archetype": e[6]}
        for e in EXPERTS
    ]


def save(con, out):
    con.executescript("""
        DROP TABLE IF EXISTS experts; DROP TABLE IF EXISTS rounds; DROP TABLE IF EXISTS contributions;
        CREATE TABLE experts (expert_id TEXT PRIMARY KEY, pseudonym TEXT NOT NULL,
            country_panel TEXT NOT NULL, lang TEXT NOT NULL, default_tier TEXT NOT NULL);
        CREATE TABLE rounds (round_id TEXT PRIMARY KEY, risk_id TEXT NOT NULL,
            stage TEXT NOT NULL, opened_at TEXT NOT NULL);
        CREATE TABLE contributions (id INTEGER PRIMARY KEY AUTOINCREMENT, round_id TEXT NOT NULL,
            question_id TEXT NOT NULL, author_token TEXT NOT NULL, tier TEXT NOT NULL, prob REAL,
            agree INTEGER, missing_text TEXT, version INTEGER NOT NULL, created_at TEXT NOT NULL);
    """)
    con.executemany(
        "INSERT INTO experts VALUES (:expert_id, :pseudonym, :country_panel, :lang, :default_tier)",
        out["experts"],
    )
    con.execute("INSERT INTO rounds VALUES (?, ?, 'reveal', ?)", (ROUND_ID, RISK_ID, OPENED.isoformat()))
    for n, body in enumerate(out["responses"]):
        created = f"{OPENED.isoformat()}T{18 + body['version']}:{n * 3 % 60:02d}:00"
        for a in body["answers"]:
            is_agree = "agree" in a
            con.execute(
                "INSERT INTO contributions (round_id, question_id, author_token, tier, prob, agree,"
                " missing_text, version, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ROUND_ID, a["question_id"], body["_author_token"], body["tier"], a.get("prob"),
                 int(a["agree"]) if is_agree else None, body["missing_text"] if is_agree else None,
                 body["version"], created),
            )
    con.commit()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--out", help="directory for experts.json, vault.json, responses_R1043.json")
    args = parser.parse_args()

    if not Path(args.db).exists():
        build_db(args.db).close()
    con = sqlite3.connect(args.db)
    out = simulate(con)
    save(con, out)
    n_v2 = sum(r["version"] == 2 for r in out["responses"])
    print(f"Wrote {len(out['experts'])} experts, {len(out['responses'])} responses ({n_v2} revisions) to {args.db}")

    if args.out:
        d = Path(args.out)
        d.mkdir(parents=True, exist_ok=True)
        for name in ("experts", "vault"):
            (d / f"{name}.json").write_text(json.dumps(out[name], indent=2, ensure_ascii=False) + "\n")
        (d / f"responses_{RISK_ID}.json").write_text(json.dumps(out["responses"], indent=2, ensure_ascii=False) + "\n")
        print(f"Wrote JSON to {d}/")

    print(f"\n{'pseudonym':10} {'archetype':16} " + "  ".join(q[-5:] for q in sorted(
        {a['question_id'] for r in out['responses'] for a in r['answers'] if 'prob' in a})))
    for e, r in zip(out["experts"], [r for r in out["responses"] if r["version"] == 1]):
        probs = [f"{a['prob']:.2f}" for a in r["answers"] if "prob" in a]
        print(f"{e['pseudonym']:10} {e['archetype']:16} " + "   ".join(probs))


if __name__ == "__main__":
    main()
