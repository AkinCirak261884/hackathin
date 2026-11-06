"""Seed the Chad panel with 8 SYNTHETIC experts, vault entries and demo invites.

    python -m api.seed          # demo invites: inv_demo_01 ... inv_demo_08

Names/emails are fake and exist only in vault.db (example.org is reserved for docs).
"""
from api import db, trust

PANEL = [
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


def seed() -> list[str]:
    db.init_db()
    with db.main_db() as m, db.vault_db() as v:
        for i, (eid, pseud, lang, tier) in enumerate(PANEL, start=1):
            m.execute(
                "INSERT OR REPLACE INTO experts (expert_id, pseudonym, country_panel, lang, default_tier)"
                " VALUES (?,?,?,?,?)", (eid, pseud, "TCD", lang, tier))
            v.execute(
                "INSERT OR REPLACE INTO identity_vault (expert_id, name, email) VALUES (?,?,?)",
                (eid, f"Synthetic Expert {i:02d}", f"synthetic.expert{i:02d}@example.org"))
            v.execute("DELETE FROM invites WHERE invite_token = ?", (demo_invite(i),))
    for i, (eid, *_rest) in enumerate(PANEL, start=1):
        trust.create_invite(eid, "TCD", token=demo_invite(i))
    return [demo_invite(i) for i in range(1, len(PANEL) + 1)]


if __name__ == "__main__":
    print("Seeded TCD panel. Demo invites:", ", ".join(seed()))
