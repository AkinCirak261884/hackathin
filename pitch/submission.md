# Submission: Ground Truth

**Repo:** https://github.com/AkinCirak261884/hackathin
**Live demo:** https://groundtruth-acaps.vercel.app (demo data, works on a phone)

**Short description**

Ground Truth is a three-minute monthly check-in for ACAPS's trusted field experts. On a live ACAPS risk (demo: R1043, eastern Chad) experts say whether ACAPS's rating is right, flag the triggers they see, and forecast each one before a deadline, choosing per answer whether they're anonymous, pseudonymous or known to ACAPS. Then they read the panel's reasons before any numbers, may update once, and only then see the group's answers; their blind answer is the one that's scored. Over time each expert builds a private track record against ACAPS's own rating, and sees when their input changed the analysis. ACAPS gets a moderator page with agreement, revisions and what's missing, grouped by AI and checked by a person; the public sees aggregates only, never below 3 answers. A backtest on 99 resolved Risk Radar risks sets the baseline: ACAPS's ratings score a Brier of 0.213 against 0.239 for always guessing the base rate.

**How it's built:** React + Vite expert app (English and French), FastAPI API on Supabase/Postgres with a separate identity vault, Python scoring and backtest on the Risk Radar export. All experts in the demo are synthetic.
