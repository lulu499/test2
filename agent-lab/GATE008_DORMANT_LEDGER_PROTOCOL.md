# Gate 008 — Dormant Transition Ledger Protocol

## Reason for the adjustment

Gate 008B demonstrated that the persistent Work monitor can read GitHub, inspect a Cursor implementation, and reason about the orchestration state, but an unattended overwrite of `agent-lab/state.json` was rejected as too risky under the current ChatGPT app permission mode.

Gate 008B-R2 then proved that the same background Work monitor can successfully perform a dedicated low-risk GitHub file update.

Therefore dormant orchestration uses append/dedicated transition ledgers instead of directly rewriting the authoritative state projection.

## Roles

- `agent-lab/state.json`: compacted orchestration projection maintained/reconciled by the active orchestrator.
- `agent-lab/transitions/<task>-attempt-<n>.json`: per-attempt durable evidence that dormant Work may update.
- `agent-lab/runs/*.review.json`: immutable review evidence after a terminal result is reconciled.

## Dormant Work rules

1. Read `state.json` and the task contract.
2. Read the per-attempt transition ledger.
3. If the ledger is already terminal, do nothing.
4. Discover a candidate Cursor implementation from GitHub.
5. Inspect exact changed paths and independent CI.
6. Perform the review.
7. Persist the outcome only to that attempt's transition ledger.
8. Do not overwrite `state.json` from dormant Work.
9. Do not process an implementation SHA already recorded in the ledger.
10. Notify the user only for terminal PASS or HUMAN_REQUIRED.

## Reconciliation

When the active orchestrator resumes, it reads any terminal transition ledger and deterministically compacts it into `state.json`, then creates the canonical review record. Reconciliation must be idempotent: a ledger already reflected in `state.json` is ignored.

## Gate 008B-R3 success condition

The persistent Work monitor must, without `Run now` and without modifying `state.json`:

- discover Cursor commit `9c142ce57bc520438da4c0bc56ac4fd0dc656179` for Gate 008B;
- verify only `agent-lab/gate008b_fixture.py` changed;
- verify the exact fixture contract;
- verify independent CI run `33296594447` succeeded;
- update only `agent-lab/transitions/gate-008b-attempt-1.json` to a terminal PASS record;
- return `GATE008B_R3_LEDGER_PASS` in the same Work conversation.
