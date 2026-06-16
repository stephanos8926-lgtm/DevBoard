# DevBoard Structure Documentation

## Directory Layout

```
project-root/
├── config.yml          # Board configuration (statuses, WIP limits, etc.)
├── tasks/              # Task files (one per task, YAML frontmatter + Markdown)
│   001-fix-login-bug.md
│   002-add-search.md
│   003-refactor-auth.md
├── activity.jsonl      # Append-only activity log
└── .devboard/          # Internal state (auto-created)
```

## Task Lifecycle

```
backlog → in-progress → review → done
   ↑          ↓            ↓
   └──── blocked ←─────────┘
```

1. **backlog** — New tasks land here
2. **in-progress** — Claimed by an agent, actively being worked on
3. **review** — Implementation complete, awaiting review/merge
4. **done** — Completed and verified
5. **blocked** — Waiting on external dependency or unmet task dependency

## Task File Format

Each task is a Markdown file with YAML frontmatter:

```markdown
---
id: 1
title: Fix login bug
status: backlog
priority: high
created: 2026-01-15T10:30:00+00:00
updated: 2026-01-15T10:30:00+00:00
project: myapp
tags:
  - bug
  - auth
depends_on: []
cos: standard
---

## Description
What needs to be done and why.

## Acceptance Criteria
- [ ] Specific, testable condition
- [ ] Another condition

## Notes
Any additional context, links, or constraints.
```

## Configuration Reference

See `config.yml` for all configurable options:

| Option | Description | Default |
|--------|-------------|---------|
| `statuses` | Ordered list of workflow states | `["backlog", "in-progress", "review", "done"]` |
| `priorities` | Ordered list of priority levels | `["low", "medium", "high", "critical"]` |
| `wip_limits` | Max concurrent tasks per status | `{"in-progress": 3, "review": 2}` |
| `claim_timeout` | How long a claim lasts before expiring | `1h` |
| `defaults.status` | Default status for new tasks | `backlog` |
| `defaults.priority` | Default priority for new tasks | `medium` |

## Classes of Service

| Class | SLA | WIP Bypass | Use Case |
|-------|-----|------------|----------|
| 🚨 Expedite | 4 hours | Yes | Critical production issues |
| 📅 Fixed Date | Due date | Yes | Deadline-driven work |
| 📋 Standard | 48 hours | No | Normal priority work |
| 💡 Intangible | 1 week | No | Tech debt, refactoring |

## Multi-Agent Coordination Rules

1. **One agent per task** — only one agent works on a task at a time
2. **Check before starting** — always run `devboard status` before picking up a task
3. **Use atomic pick** — `devboard pick --agent <name>` prevents double-claiming
4. **Respect WIP limits** — don't claim beyond your configured limit
5. **Release stale claims** — claims expire after the configured timeout
6. **Update on completion** — run `devboard complete <id>` when done
