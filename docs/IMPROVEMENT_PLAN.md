# DevBoard Improvement Plan

## Source Reference
- **Repository**: https://github.com/antopolskiy/kanban-md (v0.33.0)
- **Language**: Go (single binary, zero runtime deps)
- **License**: MIT

## Architecture Comparison

| Aspect | kanban-md (reference) | DevBoard (current) |
|--------|----------------------|-------------------|
| **Task format** | YAML frontmatter + Markdown body | YAML frontmatter + Markdown body |
| **Config** | `config.yml` with statuses, priorities, WIP limits, claim_timeout, classes | `config.yml` with same |
| **Status model** | Configurable columns | Configurable columns |
| **Claim system** | `claimed_by` + `claimed_at` with configurable timeout | Same |
| **Atomic pick** | `pick --claim` atomically finds, claims, and moves | Same (atomic check-and-write) |
| **WIP limits** | Per-status WIP limits with enforcement | Same |
| **Classes of service** | expedite, fixed-date, standard, intangible | Same |
| **Dependencies** | `depends_on` with cycle detection and auto-unblock | `depends_on` with auto-unblock |
| **Parent/child** | `parent` field for subtasks | Planned |
| **Due dates** | `due` field with overdue detection | Supported |
| **Time tracking** | `started`, `completed` timestamps auto-set | Same |
| **Activity log** | `log` command with append-only event log | Same (JSONL) |
| **Metrics** | Throughput, lead/cycle time, flow efficiency | Same |
| **TUI** | Full interactive TUI with bubbletea | Planned |
| **Agent skills** | Pre-written SKILL.md | See skills directory |
| **Output formats** | Table, JSON, `--compact` | Table, `--compact` |
| **Batch operations** | `edit 1,2,3 --priority high` | Planned |
| **Archive** | Soft-delete to `archived` status | Planned |
| **Handoff** | `handoff` command with note + block + release | Planned |
| **Agent identity** | `agent-name` generates unique names | Same |
| **Self-healing** | Auto-detect duplicate IDs, filename/frontmatter mismatches | Planned |
| **Config migration** | Versioned config with auto-migration | Planned |

## Remaining Improvements (Prioritized)

### P2 — Nice-to-have (add for completeness)
1. **Parent/child tasks** — Subtask support via `parent` field
2. **Batch operations** — `devboard edit 1,2,3 --priority high`
3. **Archive** — Soft-delete to `archived` status
4. **Handoff** — `devboard handoff` command with note + block + release
5. **TUI** — Interactive terminal board (long-term)
6. **Self-healing** — Auto-detect and fix duplicate IDs, filename mismatches
7. **Config migration** — Versioned config with auto-migration
8. **JSON output** — `--json` flag for machine-readable output
