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


# ---- area size (decided 7 Nov by the team owner while Lane B was offline) ----

def test_named_village_turns_comments_off():
    r = d("Clashes near Farchana camp in Ouaddai", "Chad")
    assert r["enabled"] is False and r["basis"] == "small_place" and r["place"]["name"] == "Farchana"


def test_city_name_is_not_a_small_place():
    # "Port Sudan" is also the name of a small village in OSM, but it is a city: falls through to the area rules
    r = d("Drone strikes on the port of Port Sudan", "Sudan")
    assert r["basis"] != "small_place"


def test_admin_areas_and_countries_are_never_towns():
    for title, country in [("Escalating cross-border insecurity linked to the Sudan conflict in eastern Chad", "Chad"),
                           ("Fighting in West Darfur displaces thousands", "Sudan")]:
        assert d(title, country)["basis"] != "small_place"


def test_few_people_affected_turns_comments_off():
    # R0233 (Chad protests) has expected exposure "<20,000" in the Risk Radar
    r = cp.decide({"risk_id": "R0233", "title": "Protests and violent clashes in N'Djamena", "country": "Chad"})
    assert r["enabled"] is False and r["basis"] == "few_people" and r["people"] == "<20,000"


def test_large_area_with_many_people_and_orgs_is_on():
    r = cp.decide({"risk_id": "R1043", "title": "Escalating cross-border insecurity linked to the Sudan conflict "
                   "increases protection risks and humanitarian needs in eastern Chad", "country": "Chad"})
    assert r["enabled"] is True and r["basis"] == "large_area" and r["people"] == ">500,000"
    assert any("Populated Places" in s["title"] for s in r["sources"])


def test_people_bucket_parsing():
    assert cp.people_upper("<20,000") == 20000 and cp.people_upper("20,000-100,000") == 100000
    assert cp.people_upper(">500,000") == float("inf") and cp.people_upper("") is None
