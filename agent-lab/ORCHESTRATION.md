# Orchestration Contract

## Roles

### ChatGPT orchestrator
- Owns product intent, task definition, acceptance criteria, review, and escalation.
- Must inspect repository evidence before declaring a task complete.
- May generate a correction task when implementation evidence fails acceptance criteria.

### Coding agent
- Owns implementation inside the task scope.
- Must not change files outside the allowed paths.
- Must report commands run, tests run, and unresolved uncertainty.

## Completion rule

A task may be marked PASS only when all of the following are true:

1. The changed files are inside the allowed scope.
2. The implementation satisfies every acceptance criterion.
3. Independent CI or verification passes.
4. The diff contains no unrelated changes.
5. No human-decision trigger is present.

## Human-decision triggers

Escalate instead of continuing automatically when a task requires:

- a material product or UX choice;
- a breaking architecture change not authorized in the task;
- destructive data or infrastructure operations;
- secrets, credentials, billing, or production deployment;
- changes outside the allowed repository scope;
- repeated failure after two correction attempts;
- ambiguity that changes intended behavior.

## Agent result envelope

Each implementation should be summarized using:

```json
{
  "task_id": "gate-001",
  "status": "implemented|blocked|needs-human",
  "summary": "...",
  "files_changed": ["..."],
  "commands_run": ["..."],
  "tests_run": ["..."],
  "known_issues": ["..."]
}
```
