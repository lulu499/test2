# Gate 010 — Fast-path orchestration pivot

## Decision

Native ChatGPT Work GitHub webhook tasks are documented as supported for eligible Plus users, but two independent Work sessions on this account exposed only time-scheduled automation controls. For this experiment, native Work webhook triggering is therefore treated as unavailable in practice and is no longer a dependency.

## Final UX requirement

The product-owner experience remains:

1. The user discusses and approves a project plan with ChatGPT.
2. ChatGPT dispatches bounded implementation work to Cursor automatically.
3. Cursor implements and reports evidence.
4. An immediate event path wakes an orchestration brain without hourly polling.
5. The orchestration brain independently reviews diff/tests/CI.
6. Mechanical failures are corrected automatically.
7. Safe dependent tasks continue automatically.
8. The user is interrupted only for material product/architecture/security/destructive/financial decisions.

The user must not copy prompts between ChatGPT and Cursor during normal operation.

## Architecture pivot

Normal fast path:

ChatGPT-approved plan -> durable task state -> Cursor -> GitHub commit/PR/CI event -> external event relay -> OpenAI orchestration response -> next bounded Cursor task or HUMAN_REQUIRED

Recovery path:

Low-frequency ChatGPT Work monitor -> reconcile durable repository state -> notify user only when useful.

## Why an external relay

The relay removes two unstable product dependencies discovered in Gates 005-010:

- hourly polling latency;
- unreliable unattended GitHub writes from dormant Work;
- unavailable native Work webhook-trigger creation despite current documentation.

## Safety boundary

The relay must not merge, deploy, spend money, expose credentials, or perform destructive operations without explicit approval. Repository/task state remains the durable source of truth. Cursor self-reports are evidence only and must be checked independently.

## Implementation phases

- 010B: define the event envelope and deterministic orchestration state transition contract; no credentials or external calls.
- 010C: implement an inert GitHub-event relay adapter and tests; external network calls mocked.
- 010D: connect an OpenAI Responses API orchestration worker after explicit approval for API credentials/billing.
- 010E: connect Cursor Cloud Agent API after explicit approval for Cursor credentials.
- 010F: prove end-to-end immediate automatic correction/continuation with hourly Work retained only as recovery.
