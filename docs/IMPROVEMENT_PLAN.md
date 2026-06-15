# DevBoard Improvement Plan — Reference: kanban-md

## Source Reference
- **Repository**: https://github.com/antopolskiy/kanban-md (v0.33.0)
- **Language**: Go (single binary, zero runtime deps)
- **License**: MIT
- **Cloned to**: /tmp/kanban-md

## Architecture Comparison

| Aspect | kanban-md (reference) | DevBoard (current) |
|--------|----------------------|-------------------|
| **Task format** | YAML frontmatter + Markdown body | Plain text header + Markdown sections |
| **Config** | `config.yml` with statuses, priorities, WIP limits, claim_timeout, classes | None (hardcoded) |
| **Status model** | Configurable columns (backlog→todo→in-progress→review→done→archived) | Fixed 4-stage (AllPhases→InProgress→JobStart→JobEnd) |
| **Claim system** | `claimed_by` + `claimed_at` with configurable timeout | Agent field, no timestamp, no timeout |
| **Atomic pick** | `pick --claim` atomically finds, claims, and moves | `claim_task()` has TOCTOU race |
| **WIP limits** | Per-status WIP limits with enforcement | None |
| **Classes of service** | expedite, fixed-date, standard, intangible | None |
| **Dependencies** | `depends_on` with cycle detection and auto-unblock | Field exists but not enforced |
| **Parent/child** | `parent` field for subtasks | None |
| **Due dates** | `due` field with overdue detection | None |
| **Time tracking** | `started`, `completed` timestamps auto-set on status change | None |
| **Activity log** | `log` command with append-only event log | None |
| **Metrics** | Throughput, lead/cycle time, flow efficiency | Basic counts only |
| **TUI** | Full interactive TUI with bubbletea | None |
| **Agent skills** | Pre-written SKILL.md for kanban-based-development | None |
| **Output formats** | Table, JSON, `--compact` (70% fewer tokens) | Rich tables only |
| **Batch operations** | `edit 1,2,3 --priority high` | None |
| **Archive** | Soft-delete to `archived` status | Move to JobEnd |
| **Handoff** | `handoff` command with note + block + release | None |
| **Agent identity** | `agent-name` generates unique names | Manual assignment |
| **Self-healing** | Auto-detects duplicate IDs, filename/frontmatter mismatches | None |
| **Config migration** | Versioned config with auto-migration | None |

## Key Architectural Differences

### 1. Task File Format
**kanban-md** uses YAML frontmatter:
```markdown
---
id: 1
title: Set up CI pipeline
status: backlog
priority: high
created: 2026-02-07T10:30:00Z
updated: 2026-02-07T10:30:00Z
tags:
  - devops
---

Optional body with more detail.
```

**DevBoard** uses plain text header:
```
NA-0001
Fix TUI Word Wrapping
Bug-Fixes
HIGH

Description here...

## AGENT
Unassigned

## DEPENDENCIES
- (none)
```

**Recommendation**: Adopt YAML frontmatter. It's more structured, parseable, and extensible. The plain text format is fragile — section parsing breaks easily.

### 2. Config-Driven Statuses
**kanban-md** has a `config.yml` that defines:
- Status columns (ordered list with `require_claim` flag per status)
- Priority levels (ordered list)
- WIP limits per status
- Claim timeout duration
- Classes of service (expedite, fixed-date, standard, intangible)
- Default values for new tasks
- TUI display settings

**DevBoard** has no config — everything is hardcoded.

**Recommendation**: Add a `config.yml` with at minimum:
- Status columns (backlog, todo, in-progress, review, done)
- WIP limits per status
- Claim timeout
- Priority levels

### 3. Atomic Pick-and-Claim
**kanban-md**'s `pick --claim` is atomic — it finds, claims, and moves in one operation. Uses file locking to prevent TOCTOU races.

**DevBoard**'s `claim_task()` checks then acts — another agent can claim between check and act.

**Recommendation**: Implement atomic pick-and-claim using `os.rename()` as the concurrency primitive (like DropSite does). First agent to rename wins.

### 4. Claim Expiration
**kanban-md** has configurable `claim_timeout` (default 1h). Expired claims are treated as unclaimed.

**DevBoard** has no expiration — a crashed agent's claim stays forever.

**Recommendation**: Add `claimed_at` timestamp and configurable timeout. Auto-expire stale claims.

### 5. WIP Limits
**kanban-md** enforces per-status WIP limits. Moving a task to a full column is rejected.

**DevBoard** has no WIP limits.

**Recommendation**: Add WIP limits per status. Critical for preventing agent overload.

### 6. Classes of Service
**kanban-md** has 4 classes: expedite (bypasses WIP), fixed-date (sorted by due), standard, intangible.

**DevBoard** has no concept of classes.

**Recommendation**: Add classes of service. Expedite is critical for urgent bugs.

### 7. Dependency Enforcement
**kanban-md** checks `depends_on` in `pick` — only tasks with all deps in terminal status are pickable. Auto-unblocks when deps complete.

**DevBoard** has a `dependencies` field but it's never checked.

**Recommendation**: Enforce dependencies in `claim_task()`. Auto-unblock on completion.

### 8. Activity Log
**kanban-md** has an append-only event log tracking all mutations (create, move, edit, delete, block, unblock).

**DevBoard** has no audit trail.

**Recommendation**: Add activity log. Essential for debugging multi-agent issues.

### 9. Metrics
**kanban-md** computes throughput, lead time, cycle time, flow efficiency, aging work items.

**DevBoard** only has basic counts.

**Recommendation**: Add flow metrics. Useful for tracking improvement over time.

### 10. Agent Skills
**kanban-md** ships with a `kanban-based-development` SKILL.md that teaches agents the full workflow: pick → worktree → implement → test → merge → done.

**DevBoard** has no agent skills.

**Recommendation**: Write a SKILL.md for DevBoard. This is how agents learn to use the board.

## Recommended Improvements (Prioritized)

### P0 — Critical (fix before multi-agent use)
1. **Atomic claim** — Fix TOCTOU race in `claim_task()` using `os.rename()` or file locking
2. **Claim expiration** — Add `claimed_at` timestamp + configurable timeout
3. **Dependency enforcement** — Check deps before allowing claim, auto-unblock on completion
4. **YAML frontmatter** — Switch from plain text to YAML frontmatter for task files

### P1 — Important (add for production use)
5. **Config-driven statuses** — Add `config.yml` with statuses, priorities, WIP limits
6. **WIP limits** — Per-status limits with enforcement
7. **Activity log** — Append-only event log for all mutations
8. **Agent identity** — `devboard agent-name` command for unique agent names
9. **Batch operations** — Support `devboard edit NA-0001,NA-0002 --priority high`
10. **Archive** — Soft-delete to archived status instead of moving to JobEnd

### P2 — Nice-to-have (add for completeness)
11. **Classes of service** — expedite, fixed-date, standard, intangible
12. **Time tracking** — Auto-set `started`/`completed` timestamps
13. **Due dates** — Due date field with overdue detection
14. **Parent/child** — Subtask support
15. **Metrics** — Flow metrics (throughput, lead time, cycle time)
16. **Handoff** — `devboard handoff` command with note + block + release
17. **Compact output** — `--compact` flag for token-efficient agent output
18. **Agent skills** — SKILL.md teaching agents the DevBoard workflow
19. **TUI** — Interactive terminal board (long-term)
20. **Self-healing** — Auto-detect and fix duplicate IDs, filename mismatches
