"""Seed R1043 (risk, triggers, questions, round) and the SYNTHETIC Chad panel.

    python -m api.seed

Panel source, in order:
1. Lane A's `analysis/synthetic/{experts,vault}.json` (or $GT_SYNTH_DIR), if present:
   invites inv_tcd_01 ... so their responses_R1043.json can be POSTed as-is.
2. Otherwise a built-in panel with invites inv_demo_01 ... inv_demo_08.
Names/emails are fake and go only into vault.db.
"""
import json
import os
import sys
from pathlib import Path

from api import db

MOCKS = Path(__file__).parent / "mocks"
ROOT = Path(__file__).resolve().parent.parent
SYNTH_DIR = Path(os.environ.get("GT_SYNTH_DIR", ROOT / "analysis" / "synthetic"))
SHORT_HORIZON = ROOT / "analysis" / "questions" / "short_horizon.json"   # Lane A: pilot questions
CSV_PATH = ROOT / "data" / "risk-radar-export.csv"

ROUND_ID, RISK_ID = "RND-R1043-1", "R1043"
RISK = (RISK_ID, "Escalating cross-border insecurity linked to the Sudan conflict increases protection "
        "risks and humanitarian needs in eastern Chad", "Chad", "High", 4, "High", "Active")
TRIGGERS = [
    ("T0618", "Expansion of cross-border attacks and insecurity", 0.4),
    ("T0619", "Attacks on strategic infrastructure in Chad", 0.1),
    ("T0620", "Renewed proxy mobilisation and cross-border armed group activity", 0.2),
]

BUILTIN_PANEL = [
    # expert_id,     pseudonym,  lang, default_tier
    ("EXP-TCD-01", "Kestrel", "fr", "known"),
    ("EXP-TCD-02", "Linden", "en", "pseudonymous"),
    ("EXP-TCD-03", "Osprey", "en", "pseudonymous"),
    ("EXP-TCD-04", "Birch", "fr", "known"),
    ("EXP-TCD-05", "Heron", "en", "pseudonymous"),
    ("EXP-TCD-06", "Sparrow", "fr", "anonymous"),
    ("EXP-TCD-07", "Alder", "fr", "known"),
    ("EXP-TCD-08", "Wren", "en", "pseudonymous"),
]


def demo_invite(i: int) -> str:
    return f"inv_demo_{i:02d}"


def load_panel(synth_dir: Path = SYNTH_DIR) -> list[dict]:
    experts, vault = synth_dir / "experts.json", synth_dir / "vault.json"
    if experts.exists() and vault.exists():
        by_id = {v["expert_id"]: v for v in json.loads(vault.read_text(encoding="utf-8"))}
        return [{**e, "name": by_id[e["expert_id"]]["name"], "email": by_id[e["expert_id"]]["email"],
                 "invite_token": by_id[e["expert_id"]]["invite_token"]}
                for e in json.loads(experts.read_text(encoding="utf-8"))]
    return [{"expert_id": eid, "pseudonym": p, "country_panel": "TCD", "lang": lang, "default_tier": tier,
             "name": f"Synthetic Expert {i:02d}", "email": f"synthetic.expert{i:02d}@example.org",
             "invite_token": demo_invite(i)}
            for i, (eid, p, lang, tier) in enumerate(BUILTIN_PANEL, start=1)]


def _impact(v: str):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def seed_risk_radar(m, csv_path: Path = CSV_PATH) -> None:
    """All 139 risks + their triggers, parsed by Lane A's analysis/ingest.py (single parser)."""
    if not csv_path.exists():
        return
    sys.path.insert(0, str(ROOT / "analysis"))
    try:
        import ingest
    finally:
        sys.path.pop(0)
    for row in ingest.load_rows(csv_path):
        rid = row["Risk ID"].strip()
        m.execute("INSERT OR IGNORE INTO risks VALUES (?,?,?,?,?,?,?)",
                  (rid, row["Risk Title"].strip(), row["Country"].strip() or None,
                   row["Probability"].strip() or None, _impact(row["Impact"].strip()),
                   row["Risk Level"].strip() or None, row["Status"].strip() or None))
        for t in ingest.parse_triggers(row["Triggers"]):
            if t.get("completion_rate") is not None and t["completion_rate"] > 1:
                t["completion_rate"] = round(t["completion_rate"] / 100, 4)  # CSV "40%" -> contract 0.4
            m.execute("INSERT OR IGNORE INTO triggers (trigger_id, risk_id, title, description, completion_rate,"
                      " objective) VALUES (:trigger_id, :risk_id, :title, :description, :completion_rate,"
                      " :objective)", t)


def seed_short_horizon(m, path: Path = SHORT_HORIZON) -> int:
    """Lane A's draft pilot questions (1-3 months). Loaded as question_set='short_horizon';
    a moderator puts them in a round with POST /moderator/rounds {"question_set": "short_horizon"}."""
    if not path.exists():
        return 0
    qs = json.loads(path.read_text(encoding="utf-8"))["questions"]
    for q in qs:
        m.execute("INSERT OR IGNORE INTO questions (question_id, risk_id, trigger_id, text, closes_at, question_set,"
                  " title, title_fr, text_fr, opens_at, resolution_criterion) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (q["question_id"], q["risk_id"], q.get("trigger_id"), q["text"], q["closes_at"], "short_horizon",
                   q.get("title"), q.get("title_fr"), q.get("text_fr"), q.get("opens_at"),
                   q.get("resolution_criterion")))
    return len(qs)


def seed_content(m) -> None:
    m.execute("INSERT OR IGNORE INTO risks VALUES (?,?,?,?,?,?,?)", RISK)  # before the CSV: known-good row
    seed_risk_radar(m)
    for tid, title, rate in TRIGGERS:
        m.execute("INSERT OR IGNORE INTO triggers (trigger_id, risk_id, title, completion_rate)"
                  " VALUES (?,?,?,?)", (tid, RISK_ID, title, rate))
    core = json.loads((MOCKS / "_questions.json").read_text(encoding="utf-8"))
    for q in core:
        m.execute("INSERT OR IGNORE INTO questions (question_id, risk_id, trigger_id, text, closes_at)"
                  " VALUES (?,?,?,?,?)", (q["question_id"], RISK_ID, q["trigger_id"], q["text"], q["closes_at"]))
    seed_short_horizon(m)
    m.execute("INSERT OR IGNORE INTO rounds (round_id, risk_id, stage, opened_at, panel) VALUES (?,?,?,?,?)",
              (ROUND_ID, RISK_ID, "blind", "2026-11-06", "TCD"))
    m.executemany("INSERT OR IGNORE INTO round_questions VALUES (?,?)", [(ROUND_ID, q["question_id"]) for q in core])


def seed(synth_dir: Path = SYNTH_DIR) -> list[str]:
    db.init_db()
    panel = load_panel(synth_dir)
    with db.main_db() as m, db.vault_db() as v:
        seed_content(m)
        for e in panel:
            m.execute("INSERT OR REPLACE INTO experts (expert_id, pseudonym, country_panel, lang, default_tier)"
                      " VALUES (?,?,?,?,?)",
                      (e["expert_id"], e["pseudonym"], e["country_panel"], e["lang"], e["default_tier"]))
            v.execute("INSERT OR REPLACE INTO identity_vault (expert_id, name, email) VALUES (?,?,?)",
                      (e["expert_id"], e["name"], e["email"]))
            # INSERT OR IGNORE: re-seeding never re-activates a revoked invite
            v.execute("INSERT OR IGNORE INTO invites (invite_token, expert_id, country_panel, created_at)"
                      " VALUES (?,?,?,datetime('now'))", (e["invite_token"], e["expert_id"], e["country_panel"]))
    return [e["invite_token"] for e in panel]


if __name__ == "__main__":
    print("Seeded R1043 + TCD panel. Invites:", ", ".join(seed()))
