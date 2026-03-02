"""Regression tests for recent fixes."""
from datetime import date, timedelta


def test_weekly_chore_only_shows_on_due_day(client, seed_kid):
    """Weekly chores should only appear in kid dashboard on their due day."""
    today = date.today()
    weekday = today.weekday()  # 0=Mon, 6=Sun
    other_day = (weekday + 3) % 7  # A different day

    # Create weekly chore due on a DIFFERENT day than today
    r = client.post("/api/management/chores", json={
        "kid_id": seed_kid,
        "name": "Weekly Not Today",
        "frequency": "WEEKLY",
        "reward": 1.0,
        "due_day": other_day,
    })
    assert r.status_code == 200

    # Create weekly chore due TODAY
    r2 = client.post("/api/management/chores", json={
        "kid_id": seed_kid,
        "name": "Weekly Today",
        "frequency": "WEEKLY",
        "reward": 1.0,
        "due_day": weekday,
    })
    assert r2.status_code == 200

    # Get kid's chores for today
    r3 = client.get(f"/api/kids/{seed_kid}/chores")
    assert r3.status_code == 200
    chore_names = [c["name"] for c in r3.json()]

    assert "Weekly Today" in chore_names
    assert "Weekly Not Today" not in chore_names


def test_daily_chore_always_shows(client, seed_kid, seed_chore):
    """Daily chores should show every day."""
    r = client.get(f"/api/kids/{seed_kid}/chores")
    assert r.status_code == 200
    names = [c["name"] for c in r.json()]
    assert "Test Chore" in names


def test_weekly_progress_uses_date_range(client, seed_kid, seed_chore):
    """Progress calculation should work regardless of week_id format in DB."""
    # Complete and approve a chore
    client.post(f"/api/chores/{seed_chore}/complete", json={
        "kid_id": seed_kid,
        "date": date.today().isoformat(),
    })
    pending = client.get("/api/approvals/pending").json()
    assert len(pending) >= 1
    client.post(f"/api/approvals/{pending[0]['id']}/review", json={"action": "APPROVE"})

    # Check kid summary — today_done should be >= 1
    kids = client.get("/api/kids/").json()
    kid = [k for k in kids if k["id"] == seed_kid][0]
    summary = kid["chores_summary"]
    assert summary["today_done"] >= 1
    assert summary["today_total"] >= 1


def test_approval_returns_even_if_retroactive_fails(client, seed_kid, seed_chore):
    """Approving a chore should always succeed, even if retroactive payout logic has issues."""
    client.post(f"/api/chores/{seed_chore}/complete", json={
        "kid_id": seed_kid,
        "date": date.today().isoformat(),
    })
    pending = client.get("/api/approvals/pending").json()
    assert len(pending) == 1

    r = client.post(f"/api/approvals/{pending[0]['id']}/review", json={"action": "APPROVE"})
    assert r.status_code == 200


def test_rotation_crud(client, seed_kid):
    """Test rotation group create, list, archive."""
    # Create
    r = client.post("/api/rotations/", json={
        "name": "Take Out Trash",
        "description": "Alternating trash duty",
        "frequency": "ALTERNATING_DAILY",
        "start_date": date.today().isoformat(),
        "members": [{"kid_id": seed_kid, "position": 0}],
    })
    assert r.status_code == 201
    group_id = r.json()["id"]

    # List
    r2 = client.get("/api/rotations/")
    assert r2.status_code == 200
    groups = r2.json()
    assert len(groups) >= 1
    assert any(g["name"] == "Take Out Trash" for g in groups)

    # Archive
    r3 = client.delete(f"/api/rotations/{group_id}")
    assert r3.status_code == 200

    # Should not appear in default list
    r4 = client.get("/api/rotations/")
    active_names = [g["name"] for g in r4.json()]
    assert "Take Out Trash" not in active_names


def test_rotation_chores_for_kid(client, seed_kid):
    """Rotation chores assigned today should appear for the kid."""
    client.post("/api/rotations/", json={
        "name": "Feed Dog",
        "frequency": "ALTERNATING_DAILY",
        "start_date": date.today().isoformat(),
        "members": [{"kid_id": seed_kid, "position": 0}],
    })

    r = client.get(f"/api/kids/{seed_kid}/rotation-chores")
    assert r.status_code == 200
    chores = r.json()
    assert len(chores) >= 1
    assert chores[0]["name"] == "Feed Dog"
    assert chores[0]["is_rotation"] is True


def test_kid_summary_includes_rotation_in_today_total(client, seed_kid):
    """Today's total should include rotation chores assigned today."""
    client.post("/api/rotations/", json={
        "name": "Sweep Floor",
        "frequency": "ALTERNATING_DAILY",
        "start_date": date.today().isoformat(),
        "members": [{"kid_id": seed_kid, "position": 0}],
    })

    kids = client.get("/api/kids/").json()
    kid = [k for k in kids if k["id"] == seed_kid][0]
    assert kid["chores_summary"]["today_total"] >= 1


def test_no_emoji_in_kiosk_views():
    """Ensure no emoji characters exist in kiosk view files."""
    import os
    import re

    emoji_pattern = re.compile(
        "[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001F000-\U0001FFFF]"
    )
    kiosk_dir = os.path.join(os.path.dirname(__file__), "..", "kiosk")
    issues = []

    for root, dirs, files in os.walk(kiosk_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            with open(path, "r") as fh:
                for i, line in enumerate(fh, 1):
                    if emoji_pattern.search(line):
                        issues.append(f"{path}:{i}: {line.strip()}")

    assert issues == [], f"Emoji found in kiosk files:\n" + "\n".join(issues)
