# FEATURE CHECKLIST — v0.1 (AUTHORITATIVE)
Project: Raspberry Pi Chores & Allowance Kiosk
Status: Source of truth for “feature complete” claims.

## A) CORE ENTITIES (MUST EXIST)

- [ ] Kid / Player
    - [ ] Name
    - [ ] Weekly allowance amount (per child)
    - [ ] Starting balance (initial manual balance)
    - [ ] Streak tracking state
    - [ ] Assigned chores

- [ ] Chore / Quest
    - [ ] Assigned kid
    - [ ] Daily or weekly recurrence
    - [ ] Weekly reset
    - [ ] Core vs non-core flag
    - [ ] Weight value (core chores weighted more heavily)
    - [ ] Due time (optional)
    - [ ] Default due handling (Daily->EOD, Weekly->Sunday)
    - [ ] Multi-completion support (N times per period)
    - [ ] Editable AFTER creation (no retroactive effect)

- [ ] Completion Record
    - [ ] Timestamp
    - [ ] Kid-marked completion
    - [ ] Approval state: pending / approved / rejected
    - [ ] Optional rejection note
    - [ ] Missed flag (system-generated)

- [ ] Ledger Entry
    - [ ] Credit (allowance, bonus)
    - [ ] Debit (purchase, cash paid out)
    - [ ] Amount
    - [ ] Note
    - [ ] Timestamp
    - [ ] Balance derived ONLY from ledger

## B) ALLOWANCE & PAYOUT LOGIC (REQUIRED)

- [ ] Weekly tally occurs every Sunday
- [ ] Tally time configurable in Admin UI
- [ ] Per-child fixed weekly allowance
- [ ] Default payout mode: prorated by completion %
- [ ] Admin override: all-or-nothing toggle
- [ ] Threshold % configurable
- [ ] Weighted completion calculation (Core > Non-core)
- [ ] Two progress values tracked: Kid Progress (All) vs Official (Approved)
- [ ] Payout uses Official Progress ONLY
- [ ] Allowance credit written as ledger entry

## C) CHORE STATE MANAGEMENT (REQUIRED)

- [ ] Kids can mark chores complete
- [ ] Completion immediately enters “pending approval”
- [ ] Parent approval required for credit
- [ ] Missed chores automatically marked when due window closes
- [ ] Missed chores:
    - [ ] Do NOT count toward completion %
    - [ ] Are visible but locked/read-only
- [ ] Multi-completion chores:
    - [ ] Track X / N completions
    - [ ] Credit per completion up to N
    - [ ] Extra completions ignored

## D) PARENT / ADMIN CONTROLS (REQUIRED)

- [ ] Parent PIN system
- [ ] PIN required for: Approvals, Balances, Rules, Backup
- [ ] Parent approval queue (Approve/Reject + Note)
- [ ] Parent can:
    - [ ] Add/edit kids
    - [ ] Add/edit chores (weights, core flags)
    - [ ] Change weekly rules
    - [ ] Manually credit/debit ledger
- [ ] Parent-only Admin UI on kiosk
- [ ] Admin web page accessible over LAN

## E) UI / KIOSK EXPERIENCE (REQUIRED)

- [ ] Full-screen kiosk mode (Auto-launch, no OS chrome)
- [ ] Touch-first UI
- [ ] Video-game / sci-fi HUD theme (Matches reference)
- [ ] Home screen: Kid tiles, Balance, Today/Week progress, Pending indicator, Streak
- [ ] Kid view: Quest list, Status icons, Progress bars, Balance
- [ ] Parent approval screen
- [ ] Admin panel
- [ ] Reports / history screen

## F) STREAKS & GAMIFICATION (REQUIRED v0.1)

- [ ] Daily streak tracking
- [ ] Streak visible on Kid tile / Detail
- [ ] (Optional) Core-chore streak

## G) REPORTING & HISTORY (REQUIRED)

- [ ] Weekly summaries per kid
- [ ] Drill-down into a specific week
- [ ] Ledger history per kid
- [ ] Read-only historical views
- [ ] No retroactive mutation of history

## H) DATA, BACKUP, & UPDATES (REQUIRED)

- [ ] SQLite is single source of truth
- [ ] Database stored outside app release directory
- [ ] USB backup export (ZIP with DB+Config)
- [ ] USB restore import (Validation, Safety Backup)
- [ ] Schema/app version recorded
- [ ] Release-folder update strategy
- [ ] Healthcheck before finalizing update
- [ ] Automatic rollback on failure
- [ ] NO microSD removal required

## I) CONNECTIVITY & FUTURE EXTENSIBILITY (REQUIRED)

- [ ] App functions fully offline
- [ ] LAN connectivity supported
- [ ] Backend API suitable for future iOS app
- [ ] No hardcoded paths or credentials
- [ ] Business logic centralized in backend
