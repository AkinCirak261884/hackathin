"""Backtest: score ACAPS's own ratings and the synthetic panel on resolved Risk Radar risks.

For every resolved risk (Materialised = 1, Not materialised = 0) with a probability rating,
adds a closed backtest round with one question, "Will this risk materialise?", and simulated
answers from each synthetic expert (~75% participation), then Brier-scores everything.

The ACAPS baseline uses real outcomes. The experts' "knowledge" is simulated (see synthetic.py),
so their scores demonstrate the pipeline; they are not evidence that experts beat ACAPS.

Usage:
    python3 analysis/backtest.py      # rebuilds analysis/backtest.db, writes analysis/charts/*
"""

import argparse
import json
import math
import random
import sqlite3
from pathlib import Path

from aggregate import EXTREMIZE, backtest_aggregates
from ingest import build_db
from leaderboard import leaderboard, track_record
from scoring import (ACAPS_PROB, APP_MAPPING, CALIBRATION_PRIOR, MAPPINGS, calibrated_acaps, calibration,
                     label_counts, label_table, mean_brier, resolved_outcomes, score_db)
from synthetic import EXPERTS, forecast, save, sigmoid, simulate

SEED = 1043
PARTICIPATION = 0.75
SIGNAL = 0.8  # how strongly the simulated "ground truth" points to the real outcome (logit units)
CHARTS = Path(__file__).resolve().parent / "charts"
BACKTEST_DB = Path(__file__).resolve().parent / "backtest.db"  # never the API's DB
OPENED = "2026-05-06"  # nominal; backtest rounds are already closed


def resolved_risks(con):
    return con.execute("""
        SELECT risk_id, title, probability, CASE status WHEN 'Materialised' THEN 1 ELSE 0 END
        FROM risks WHERE status IN ('Materialised', 'Not materialised') AND probability IS NOT NULL
        ORDER BY risk_id
    """).fetchall()


def add_backtest(con, vault, seed=SEED):
    """Insert backtest rounds, questions and simulated contributions. Returns (acaps_pairs, risks)."""
    rng = random.Random(seed)
    tokens = {v["expert_id"]: v["author_token"] for v in vault}
    risks = resolved_risks(con)
    links = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='round_questions'").fetchone()
    acaps_pairs = []  # (label, outcome)
    for risk_id, title, probability, outcome in risks:
        qid, rid = f"Q-{risk_id}-MAT", f"RND-{risk_id}-BT"
        acaps_p = ACAPS_PROB[probability]
        acaps_pairs.append((probability, outcome))
        # Named columns: Lane B's rounds/questions tables carry extra columns (with defaults).
        con.execute("INSERT OR REPLACE INTO rounds (round_id, risk_id, stage, opened_at) VALUES (?, ?, 'closed', ?)",
                    (rid, risk_id, OPENED))
        con.execute(
            "INSERT OR REPLACE INTO questions (question_id, risk_id, trigger_id, text, closes_at, outcome)"
            " VALUES (?, ?, NULL, ?, ?, ?)",
            (qid, risk_id, f"Will this risk materialise within six months? {title}", OPENED, outcome),
        )
        if links:  # Lane B's round → question link table
            con.execute("INSERT OR IGNORE INTO round_questions (round_id, question_id) VALUES (?, ?)", (rid, qid))
        # One shared, noisy "ground truth" per risk, so experts' errors are correlated like real ones.
        truth = sigmoid((SIGNAL if outcome else -SIGNAL) + rng.gauss(0, 1.0))
        for expert_id, *_rest, tier, _lang, archetype in EXPERTS:
            if rng.random() > PARTICIPATION:
                continue
            con.execute(
                "INSERT INTO contributions (round_id, question_id, author_token, tier, prob, version, created_at)"
                " VALUES (?, ?, ?, ?, ?, 1, ?)",
                (rid, qid, tokens[expert_id], tier, forecast(archetype, acaps_p, truth, rng), OPENED + "T12:00:00"),
            )
    con.commit()
    return acaps_pairs, risks


def summarise(con, acaps_labels, experts):
    acaps_pairs = [(ACAPS_PROB[label], y) for label, y in acaps_labels]
    base_rate = sum(y for _, y in acaps_pairs) / len(acaps_pairs)
    by_token = {}
    for token, _qid, p, y in con.execute("""
        SELECT s.author_token, s.question_id, c.prob, q.outcome FROM scores s
        JOIN questions q USING (question_id)
        JOIN contributions c ON c.author_token = s.author_token AND c.question_id = s.question_id
        WHERE s.question_id LIKE '%-MAT'
    """):
        by_token.setdefault(token, []).append((p, y))

    rows = []
    for e, token in experts:
        pairs = by_token.get(token, [])
        rows.append({
            # Anonymous-tier experts never appear with a pseudonym, and no tokens leave this file.
            "display_name": "Anonymous expert" if token.startswith("anon_") else e["pseudonym"],
            "archetype": e["archetype"], "anonymous": token.startswith("anon_"),
            "n": len(pairs), "brier": round(mean_brier(pairs), 4), "calibration": calibration(pairs),
        })
    rows.sort(key=lambda r: r["brier"])
    return {
        "n_resolved": len(acaps_pairs),
        "base_rate": round(base_rate, 3),
        "acaps_mapping_used": APP_MAPPING,
        "acaps": {"brier": round(mean_brier(acaps_pairs), 4), "calibration": calibration(acaps_pairs)},
        "acaps_brier_by_mapping": {
            name: {"brier": round(mean_brier([(m[label], y) for label, y in acaps_labels]), 4), "probabilities": m}
            for name, m in MAPPINGS.items()
        },
        "climatology_brier": round(mean_brier([(base_rate, y) for _, y in acaps_pairs]), 4),
        "acaps_by_label": label_table(con),
        "calibrated_acaps": _calibrated_summary(con),
        "experts": rows,
        "note": "ACAPS baseline uses real outcomes; synthetic experts' knowledge is simulated.",
    }


def _calibrated_summary(con):
    res = resolved_outcomes(con)
    counts = label_counts(res)
    loo = mean_brier([(calibrated_acaps(label, counts, y), y) for label, y in res.values()])
    in_sample = mean_brier([(calibrated_acaps(label, counts), y) for label, y in res.values()])
    return {
        "prior_pseudo_risks": CALIBRATION_PRIOR,
        "brier_leave_one_out": round(loo, 4),
        "brier_in_sample_leaky": round(in_sample, 4),
        "note": "Leave-one-out is the honest score and the one the badge uses; in-sample lets each risk set its own baseline.",
    }


# ---------- chart (plain SVG, no dependencies) ----------

W, H = 680, 524
X0, X1, Y0, Y1 = 64, 520, 92, 432  # plot area: x left/right, y top/bottom


def _x(p):
    return X0 + p * (X1 - X0)


def _y(p):
    return Y1 - p * (Y1 - Y0)


def _radius(n):
    # Area grows with the number of forecasts in the bin; never below the 8px minimum marker.
    return min(9.0, max(4.0, 1.4 * math.sqrt(n)))


def calibration_svg(summary):
    best, worst = summary["experts"][0], summary["experts"][-1]
    series = [
        ("s1", "ACAPS rating", f"Brier {summary['acaps']['brier']:.3f}", summary["acaps"]["calibration"]),
        ("s2", f"{best['display_name']} (best synthetic)", f"Brier {best['brier']:.3f}", best["calibration"]),
        ("s3", f"{worst['display_name']} (worst synthetic)", f"Brier {worst['brier']:.3f}", worst["calibration"]),
    ]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        'role="img" aria-labelledby="t d" font-family="system-ui, -apple-system, Segoe UI, sans-serif">',
        "<style>",
        "svg{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;"
        "--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a}",
        "@media (prefers-color-scheme: dark){svg{--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;"
        "--grid:#2c2c2a;--axis:#383835;--s1:#3987e5;--s2:#d95926;--s3:#199e70}}",
        ".t{fill:var(--ink);font-size:17px;font-weight:600}.sub{fill:var(--ink2);font-size:13px}"
        ".tick{fill:var(--muted);font-size:12px}.lab{fill:var(--ink);font-size:12px;font-weight:600}"
        ".val{fill:var(--ink2);font-size:12px}.grid{stroke:var(--grid);stroke-width:1}"
        ".axis{stroke:var(--axis);stroke-width:1}",
        "</style>",
        '<rect width="100%" height="100%" fill="var(--surface)"/>',
        '<text id="t" class="t" x="24" y="34">Calibration on resolved Risk Radar risks</text>',
        f'<text id="d" class="sub" x="24" y="56">Forecast probability vs. share that materialised · '
        f'{summary["n_resolved"]} resolved risks · experts are synthetic</text>',
    ]
    for i in range(6):
        p = i / 5
        out.append(f'<line class="grid" x1="{X0}" x2="{X1}" y1="{_y(p):.1f}" y2="{_y(p):.1f}"/>')
        out.append(f'<text class="tick" x="{X0 - 8}" y="{_y(p) + 4:.1f}" text-anchor="end">{int(p * 100)}%</text>')
        out.append(f'<text class="tick" x="{_x(p):.1f}" y="{Y1 + 20}" text-anchor="middle">{int(p * 100)}%</text>')
    out.append(f'<line class="axis" x1="{X0}" x2="{X1}" y1="{Y1}" y2="{Y1}"/>')
    out.append(f'<text class="tick" x="{(X0 + X1) / 2}" y="{Y1 + 42}" text-anchor="middle">Forecast probability</text>')
    out.append(f'<text class="tick" transform="translate(18 {(Y0 + Y1) / 2}) rotate(-90)" text-anchor="middle">'
               'Share materialised</text>')
    # Perfect-calibration reference: muted, behind the data.
    out.append(f'<line x1="{_x(0)}" y1="{_y(0)}" x2="{_x(1)}" y2="{_y(1)}" stroke="var(--axis)" stroke-width="1.5"/>')
    angle = math.degrees(math.atan2(Y1 - Y0, X1 - X0))
    out.append(f'<text class="tick" transform="translate({_x(0.8):.1f} {_y(0.8) + 16:.1f}) rotate({-angle:.1f})" '
               'text-anchor="middle">perfect calibration</text>')

    # Legend row (always present for >= 2 series).
    lx = 24
    for key, name, score, _ in series:
        out.append(f'<circle cx="{lx + 5}" cy="76" r="5" fill="var(--{key})"/>')
        out.append(f'<text class="val" x="{lx + 15}" y="80">{name}</text>')
        lx += 15 + 6.4 * len(name) + 24

    label_ys = []
    for key, name, score, pts in series:
        path = " ".join(f"{'M' if i == 0 else 'L'}{_x(b['mean_prob']):.1f},{_y(b['observed']):.1f}" for i, b in enumerate(pts))
        out.append(f'<path d="{path}" fill="none" stroke="var(--{key})" stroke-width="2" stroke-linejoin="round"/>')
        for b in pts:
            tip = f"{name}: forecast {b['mean_prob']:.0%}, materialised {b['observed']:.0%} (n={b['n']})"
            out.append(f'<g><title>{tip}</title><circle cx="{_x(b["mean_prob"]):.1f}" cy="{_y(b["observed"]):.1f}" '
                       f'r="10" fill="transparent"/><circle cx="{_x(b["mean_prob"]):.1f}" cy="{_y(b["observed"]):.1f}" '
                       f'r="{_radius(b["n"]):.1f}" fill="var(--{key})" stroke="var(--surface)" stroke-width="2"/></g>')
        # Direct label at the line end, nudged apart so labels never overlap.
        end_y = _y(pts[-1]["observed"])
        while any(abs(end_y - y) < 38 for y in label_ys):
            end_y += 38
        label_ys.append(end_y)
        out.append(f'<text class="lab" x="{X1 + 14}" y="{end_y - 2:.1f}">{name.split(" (")[0]}</text>')
        out.append(f'<text class="val" x="{X1 + 14}" y="{end_y + 13:.1f}">{score}</text>')
    out.append(f'<text class="tick" x="24" y="{H - 16}">Dot size = number of forecasts in the bin. Hover a dot for '
               'details. Data: analysis/charts/backtest_summary.json</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def run(db_path=BACKTEST_DB):
    """Rebuild db_path with the backtest. Returns (summary, leaderboard, {expert_id: track record})."""
    con = build_db(db_path)  # fresh DB: backtest rows must not mix with real responses
    con.row_factory = None
    out = simulate(con)
    save(con, out)
    acaps_labels, _ = add_backtest(con, out["vault"])
    score_db(con)
    tokens = {v["expert_id"]: v["author_token"] for v in out["vault"]}
    summary = summarise(con, acaps_labels, [(e, tokens[e["expert_id"]]) for e in out["experts"]])
    order = [q for (q,) in con.execute("SELECT question_id FROM questions WHERE question_id LIKE '%-MAT' ORDER BY risk_id")]
    summary["aggregate_backtest"] = {
        str(a): backtest_aggregates(con, order, a)["brier"] for a in (1.0, 1.25, EXTREMIZE, 2.0)
    }
    summary["aggregate_backtest_note"] = ("Group forecast Brier by extremizing factor; out-of-sample weights "
                                          "(only questions earlier by Risk ID). Synthetic experts.")
    board = leaderboard(con)
    records = {e["expert_id"]: track_record(con, tokens[e["expert_id"]]) for e in out["experts"]}
    con.close()
    return summary, board, records


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", default=BACKTEST_DB)
    args = parser.parse_args()
    if Path(args.db).resolve().parent.name == "var":
        parser.error("refusing to rebuild the API's database; use analysis/backtest.db")

    summary, board, records = run(args.db)
    CHARTS.mkdir(exist_ok=True)
    (CHARTS / "calibration.svg").write_text(calibration_svg(summary))
    (CHARTS / "backtest_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (CHARTS / "leaderboard.json").write_text(json.dumps(board, indent=2, ensure_ascii=False) + "\n")
    # One pseudonymous and one anonymous example, as Lane B would serve them to their owner.
    example = {"pseudonymous": records["EXP-TCD-01"], "anonymous": records["EXP-TCD-06"]}
    (CHARTS / "track_record_example.json").write_text(json.dumps(example, indent=2, ensure_ascii=False) + "\n")

    print(f"{summary['n_resolved']} resolved risks, base rate {summary['base_rate']:.0%}")
    for name, m in summary["acaps_brier_by_mapping"].items():
        used = " (used)" if name == summary["acaps_mapping_used"] else ""
        print(f"  {'ACAPS rating, ' + name + used:28} Brier {m['brier']:.3f}")
    print(f"  {'Always base rate':28} Brier {summary['climatology_brier']:.3f}")
    for r in summary["experts"]:
        print(f"  {r['display_name'] + ' (' + r['archetype'] + ')':28} Brier {r['brier']:.3f}  n={r['n']}")
    c = summary["calibrated_acaps"]
    print(f"  {'Calibrated ACAPS (LOO)':28} Brier {c['brier_leave_one_out']:.3f}   (in-sample, leaky: {c['brier_in_sample_leaky']:.3f})")
    print("\nPer label (n, materialised, 90% Wilson):")
    for r in summary["acaps_by_label"]:
        print(f"  {r['label']:10} n={r['n']:2} k={r['materialised']:2} rate {r['rate']:.0%} "
              f"[{r['wilson90'][0]:.0%}–{r['wilson90'][1]:.0%}] midpoint {r['midpoint']:.0%} calibrated {r['calibrated']:.0%}")
    print("\nACAPS calibration:")
    for b in summary["acaps"]["calibration"]:
        print(f"  said {b['mean_prob']:.0%} → materialised {b['observed']:.0%} (n={b['n']})")
    print("\nGroup aggregate (out-of-sample), Brier by extremizing factor:")
    for a, b in summary["aggregate_backtest"].items():
        print(f"  ×{a}: median {b['median']:.3f}  weighted {b['weighted']:.3f}  "
              f"weighted+extremized {b['weighted_extremized']:.3f}  (ACAPS {b['acaps']:.3f})")
    print("\nLeaderboard:")
    for e in board["entries"]:
        badge = "  ★ super estimator" if e["super_estimator"] else ""
        print(f"  {e['rank']}. {e['display_name']:18} {e['mean_brier']:.3f} vs calibrated ACAPS "
              f"{e['calibrated_acaps_brier_same_questions']:.3f} (gain lower90 {e['gain_vs_calibrated_acaps_lower90']:+.3f}) "
              f"raw ACAPS {e['acaps_brier_same_questions']:.3f} n={e['n_resolved']}{badge}")
    print(f"\nWrote calibration.svg, backtest_summary.json, leaderboard.json, track_record_example.json to {CHARTS}")


if __name__ == "__main__":
    main()
