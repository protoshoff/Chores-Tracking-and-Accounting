# Test Plan v1.0

## 1. Strategy
- **Backend:** Automated Unit & Integration tests using `pytest` and `sqlite` (in-memory or temp file).
- **Frontend:** Manual verification for Kiosk UI (due to hardware dependency).
- **Integration:** "Skeleton Smoke Test" to verify End-to-End connectivity.

## 2. Backend Test Matrix (Automated)

### 2.1. Models & Database
- [ ] **Schema Creation:** Verify `SQLModel.metadata.create_all` works cleanly.
- [ ] **Migrations:** Verify `alembic upgrade head` applies all version files.
- [ ] **User Model:** Verify `balance_cents` defaults to 0.
- [ ] **Chore Model:** Verify `frequency` enum constraints.

### 2.2. API Endpoints
*Fixtures:* Fresh DB with 1 Kid ("Alice") and 1 Chore ("Walk Dog").

#### Kids
- [ ] `GET /api/kids`: Returns list containing Alice.
- [ ] `GET /api/kids/{id}`: Returns Alice details.
- [ ] `GET /api/kids/{invalid_id}`: Returns 404.

#### Chores
- [ ] `GET /api/kids/{id}/chores`: Returns "Walk Dog".
- [ ] `POST .../complete`:
    - Valid: Returns 201, status `PENDING`.
    - Duplicate complete: Returns 400 or updates existing? (Rule: Multi-complete allowed? Spec says "Multi-completion supported". So returns 201).
    - Invalid Kid: Returns 404.

#### Approvals
- [ ] `GET /api/approvals/pending`: Shows the pending chore.
- [ ] `POST .../review`:
    - Action `APPROVE`: Status becomes `APPROVED`. Alice's progress updates.
    - Action `REJECT`: Status becomes `REJECTED`. Alice's progress reverts.

#### Ledger & Rollup
- [ ] `POST /api/ledger/transaction`: Balance updates correctly.
- [ ] `POST /api/ledger/payout`: Trigger weekly payout.
    - Setup: Mark chores done -> Approve -> Trigger Payout.
    - Assert: Transaction created. Balance increased. Rollup record created.

## 3. Operations & Deployment Tests
- [ ] **Backup:** Call `/api/system/backup` -> Verify zip response contains `chores.db`.
- [ ] **Restore:** Mock USB restore script -> Verify DB replaced.

## 4. UI Verification (Manual)
1. **Boot:** App launches fullscreen.
2. **Home:** Shows Alice.
3. **Dash:** Alice's balance matches DB.
4. **Action:** Alice taps "Walk Dog" -> Checkbox checks -> "Pending" badge appears.
5. **Admin:** Enter PIN -> Approve "Walk Dog".
6. **Dash:** Refresh -> "Walk Dog" marked Approved. Progress bar grows.
