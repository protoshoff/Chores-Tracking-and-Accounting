"""Core API endpoint tests."""
from datetime import date


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "running" in r.json()["message"].lower()


def test_create_kid(client):
    r = client.post("/api/management/kids", json={"name": "Alice", "allowance": 5.0})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Alice"
    assert data["allowance"] == 5.0
    assert data["balance"] == 0.0


def test_create_and_list_chores(client, seed_kid):
    r = client.post("/api/management/chores", json={
        "kid_id": seed_kid,
        "name": "Wash Dishes",
        "frequency": "DAILY",
        "reward": 1.5,
    })
    assert r.status_code == 200
    chore_id = r.json()["id"]

    r2 = client.get("/api/management/chores")
    assert r2.status_code == 200
    names = [c["name"] for c in r2.json()]
    assert "Wash Dishes" in names


def test_complete_chore(client, seed_kid, seed_chore):
    r = client.post(f"/api/chores/{seed_chore}/complete", json={
        "kid_id": seed_kid,
        "date": date.today().isoformat(),
    })
    assert r.status_code == 201
    assert r.json()["status"] == "PENDING"


def test_approval_flow(client, seed_kid, seed_chore):
    # Complete a chore
    client.post(f"/api/chores/{seed_chore}/complete", json={
        "kid_id": seed_kid,
        "date": date.today().isoformat(),
    })

    # List pending
    r = client.get("/api/approvals/pending")
    assert r.status_code == 200
    pending = r.json()
    assert len(pending) == 1
    log_id = pending[0]["id"]

    # Approve
    r2 = client.post(f"/api/approvals/{log_id}/review", json={"action": "APPROVE"})
    assert r2.status_code == 200

    # No more pending
    r3 = client.get("/api/approvals/pending")
    assert len(r3.json()) == 0


def test_no_double_credit_on_approval(client, seed_kid, seed_chore):
    """Regression: approving a chore should NOT directly change kid balance."""
    # Complete + approve
    client.post(f"/api/chores/{seed_chore}/complete", json={
        "kid_id": seed_kid,
        "date": date.today().isoformat(),
    })
    pending = client.get("/api/approvals/pending").json()
    client.post(f"/api/approvals/{pending[0]['id']}/review", json={"action": "APPROVE"})

    # Balance should still be 0 — only weekly payout credits balance
    kids = client.get("/api/kids/").json()
    kid = [k for k in kids if k["id"] == seed_kid][0]
    assert kid["balance"] == 0.0


def test_pin_verify(client):
    r = client.post("/api/system/pin/verify", json={"pin": "1234"})
    assert r.json()["valid"] is True

    r2 = client.post("/api/system/pin/verify", json={"pin": "0000"})
    assert r2.json()["valid"] is False


def test_pin_update_and_verify(client):
    # Update PIN
    r = client.put("/api/system/pin", json={"pin": "9999"})
    assert r.status_code == 200

    # Old PIN fails
    r2 = client.post("/api/system/pin/verify", json={"pin": "1234"})
    assert r2.json()["valid"] is False

    # New PIN works
    r3 = client.post("/api/system/pin/verify", json={"pin": "9999"})
    assert r3.json()["valid"] is True


def test_debug_reset_requires_pin(client):
    r = client.post("/api/debug/reset", json={"pin": "wrong"})
    assert r.status_code == 403


def test_ledger_transaction(client, seed_kid):
    r = client.post("/api/ledger/transaction", json={
        "kid_id": seed_kid,
        "amount": 5.0,
        "type": "BONUS",
        "description": "Test bonus",
    })
    assert r.status_code == 201

    history = client.get(f"/api/ledger/{seed_kid}/history").json()
    assert len(history) == 1
    assert history[0]["amount"] == 5.0


def test_config_get_and_update(client):
    r = client.get("/api/system/config")
    assert r.status_code == 200

    r2 = client.put("/api/system/config", json={"payout_mode": "PRORATED"})
    assert r2.status_code == 200

    r3 = client.get("/api/system/config")
    assert r3.json()["payout_mode"] == "PRORATED"


def test_management_approvals_delegates(client, seed_kid, seed_chore):
    """Management approval endpoints should use the same logic as /api/approvals."""
    client.post(f"/api/chores/{seed_chore}/complete", json={
        "kid_id": seed_kid,
        "date": date.today().isoformat(),
    })

    # List via management endpoint
    pending = client.get("/api/management/approvals").json()
    assert len(pending) == 1

    # Approve via management endpoint
    r = client.post(f"/api/management/approvals/{pending[0]['id']}/approve")
    assert r.status_code == 200

    # Verify it's approved
    pending2 = client.get("/api/management/approvals").json()
    assert len(pending2) == 0
