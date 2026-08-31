# ChatGPT ↔ Coding Agent Lab

This directory is an isolated experiment for a supervised coding-agent workflow.

## Objective

Validate this loop:

1. ChatGPT defines a structured task.
2. A coding agent implements it on an isolated branch.
3. GitHub produces independent evidence through CI and diffs.
4. ChatGPT reviews the evidence instead of trusting the agent's self-report.
5. ChatGPT either continues automatically or escalates a real decision to the user.

## Safety rules

- Do not modify files outside `agent-lab/` unless the task explicitly says so.
- Do not merge automatically.
- Do not push secrets or credentials.
- A task is not complete just because an agent says it is complete; CI and diff review are required.

## Baseline application

`app.py` exposes a tiny pure function. The application is intentionally trivial because the orchestration behavior—not the product—is the experiment.
