# Spec: Alternating & Biweekly Chores

## Problem

Currently chores are assigned to a single kid with DAILY or WEEKLY frequency. Real families need:

1. **Alternating chores** — 2+ kids take turns doing the same chore (e.g., Kid A does dishes Mon/Wed/Fri, Kid B does Tue/Thu/Sat)
2. **Every-other-day chores** — A chore that only needs doing every 2 days
3. **Biweekly chores** — A chore due every 2 weeks

---

## Proposed Design

### Core Concept: Rotation Groups

Instead of complicating the `Chore` model with many frequency types, introduce a **Rotation Group** — a shared chore that rotates between kids on a schedule.

### New Data Model

```
RotationGroup (new table)
├── id: int (PK)
├── name: str              # "Dishes", "Take Out Trash"
├── description: str?
├── frequency: RotationFrequency  # ALTERNATING_DAILY, EVERY_OTHER_DAY, BIWEEKLY
├── start_date: date       # Rotation anchor date (determines who starts)
├── archived: bool
│
├── members: [RotationMember]  # Which kids participate
└── (no kid_id — shared across kids)

RotationMember (new table)
├── id: int (PK)
├── group_id: int (FK → RotationGroup)
├── kid_id: int (FK → User)
├── position: int          # Order in rotation (0, 1, 2...)
```

### Frequency Types

```python
class RotationFrequency(str, Enum):
    ALTERNATING_DAILY = "ALTERNATING_DAILY"   # Kids take turns each day
    EVERY_OTHER_DAY = "EVERY_OTHER_DAY"       # One kid, every 2 days
    BIWEEKLY = "BIWEEKLY"                     # One kid (or rotating), every 2 weeks
```

### How Rotation Assignment Works

**ALTERNATING_DAILY** (most common use case):
- Given N kids in the rotation, each day the "active" kid is determined by:
  ```
  days_since_start = (today - group.start_date).days
  active_position = days_since_start % len(members)
  active_kid = members[active_position].kid_id
  ```
- Example: Group "Dishes" with [Grayson(pos=0), Owen(pos=1)], start_date=Monday
  - Monday → Grayson, Tuesday → Owen, Wednesday → Grayson, ...

**EVERY_OTHER_DAY** (single kid or rotating):
- Chore is only due every 2nd day from `start_date`
- If multiple members: rotates through them on due days
  ```
  days_since_start = (today - group.start_date).days
  is_due_today = (days_since_start % 2) == 0
  if multiple members:
      rotation_index = (days_since_start // 2) % len(members)
  ```

**BIWEEKLY** (single kid or rotating):
- Due once every 2 weeks (on the same weekday as `start_date`)
- If multiple members: alternates which kid each period
  ```
  weeks_since_start = (today - group.start_date).days // 7
  is_due_this_week = (weeks_since_start % 2) == 0
  if multiple members:
      rotation_index = (weeks_since_start // 2) % len(members)
  ```

---

## Changes Required

### Backend

**1. Models (`backend/models.py`)**
- Add `RotationGroup` table
- Add `RotationMember` table
- Add `RotationFrequency` enum
- Add optional `rotation_group_id` to `ChoreLog` (to link logs to rotation chores)

**2. New Service (`backend/services/rotation.py`)**
- `get_todays_rotation_chores(kid_id) → list` — Returns rotation chores assigned to this kid today
- `get_rotation_schedule(group_id, date_range) → dict` — Preview who does what and when
- `mark_rotation_complete(group_id, kid_id, date)` — Create a ChoreLog for the rotation chore
- `calculate_rotation_expected(kid_id, week_id) → int` — How many rotation instances this kid was expected to complete this week (for payout)

**3. API (`backend/api/rotations.py`)**
- `GET /api/rotations/` — List all rotation groups
- `POST /api/rotations/` — Create rotation group with members
- `PUT /api/rotations/{id}` — Update group
- `DELETE /api/rotations/{id}` — Archive group
- `GET /api/rotations/{id}/schedule?weeks=2` — Preview schedule
- `POST /api/rotations/{id}/complete` — Mark today's rotation done

**4. Payout Integration (`backend/services/payout.py`)**
- `calculate_and_payout()` must include rotation chores in instance counting:
  ```
  # Current: total_expected = sum(7 if DAILY else 1 for chore in kid_chores)
  # New:     total_expected += rotation_service.calculate_rotation_expected(kid_id, week_id)
  ```
- Rotation instances count the same as regular chore instances

**5. Automation (`backend/services/automation.py`)**
- `daily_maintenance()` must also create INCOMPLETE logs for missed rotation chores

**6. Chores Service (`backend/services/chores.py`)**
- `calculate_weekly_progress()` must include rotation chore stats

**7. Migration**
- Alembic migration to add `rotation_groups` and `rotation_members` tables
- Add `rotation_group_id` (nullable) to `chore_log`

### Kiosk UI

**8. Dashboard (`kiosk/views/dashboard.py`)**
- Show rotation chores in today's chore list alongside regular chores
- Visual indicator that it's a shared/rotation chore (e.g., 🔄 icon, or "Shared with Owen")
- Only show to the kid whose turn it is today

**9. Quest Manager (`kiosk/views/manage_chores.py`)**
- New section or tab: "ROTATION QUESTS"
- Create rotation group: pick name → select 2+ kids → choose frequency → set start date
- Edit: reorder rotation, add/remove kids
- Preview schedule: "This week: Mon=Grayson, Tue=Owen, Wed=Grayson..."

**10. Admin Dashboard (`admin/index.html`)**
- Add rotation management to web admin
- Schedule preview table

### What Does NOT Change

- Regular DAILY/WEEKLY chores work exactly as before
- The `Chore` table is untouched (rotation chores are a parallel system)
- Payout modes (ALL_OR_NOTHING / PRORATED) work the same — rotation chores just add to the instance counts
- PIN verification, ledger, streaks — all unchanged

---

## UI Flow Example

**Creating a rotation chore (Quest Manager):**
```
[ROTATION QUESTS tab]
  Name: "Dishes"
  Frequency: [Alternating Daily ▼]
  Crew: [✓ Grayson] [✓ Owen]  (multi-select)
  Starting: [Grayson ▼]  (who goes first)
  [CREATE]
```

**Kid dashboard (Grayson's view on Monday):**
```
TODAY'S QUESTS
  ☐ Walk Dog          (daily)
  ☐ Dishes 🔄         (your turn today — alternates with Owen)
  ☐ Clean Room        (weekly)
```

**Kid dashboard (Owen's view on Monday):**
```
TODAY'S QUESTS
  ☐ Feed Cat           (daily)
  ☐ Take Out Trash     (daily)
  (Dishes not shown — it's Grayson's turn)
```

---

## Payout Impact

**Example: Grayson has 2 daily chores + alternating dishes**

In a 7-day week with alternating dishes (2 kids):
- Regular daily instances: 2 × 7 = 14
- Rotation instances (Grayson's turns): 4 days (Mon/Wed/Fri/Sun) = 4
- **Total expected: 18**
- If Grayson completes all: 18/18 = 100% → full allowance

This means each kid's expected instance count is different based on their rotation schedule for that specific week, which is correct — they only need to do it on their assigned days.

---

## Implementation Order

1. **Models + Migration** — Add tables, run alembic
2. **Rotation Service** — Core logic for determining who does what when
3. **API endpoints** — CRUD + schedule preview
4. **Payout integration** — Include rotation in instance counts
5. **Automation integration** — Missed rotation chore marking
6. **Kiosk dashboard** — Show rotation chores to correct kid
7. **Kiosk quest manager** — Create/edit rotation groups
8. **Admin web UI** — Rotation management

**Estimated effort: 3-4 focused sessions**

---

## Open Questions

1. **Should rotation chores also support a "due window"?** (e.g., dishes must be done by 8 PM)
2. **What happens when a kid is deactivated mid-rotation?** Skip them and continue with remaining members?
3. **Can a kid swap days with another kid?** (manual override for "I'll do your day if you do mine tomorrow")
4. **Should the schedule preview show on the home screen kid cards?** (e.g., "Dishes today" badge)

---

*Spec written 2026-02-16. Ready for implementation on approval.*
