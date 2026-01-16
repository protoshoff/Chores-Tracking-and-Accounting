# Database Schema v1.0

## 1. Overview
- **Engine:** SQLite (`/var/lib/chores_app/chores.db`)
- **ORM:** SQLModel (Pydantic + SQLAlchemy)
- **Migrations:** Alembic (Recommended for schema evolution safety)

## 2. Tables

### 2.1. `users` (Kids)
Table: `users`
- `id` (PK, int, auto)
- `name` (str, index)
- `pin_hash` (str, nullable) - Future use
- `avatar_path` (str, default="/static/default_avatar.png")
- `allowance_cents` (int, default=0)
- `balance_cents` (int, default=0) - Denormalized cached balance
- `is_active` (bool, default=True)

### 2.2. `chores` (Definitions)
Table: `chores`
- `id` (PK, int, auto)
- `kid_id` (FK -> users.id, index)
- `name` (str)
- `description` (str, nullable)
- `weight` (int, default=1)
- `frequency` (enum: 'DAILY', 'WEEKLY')
- `due_time` (time, nullable, default="23:59")
- `archived` (bool, default=False) - Soft delete

### 2.3. `hore_log` (Instances & Completions)
Table: `chore_log`
Tracks every "instance" of a chore that *must* be done or *was* done.
- `id` (PK, int, auto)
- `chore_id` (FK -> chores.id)
- `kid_id` (FK -> users.id, index)
- `week_id` (str, index) - ISO format "YYYY-W##" (e.g. "2023-W42")
- `date` (date, index) - The due date
- `status` (enum: 'PENDING', 'APPROVED', 'REJECTED', 'INCOMPLETE')
- `completed_at` (datetime, nullable)
- `reviewed_at` (datetime, nullable)
- `notes` (str, nullable)

**"Missed" Representation:**
A row exists with `status='INCOMPLETE'` and `date < TODAY` (for daily) or `week_id < CURRENT_WEEK` (for weekly).
*Optimization:* We can either pre-generate rows for the week (easiest for querying "What do I do today?") or generate them dynamically.
*Decision:* **Pre-generate** rows on Sunday night (or upon creation of new chore) for the current week. This makes "Missed" queries trivial: `SELECT * FROM chore_log WHERE status='INCOMPLETE' AND date < :today`.

### 2.4. `ledger_entries`
Table: `ledger_entries`
- `id` (PK, int, auto)
- `kid_id` (FK -> users.id, index)
- `transaction_type` (enum: 'ALLOWANCE', 'BONUS', 'SPEND', 'PAYOUT', 'ADJUSTMENT')
- `amount_cents` (int) - Signed integer (+ credit, - debit)
- `description` (str)
- `timestamp` (datetime, default=UTC)
- `week_id` (str, nullable) - Link to a rollup if applicable

### 2.5. `weekly_rollups` (Stats)
Table: `weekly_rollups`
Stores the finalized stats for a past week.
- `id` (PK, int, auto)
- `kid_id` (FK -> users.id)
- `week_id` (str)
- `total_weight_possible` (int)
- `total_weight_completed` (int) - (Approved only)
- `payout_cents` (int)
- `finalized_at` (datetime)

### 2.6. `streaks` (Gamification)
Table: `streaks`
- `kid_id` (PK, FK -> users.id)
- `current_streak_days` (int, default=0)
- `last_completed_date` (date, nullable)
- `max_streak_days` (int, default=0)

### 2.7. `settings` (Key-Value)
Table: `settings`
- `key` (PK, str) - e.g., "parent_pin_hash", "tally_cron", "payout_mode"
- `value` (str) - JSON encoded value

- `payout_mode`: "PRORATED" (default) or "ALL_OR_NOTHING"
- `tally_time`: "SUN 00:00"

## 3. Computations

### 3.1. Rollup Calculation (Weekly)
Triggered Sunday.
For each Kid:
1. **Numerator:** Sum `chore.weight` of `chore_log` where `week_id=LAST_WEEK` AND `status='APPROVED'`.
2. **Denominator:** Sum `chore.weight` of `chore_log` where `week_id=LAST_WEEK`. (Includes Incomplete, Rejected, Approved).
    *Excludes:* Chores added *mid-week*?
    *Rule:* If a chore is assigned, it counts. Pre-generation ensures logical denominator.
3. **Ratio:** `Num / Denom`.
4. **Payout:**
   - If `PRORATED`: `Allowance * Ratio`.
   - If `ALL_OR_NOTHING`: `Allowance` if `Ratio == 1.0` else `0`.

## 4. Migration Approach
**Tool:** Alembic.
**Why:**
- SQLModel creates schemas, but doesn't handle updates (ALTER TABLE).
- We need to preserve `ledger_entries` data critically.
- Ops script will run `alembic upgrade head` on deploy.

**Files:**
- `/backend/migrations/env.py`
- `/backend/migrations/versions/xxxx_init.py`
