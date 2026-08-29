# Gate 006 — Production Architecture Blueprint

## Objective

Define the production orchestration architecture using only capabilities already proven by Gates 001–005A.3. Gate 005B (immediate GitHub webhook wake-up) remains pending and is not required for this architecture.

## System roles

### ChatGPT Work — orchestration brain

ChatGPT Work owns:
- user intent and product decisions;
- decomposition into bounded engineering tasks;
- acceptance criteria and protected validation design;
- dispatch to Cursor;
- independent review of commits, diffs, tests, and CI;
- mechanical retry/correction;
- human escalation when required;
- durable orchestration state transitions;
- generation of the next safe task after a pass.

Work is the persistent human-facing conversation. The verified dormant wake mechanism is an hourly condition-watch poll. Immediate webhook wake-up is not assumed.

### GitHub — durable state and event bus

GitHub owns persistence between executions:
- task specifications;
- orchestration state;
- review records;
- implementation commits;
- PR discussion used for Cursor dispatch and agent reports;
- CI evidence.

No critical orchestration fact may exist only in conversational context. Anything required after a dormant interval must be recoverable from GitHub.

### Cursor Cloud Agent — bounded implementation worker

Cursor owns only implementation work explicitly delegated by ChatGPT. Cursor must:
- read the persisted task;
- obey allowed/protected paths;
- implement acceptance criteria;
- run requested tests;
- commit and push;
- report changed files, commands, tests, and unresolved issues.

Cursor does not own product decisions, final acceptance, merge authority, or task chaining.

### GitHub Actions — independent verifier

CI is independent evidence. Cursor self-reported test success is insufficient for PASS when CI is available.

## Core architecture

```text
User
  ↕
Persistent ChatGPT Work conversation
  ↕
GitHub durable orchestration state
  ↕                     ↘
Cursor Cloud Agent       GitHub Actions
  ↓                          ↓
implementation commit → independent verification
  ↘                          ↙
        ChatGPT review
             ↓
  PASS / AUTO-CORRECT / HUMAN_REQUIRED
             ↓
      next safe task or stop
```

## Operating modes

### 1. Active orchestration mode

Used while Work is actively executing.

Flow:
1. Read current state.
2. Generate one bounded task.
3. Persist task and protected validation.
4. Mark task active.
5. Dispatch Cursor by PR comment.
6. Observe Cursor result.
7. Inspect exact implementation commit and scope.
8. Inspect independent CI.
9. Decide PASS, AUTO_CORRECT, or HUMAN_REQUIRED.
10. Persist review and state before any next action.
11. On PASS, generate the next safe task without asking the user unless an escalation boundary is crossed.

### 2. Dormant monitoring mode

Used after no further immediate action is possible.

Verified mechanism: ChatGPT Work condition-watch, polling hourly.

Each poll must be idempotent:
1. Read state.json.
2. If there is no active task or actionable transition, do nothing and do not notify.
3. If active task already has a processed implementation commit, do nothing.
4. If a new Cursor result/commit exists, acquire it by commit SHA.
5. Verify scope and CI.
6. Persist a transition marker before dispatching any correction or next task.
7. Continue automatically when safe.
8. Notify the user only for HUMAN_REQUIRED, terminal completion, or explicitly requested milestones.

Expected dormant latency: up to one polling interval.

## Durable state model

`agent-lab/state.json` is the orchestration pointer, not the full history.

Required logical fields for production:

```json
{
  "experiment": "...",
  "status": "...",
  "active_task": "task-id-or-null",
  "active_attempt": 1,
  "last_passed_task": "...",
  "human_required": false,
  "last_processed_commit": "sha-or-null",
  "last_processed_event": "stable-id-or-null",
  "pending_action": "await-agent|await-ci|review|correct|next-task|human|null",
  "retry_count": 0,
  "max_auto_retries": 2,
  "monitor": {
    "mode": "work-condition-watch",
    "interval": "hourly"
  }
}
```

Full historical evidence belongs under `agent-lab/runs/` and `agent-lab/tasks/`.

## Task contract

Every implementation task must include:
- stable task id;
- objective;
- allowed paths;
- protected paths;
- acceptance criteria;
- verification commands;
- known product decisions it inherits;
- explicit human-escalation conditions;
- expected result envelope.

Tasks must be persisted before Cursor is contacted.

## Idempotency and duplicate prevention

Hourly polling makes duplicate handling mandatory.

Rules:
- commit SHA is the primary implementation identity;
- each commit is reviewed at most once per task attempt;
- each correction carries a new attempt number;
- each dispatch has a stable task/attempt marker in its PR comment;
- `last_processed_commit` is persisted before producing a downstream action;
- a next task is never generated twice for the same predecessor review;
- if state and GitHub disagree, stop automatic mutation and reconstruct from immutable task/review records.

## Automatic correction policy

Mechanical failures may be corrected automatically, including:
- syntax errors;
- lint/type/test failures;
- implementation that plainly misses an explicit acceptance criterion;
- accidental allowed-path implementation defects;
- deterministic CI failures with an unambiguous repair.

Maximum automatic correction attempts: 2 by default.

After the retry limit, escalate to the user unless the failure is infrastructure-only and a non-mutating retry is clearly safe.

## Human escalation policy

Stop and ask the user for:
- material product or UX ambiguity;
- incompatible interpretations that change intended behavior;
- major architecture changes not already approved;
- destructive data/infra operations;
- credentials, secrets, billing, or security-sensitive actions;
- production deployment or merge authority unless explicitly pre-authorized;
- scope expansion beyond the persisted task;
- repeated failure after the automatic retry limit;
- inconsistent or corrupted orchestration state.

A resolved human product decision becomes durable project state and must not be reopened for later mechanical failures.

## Verification policy

PASS requires all applicable checks:
1. Cursor changed only authorized paths.
2. Acceptance criteria are satisfied by direct diff/content inspection.
3. Protected tests were not changed by Cursor.
4. Independent CI succeeds.
5. No unrelated diff is present.
6. No human-escalation trigger is active.

Cursor saying "done" is never sufficient evidence.

## Merge and production policy

Default production safety:
- no automatic merge;
- no production deployment;
- no secret/credential mutation;
- no paid-resource creation;
- no destructive infrastructure actions.

These may be added later only as explicitly authorized capabilities with their own gates.

## Work monitor lifecycle

Because Gate 005A.3 observed the monitor in a paused state after successful detection, production must not assume perpetual re-arming.

Until continuous re-arming behavior is separately proven, use one of these safe strategies:
1. a recurring hourly condition watch that remains enabled by design; or
2. after every successful Work wake, explicitly verify that the monitor is still enabled and recreate/re-enable it if necessary.

Monitor maintenance itself must be idempotent: there should be only one active monitor for a given project/PR role.

## Gate 005B upgrade path

If native immediate GitHub event triggering becomes available later, replace only the wake transport:

```text
hourly condition-watch polling
            ↓
GitHub webhook/event trigger
```

The rest of the architecture — GitHub state, task contracts, Cursor boundaries, CI review, retry policy, and human escalation — remains unchanged.

## Production recommendation

Use **ChatGPT Work on web as the persistent brain**, **GitHub as the canonical durable state/event surface**, **Cursor Cloud Agent as the implementation worker**, and **GitHub Actions as independent verification**.

The architecture should be designed as an event-driven state machine even while the current Work wake mechanism is hourly polling. This keeps the system compatible with a future Gate 005B webhook upgrade without redesigning the orchestration protocol.
