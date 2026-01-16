# API Specification v0.1

Base URL: `http://{kiosk_ip}:8000`
Content-Type: `application/json`

## Authentication
- **User (Kid):** Implicitly trusted for local read ops. Critical write ops (marking done) require `kid_id` validation.
- **Admin (Parent):** Requires header `X-Admin-PIN` containing the SHA256 hash of the parent PIN.
    - *Note:* This is security-by-obscurity suitable only for a trusted local LAN for this MVP.

## Common Models

### Error Response
```json
{
  "detail": "Error message description",
  "code": "ERROR_CODE"
}
```

### ChoreStatus Enum
- `PENDING`: Marked done by kid, waiting for parent.
- `APPROVED`: Confirmed by parent. Counts toward progress.
- `REJECTED`: Denied by parent. Does not count.
- `INCOMPLETE`: Default state (or reset after rejection).

## 1. System & Health

### `GET /api/health`
Check system status and database connectivity.
- **Response 200 OK:**
```json
{
  "status": "online",
  "version": "0.1.0",
  "database": "connected",
  "pending_migrations": false
}
```

### `GET /api/system/backup` (Admin Only)
Trigger a database export.
- **Response 200 OK:** Returns a `.zip` file stream of the current database and config.

## 2. Kids & Profiles

### `GET /api/kids`
List all configured kids with their current status.
- **Response 200 OK:**
```json
[
  {
    "id": 1,
    "name": "Alice",
    "avatar_path": "/static/avatars/alice.png",
    "balance_cents": 1250,
    "weekly_allowance_cents": 500,
    "progress": {
       "completed_weight": 5,
       "total_weight": 10,
       "ratio": 0.5
    }
  }
]
```

### `GET /api/kids/{kid_id}`
Get details for a single kid.

## 3. Chores

### `GET /api/kids/{kid_id}/chores`
Get chores for the current view (defaults to today's active chores).
- **Query Params:**
  - `date`: `YYYY-MM-DD` (optional, defaults to today)
  - `include_weekly`: `bool` (default true)
- **Response 200 OK:**
```json
[
  {
    "id": 101,
    "name": "Walk Dog",
    "description": "Take Fido for 15 mins",
    "weight": 1,
    "status": "INCOMPLETE", 
    "due_time": "20:00",
    "frequency": "DAILY",
    "icon": "dog"
  }
]
```

### `POST /api/chores/{chore_id}/complete`
Mark a chore as done.
- **Body:**
```json
{
  "kid_id": 1,
  "date": "2023-10-27" // To ensure we mark the right instance
}
```
- **Response 201 Created:**
```json
{
  "log_id": 505,
  "status": "PENDING",
  "message": "Good job! Sent to parent for approval."
}
```
- **Response 400 Bad Request:** If chore is already done or not active.

## 4. Admin & Approvals (Head: X-Admin-PIN)

### `GET /api/approvals/pending`
Get all pending chore completions requiring review.
- **Response 200 OK:**
```json
[
  {
    "log_id": 505,
    "kid_name": "Alice",
    "chore_name": "Walk Dog",
    "completed_at": "2023-10-27T16:30:00Z"
  }
]
```

### `POST /api/approvals/{log_id}/review`
Approve or Reject a chore completion.
- **Body:**
```json
{
  "action": "APPROVE" // or "REJECT"
}
```
- **Response 200 OK:**
```json
{
  "log_id": 505,
  "status": "APPROVED",
  "progress_update": {
      "kid_id": 1,
      "new_ratio": 0.6
  }
}
```

## 5. Ledger & Finance (Head: X-Admin-PIN)

### `GET /api/ledger/{kid_id}`
Get transaction history.
- **Query Params:** `limit=50`
- **Response 200 OK:**
```json
[
  {
    "id": 901,
    "type": "ALLOWANCE",
    "amount_cents": 500,
    "description": "Weekly Allowance (100% completion)",
    "timestamp": "2023-10-22T09:00:00Z"
  }
]
```

### `POST /api/ledger/transaction`
Manually add a transaction (Bonus, Spend, etc.).
- **Body:**
```json
{
  "kid_id": 1,
  "type": "SPEND",
  "amount_cents": -200, // Negative for spend
  "description": "Ice Cream"
}
```
- **Response 201 Created:** Returns the new transaction and updated balance.

### `POST /api/ledger/payout`
Trigger a manual weekly allowance calculation/payout cycle (usually scheduled, but available for testing/manual override).
- **Body:** `{"week_id": "2023-W43"}`
- **Response 200 OK:** Summary of payouts created.

## 6. Settings (Admin Only)

### `GET /api/settings`
Get current system configuration.
- **Response 200 OK:**
```json
{
  "tally_time": "SUN 00:00",
  "payout_mode": "PRORATED",
  "parent_pin_hash": "sha256...",
  "allowance_enabled": true
}
```

### `PUT /api/settings`
Update system configuration.
- **Body:** Partial object (e.g. `{"payout_mode": "ALL_OR_NOTHING"}`).
- **Response 200 OK:** Updated settings.
