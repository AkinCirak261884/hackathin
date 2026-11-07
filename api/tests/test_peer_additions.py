"""Peers see expert additions without authors, only once the round is unlocked, plus a summary."""
from fastapi.testclient import TestClient

from api import main

c = TestClient(main.app)
R = "RND-R1043-1"


def answer(inv, missing):
    body = {"invite_token": inv, "tier": "pseudonymous", "version": 1, "missing_text": missing,
            "answers": [{"question_id": "Q-R1043-AGREE", "agree": True}, {"question_id": "Q-R1043-T0618", "prob": 0.6}]}
    assert c.post(f"/rounds/{R}/responses", json=body).status_code == 201


def test_additions_hidden_until_reveal_then_shown_without_authors():
    answer("inv_demo_01", "Rainy season.\nSeeing, not on ACAPS's list (may be bigger than this risk): Armed group recruiting in camps")
    answer("inv_demo_02", "Risk missing from the top-3 list: Cholera in the east")
    answer("inv_demo_03", "Seeing, not on ACAPS's list: Fuel prices doubled")
    blind = c.get(f"/rounds/{R}/thread", headers={"X-Invite-Token": "inv_demo_01"}).json()
    assert "additions" not in blind and blind["locked"]
    assert c.post(f"/moderator/rounds/{R}/advance", json={"to": "reveal"}).status_code == 200
    t = c.get(f"/rounds/{R}/thread", headers={"X-Invite-Token": "inv_demo_01"}).json()
    if not t["comments"]["enabled"]:
        assert "additions" not in t
        return
    texts = {a["text"]: a for a in t["additions"]}
    assert texts["Armed group recruiting in camps"]["bigger"] is True
    assert texts["Cholera in the east"]["kind"] == "risk"
    assert texts["Fuel prices doubled"]["bigger"] is False
    assert "Rainy season." not in texts  # plain "what's missing" text stays moderator-only
    for a in t["additions"]:
        assert set(a) == {"kind", "bigger", "prob", "text"}  # no author, tier, time or id
    assert t["summary"]["source"] in ("ai", "keywords")


def test_coordinated_copy_paste_is_not_amplified():
    same = "Seeing, not on ACAPS's list (may be bigger than this risk): Army deserting the border posts tonight"
    answer("inv_demo_01", same)
    answer("inv_demo_02", same)
    answer("inv_demo_03", "Seeing, not on ACAPS's list: Fuel prices doubled")
    assert c.post(f"/moderator/rounds/{R}/advance", json={"to": "reveal"}).status_code == 200
    t = c.get(f"/rounds/{R}/thread", headers={"X-Invite-Token": "inv_demo_03"}).json()
    if not t["comments"]["enabled"]:
        return
    texts = [a["text"] for a in t["additions"]]
    assert "Army deserting the border posts tonight" not in texts
    assert "Fuel prices doubled" in texts
    assert t["withheld_coordinated"] == 2


def test_likelihood_travels_with_additions():
    answer("inv_demo_01", "Seeing, not on ACAPS's list (may be bigger than this risk) · 70% likely: Armed group recruiting in camps")
    answer("inv_demo_02", "Risk missing from the top-3 list · 40% likely: Cholera in the east")
    answer("inv_demo_03", "Seeing, not on ACAPS's list: Fuel prices doubled")
    assert c.post(f"/moderator/rounds/{R}/advance", json={"to": "reveal"}).status_code == 200
    t = c.get(f"/rounds/{R}/thread", headers={"X-Invite-Token": "inv_demo_01"}).json()
    if not t["comments"]["enabled"]:
        return
    by = {a["text"]: a for a in t["additions"]}
    assert by["Armed group recruiting in camps"]["prob"] == 0.7 and by["Armed group recruiting in camps"]["bigger"] is True
    assert by["Cholera in the east"]["prob"] == 0.4 and by["Fuel prices doubled"]["prob"] is None
