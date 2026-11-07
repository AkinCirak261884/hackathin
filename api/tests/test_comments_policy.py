"""Comments on/off from OCHA 3W presence (team decision 7 Nov): few organisations -> off."""
import os

import pytest
from fastapi.testclient import TestClient

from api import comments_policy as cp
from api.main import app

client = TestClient(app)


def d(title, country):
    return cp.decide({"risk_id": "X", "title": title, "country": country})


def test_snapshot_has_three_countries_with_source():
    c = cp.presence()["countries"]
    assert set(c) == {"TCD", "SDN", "UKR"}
    for v in c.values():
        assert v["dataset"].startswith("https://data.humdata.org/dataset/") and "CC BY" in v["licence"]
        assert v["n_orgs_country"] > 100


def test_eastern_chad_region_is_on():
    r = d("Escalating cross-border insecurity ... in eastern Chad", "Chad")
    assert r["enabled"] is True and r["areas"] == ["Ouaddai", "Sila", "Wadi Fira", "Ennedi Est"]
    assert r["n_orgs"] >= 124 and "eastern chad" in r["area_basis"]


def test_small_presence_is_off():
    r = d("Interregional trade restrictions disrupt markets ... in West Kordofan", "Sudan")
    assert r["enabled"] is False and r["areas"] == ["West Kordofan"] and r["n_orgs"] < r["min_orgs"]
    assert "comments off" in r["reason"]


def test_named_state_beats_region_and_other_countries_ignored():
    # "eastern Chad" is in another country than the risk (Sudan): only West Darfur counts
    r = d("Mass returns from eastern Chad exacerbate humanitarian needs in West Darfur State", "Sudan")
    assert r["areas"] == ["West Darfur"]


def test_word_northern_needs_state():
    assert d("Northern areas see protests", "Sudan")["areas"] == []
    assert d("Drone attacks on the power grid in Northern state", "Sudan")["areas"] == ["Northern"]


def test_union_counts_an_org_once():
    one = d("x in North Kordofan", "Sudan")["n_orgs"]
    two = d("x in North Kordofan and White Nile state", "Sudan")["n_orgs"]
    c = cp.presence()["countries"]["SDN"]["areas"]
    assert max(one, c["White Nile"]["n_orgs"]) <= two <= one + c["White Nile"]["n_orgs"]


def test_whole_country_and_unknown_country():
    assert d("Attacks on energy infrastructure", "Ukraine")["n_orgs"] == 427
    r = d("Floods", "Haiti")
    assert r["enabled"] is False and r["n_orgs"] is None and r["source"] is None


def test_threshold_from_env(monkeypatch):
    monkeypatch.setenv("COMMENTS_MIN_ORGS", "500")
    assert d("x in eastern Chad", "Chad")["enabled"] is False
    monkeypatch.setenv("COMMENTS_MIN_ORGS", "5")
    assert d("x in West Kordofan", "Sudan")["enabled"] is True


def test_round_endpoints_carry_comments_block():
    with client:
        rnd = client.get("/rounds/RND-R1043-1").json()
        assert rnd["comments"]["enabled"] is True and rnd["comments"]["source"]["as_of"]
        mod = client.get("/moderator/rounds/RND-R1043-1").json()
        assert mod["comments"] == rnd["comments"]
