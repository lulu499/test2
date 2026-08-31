# Gate 005A.3 — Work persistence test

Use this prompt **inside one ChatGPT Work conversation** and keep that conversation open/identifiable for the duration of the test.

> Create an event-triggered task for the connected GitHub repository `lulu499/test2`.
>
> Trigger only on a **new pull-request comment** on PR #1 whose body is exactly:
>
> `GATE005A3_TRIGGER WORK-PERSIST-005A3-20260829`
>
> When that exact event occurs, do not modify GitHub, do not contact Cursor, do not merge, and do not perform any other external action. Respond only with:
>
> `GATE005A3_WORK_RETURN WORK-PERSIST-005A3-20260829`
>
> This is a persistence experiment. The important requirement is that the triggered result should be observable in this exact Work conversation if the product supports that behavior. Do not create additional work beyond this probe.

## Orchestrator procedure after the task is armed

1. Product owner tells the existing orchestration chat: `armed`.
2. Orchestrator posts exactly one non-@cursor comment to PR #1:
   `GATE005A3_TRIGGER WORK-PERSIST-005A3-20260829`
3. Product owner observes where the triggered ChatGPT result appears.
4. Classification:
   - `PASS_SAME_WORK_THREAD` — exact result appears in the same Work conversation.
   - `PARTIAL_SEPARATE_TASK_THREAD` — trigger fires but result appears in a separate task-associated conversation.
   - `FAIL_TRIGGER` — no triggered result occurs.
5. No code changes, Cursor dispatch, merge, deployment, or production action are permitted.
