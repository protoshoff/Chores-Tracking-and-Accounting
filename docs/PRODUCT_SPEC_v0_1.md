# Product Specification v0.1: Chores & Allowance Kiosk

## 1. Overview
A touch-based kiosk application for Raspberry Pi 4 (10.1" 1024x600) to track children's chores and automate allowance calculations. The system runs offline-capable on a LAN, serving a Kiosk UI on the device and a responsive Admin/Parent UI via a local web server.

**Core Value:** Transparent, fair, and automated tracking of work vs. reward for kids, with ledger-based accountability.

## 2. Hardware & Environment
- **Device:** Raspberry Pi 4
- **Display:** Hosyond 10.1" Touchscreen (1024x600 resolution)
- **OS:** Raspberry Pi OS (Lite or Desktop with auto-login)
- **Connectivity:** LAN-connected, Offline-capable (data stored locally)
- **Boot:** Auto-boot directly to Full-screen Kiosk UI (no desktop environment visible)

## 3. User Roles
1.  **Kid (User):**
    - View assigned chores (Daily/Weekly).
    - Mark chores as "Done".
    - View current Balance and Weekly Progress.
2.  **Parent (Admin):**
    - Approve/Reject "Done" chores.
    - Manage Ledger (Add Bonus, Record Purchase/Cash Out).
    - Configure Rules (Allowance amount, Due times, Weights).
    - Admin access protected by PIN.

## 4. Core Workflows & Rules

### 4.1. Allowance & Payout Strategy
- **Cycle:** Weekly, resetting every Sunday at a configurable time (default 00:00 or user-specified).
- **Amount:** Fixed weekly allowance per child ($ Amount).
- **Payout Calculation:**
    - **Default:** Prorated based on % of *Weighted* chores completed and APPROVED.
    - **Override:** Toggle for "All-or-Nothing" (100% completion required for any payout).
- **Weighting:** Chores have integer weights (default 1). "Core" chores can be weighted higher (e.g., 3x).
- **Basis:** Payout is calculated strictly on **Official Progress** (Approved completions). Pending reviews do NOT count toward payout if not approved by tally time.

### 4.2. Chore Lifecycle
1.  **Assignments:** Chores are defined as Recurring (Daily or Weekly).
2.  **Due Times:**
    - *Daily:* Due by end-of-day (reset at midnight).
    - *Weekly:* Due by Sunday Tally time.
3.  **Completion:**
    - Kid marks chore as "Done".
    - Status changes: `Pending Approval`.
    - Updates **Kid Progress** (visible to kid) but NOT **Official Progress**.
4.  **Review:**
    - Parent enters PIN to access Admin/Approval Queue.
    - Parent marks `Pending` items as `Approved` or `Rejected`.
    - `Approved`: Adds to **Official Progress**.
    - `Rejected`: Returns to `Incomplete` (Kid must redo).
5.  **Multi-Completion:** Some chores (e.g., "Walk Dog") can be done N times/period. Each completion counts separately.

### 4.3. Progress Tracking
- **Kid Progress:** (Approved Weight + Pending Weight) / Total Weight.
- **Official Progress:** (Approved Weight) / Total Weight.
- **Display:** Both values shown on Kid Dashboard to manage expectations.

### 4.4. Ledger & Balance
- **Model:** Double-entry style or simple transaction log.
- **Starting Balance:** Input manually when creating a child profile.
- **Transactions:**
    - `Allowance Credit`: Automated weekly deposit.
    - `Bonus Credit`: Manual entry by parent (with note).
    - `Penalty Debit`: (Out of scope for v0.1, but manual Debit allowed).
    - `Purchase Debit`: Parent records an item bought for the kid.
    - `Cash Out`: Parent gives physical cash; balance decreases.
- **History:** Immutable history of all financial events.

### 4.5. Editing & History
- **Rule Changes:** Changing allowance amount or chore variations applies *forward-only*. Past ledger entries remain fixed.
- **Retroactive Correction:** If a parent makes a mistake, they insert a manual adjustment transaction rather than editing the log history.

## 5. Screen Layouts (Resolution 1024x600)

### 5.1. Home Screen (Idle)
- **Layout:** Grid of "Kid Cards".
- **Content:** Kid Name, Avatar, Current Savings Balance (large text).
- **Action:** Tap card -> Enter Kid PIN (optional) -> Kid Dashboard.
- **Status Bar:** Clock, Network Status, "Admin" Lock Icon (Top Right).

### 5.2. Partent Admin (PIN Gated)
- **Access:** Tap Lock Icon -> Enter Parent PIN.
- **Tabs:**
    - **Approvals:** List of pending items -> Approve/Reject All or Individual.
    - **Ledger:** Select Kid -> Add Transaction ( Type: Bonus/Spend/CashOut, Amount, Note).
    - **Settings:** WiFi, Reboot, Update App, Backup/Restore.

### 5.3. Kid Dashboard
- **Header:** Name, Balance ($12.50), Official Progress bar (Green), Pending Ghost bar (Yellow).
- **Main Area (Split):**
    - **Left (Actions):** "I did a chore" button (Big).
    - **Right (Today's List):** Scrollable list of due chores.
        - Icon, Name, Status Checkbox.
        - Tap to mark Done.
- **Footer:** "Weekly Status" toggle to see full week view.

## 6. Technical Constraints & Data
- **Database:** SQLite (`/var/lib/chores_app/chores.db`).
- **Backend:** FastAPI (Python).
- **Frontend:** PySide6 (Qt) for Kiosk; HTML/JS for minimal mobile admin.
- **Updates:** `release-folder` strategy (symlink swap) with rollback capability.
- **Backup:** Export DB + config to USB drive as `.zip`.

## 7. Acceptance Criteria (v0.1)
- [ ] System boots to Kiosk UI automatically.
- [ ] Parent can add a child and set allowance $.
- [ ] Kid can mark a daily chore as done.
- [ ] Parent can approve that chore; Official Progress updates.
- [ ] At Sunday Tally time, Ledger verifies correct calculated payout credited.
- [ ] "Cash Out" transaction correctly reduces visible balance.
- [ ] Manual Reboot/Update available from secured Admin menu.
