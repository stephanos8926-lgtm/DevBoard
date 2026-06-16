# DevBoard Specification

## Overview

DevBoard is a file-based kanban task board designed for multi-agent coordination.
It uses Markdown files with YAML frontmatter as the task storage format, making
tasks human-readable, git-friendly, and easily parseable by both humans and AI agents.

## Design Principles

1. **File-based** — No database required. Tasks are files on disk.
2. **Git-friendly** — All data is plain text. Version control works naturally.
3. **Atomic operations** — Claims use atomic check-and-write to prevent races.
4. **Configurable** — Workflow states, WIP limits, and timeouts are configurable.
5. **Agent-first** — Designed for AI agents but works great for humans too.

## Architecture

```
┌─────────────────────────────────────────┐
│              CLI (click)                │
├─────────────────────────────────────────┤
│           DevBoard Manager              │
│  ┌─────────┬──────────┬──────────────┐  │
│  │  Task   │  Stats   │   Activity   │  │
│  │  CRUD   │  & Flow  │    Log       │  │
│  └─────────┴──────────┴──────────────┘  │
├─────────────────────────────────────────┤
│         YAML Frontmatter I/O            │
├─────────────────────────────────────────┤
│           File System (tasks/)          │
└─────────────────────────────────────────┘
```

## Data Model

### Task

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Auto | Sequential unique ID |
| title | string | Yes | Task name |
| status | string | Yes | Workflow state |
| priority | string | Yes | low/medium/high/critical |
| created | datetime | Auto | Creation timestamp |
| updated | datetime | Auto | Last modification timestamp |
| started | datetime | No | When work began |
| completed | datetime | No | When work finished |
| agent | string | No | Assigned agent name |
| claimed_by | string | No | Agent who claimed the task |
| claimed_at | datetime | No | When the claim was made |
| project | string | No | Project grouping |
| tags | list[string] | No | Filterable tags |
| depends_on | list[integer] | No | Task IDs that must be done first |
| cos | string | No | Class of service |
| due | datetime | No | Optional due date |
| body | string | No | Markdown description |

### Config

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| version | integer | 1 | Config schema version |
| board.name | string | "DevBoard" | Board display name |
| statuses | list[string] | ["backlog", "in-progress", "review", "done"] | Workflow states |
| priorities | list[string] | ["low", "medium", "high", "critical"] | Priority levels |
| wip_limits | map[string]int | {"in-progress": 3, "review": 2} | Max concurrent per status |
| claim_timeout | string | "1h" | Claim expiration duration |
| defaults.status | string | "backlog" | Default status for new tasks |
| defaults.priority | string | "medium" | Default priority for new tasks |

## Workflow

### Task Lifecycle

```
┌──────────┐    claim     ┌─────────────┐    submit    ┌────────┐
│ backlog  │ ───────────→ │ in-progress │ ──────────→ │ review │
└──────────┘              └─────────────┘             └────────┘
     ↑                           │                        │
     │         unblock           │    block               │ approve
     └───────────────────────────┤                        ↓
                                 │                   ┌───────┐
                                 └─────────────────→ │ done  │
                                                     └───────┘
```

### Claim Protocol

1. Agent calls `devboard pick --agent <name>` or `devboard claim <id> --agent <name>`
2. System checks: task is available, dependencies satisfied, WIP limit not exceeded
3. If all checks pass: task is claimed, `claimed_by` and `claimed_at` are set
4. Claim expires after `claim_timeout` (default 1 hour)
5. Only the claiming agent can complete the task

### Dependency Resolution

- Tasks with `depends_on` cannot be claimed until all dependencies are `done`
- When a task is completed, all tasks that depend on it are checked
- If all dependencies are now satisfied, blocked tasks are auto-unblocked

## File Format

### Task File

```markdown
---
id: 1
title: Example Task
status: backlog
priority: high
created: 2026-01-15T10:30:00+00:00
updated: 2026-01-15T10:30:00+00:00
project: myapp
tags:
  - feature
  - auth
depends_on: []
cos: standard
---

## Description
Task description in Markdown.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

### Filename Convention

Tasks are stored as `NNN-title-slug.md` in the `tasks/` directory:
- `NNN` is the zero-padded task ID
- `title-slug` is the lowercased, hyphenated title
- Example: `001-fix-login-bug.md`

## API Reference

See the source code in `src/devboard/__init__.py` for the full API reference.
Key classes:
- `Task` — Data model for a single task
- `DevBoard` — Board manager (CRUD, claims, stats, flow metrics)
- `BoardStats` — Board statistics
- `FlowStats` — Flow metrics (throughput, lead time, cycle time)
- `ActivityEvent` — Activity log entry
