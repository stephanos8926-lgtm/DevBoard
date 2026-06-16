# DevBoard — Multi-Agent Shared Task Board

A file-based kanban system for coordinating work across multiple AI agents and human developers.

## Quick Start

```bash
# Install
pip install devboard

# Initialize a new board in your project
cd /path/to/your/project
devboard init

# Add a task
devboard add "Fix login bug" --priority high --project myapp

# Pick and claim a task
devboard pick --agent my-name

# Complete a task
devboard complete 1 --agent my-name

# View board status
devboard status
```

## Features

- **YAML frontmatter tasks** — Structured, parseable, extensible
- **Atomic claims** — TOCTOU-safe check-and-write prevents double-claiming
- **Claim expiration** — Configurable timeout (default 1h) for crashed agents
- **Dependency enforcement** — Can't claim tasks with unmet dependencies; auto-unblock on completion
- **WIP limits** — Per-status limits prevent agent overload
- **Classes of service** — Expedite (bypasses WIP), fixed-date, standard, intangible
- **Flow metrics** — Throughput, lead time, cycle time, Little's Law, SLA compliance
- **Activity log** — Append-only JSONL audit trail
- **Agent identity** — Random two-word names (e.g., "swift-river")
- **Hermes plugin** — 8 tools + 2 hooks for AI agent integration

## Task File Format

Tasks are Markdown files with YAML frontmatter:

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
---

## Description
Users can't log in when using SSO.

## Acceptance Criteria
- [ ] SSO login works with Google
- [ ] SSO login works with GitHub
- [ ] Tests pass
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `devboard init [path]` | Initialize a new DevBoard |
| `devboard status` | Show board status |
| `devboard add <title>` | Add a new task |
| `devboard list` | List tasks with filtering |
| `devboard show <id>` | Show task details |
| `devboard pick --agent <name>` | Pick and claim next available task |
| `devboard claim <id> --agent <name>` | Claim a specific task |
| `devboard complete <id> --agent <name>` | Complete a task |
| `devboard move <id> <status>` | Move task to new status |
| `devboard log` | Show activity log |
| `devboard board` | Show board summary with WIP utilization |
| `devboard agent-name` | Generate a random agent name |

## Configuration

DevBoard uses a `config.yml` in the board root:

```yaml
version: 1
board:
  name: My Project Board
statuses:
  - backlog
  - in-progress
  - review
  - done
priorities:
  - low
  - medium
  - high
  - critical
wip_limits:
  in-progress: 3
  review: 2
claim_timeout: 1h
defaults:
  status: backlog
  priority: medium
next_id: 1
```

## Multi-Agent Coordination

When multiple agents share a DevBoard:

1. **Always check** `devboard status` before starting work
2. **Use `devboard pick`** to atomically find and claim a task
3. **Respect WIP limits** — don't claim beyond your limit
4. **Complete or release** tasks when done (don't leave stale claims)
5. **Claims expire** after the configured timeout

## License

MIT License — see [LICENSE](LICENSE) for details.
