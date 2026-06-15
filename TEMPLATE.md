# TASK FILE TEMPLATE

```
[TASK_ID]
[TASK_NAME]
[PHASE]
[PRIORITY]

[DESCRIPTION OF WHAT THIS TASK WILL DO]

## AGENT
[Agent name or "Unassigned"]

## DEPENDENCIES
- [TASK_ID] [TASK_NAME] (must be completed first)

## PROJECT
[Project name or path, e.g., "NexusAgent", "ast-tools"]

## FILES TO MODIFY
- (list files this task will modify)

## FILES TO CREATE
- (list files that will be created)

## ACCEPTANCE CRITERIA
- [ ] (checkable condition 1)
- [ ] (checkable condition 2)

## NOTES
(additional context, constraints, or links)
```

## Field Descriptions

| Field | Description |
|-------|-------------|
| `TASK_ID` | Unique ID (e.g., `NA-0042` for NexusAgent task 42, `AT-0007` for ast-tools task 7) |
| `TASK_NAME` | Short, descriptive name |
| `PHASE` | Project phase or milestone (e.g., `Refactoring`, `Feature Work`, `Bug Fixes`) |
| `PRIORITY` | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `AGENT` | Name of the agent or developer working on this task |
| `DEPENDENCIES` | List of task IDs that must be completed before this one |
| `PROJECT` | Which project this task belongs to |
| `FILES TO MODIFY` | Existing files that will be changed |
| `FILES TO CREATE` | New files that will be created |
| `ACCEPTANCE CRITERIA` | Checkable list of conditions for completion |
| `NOTES` | Any additional context |

## Task ID Convention
- Format: `XX-NNNN` where `XX` is the project abbreviation and `NNNN` is a sequential number
- Project abbreviations: `NA` = NexusAgent, `AT` = ast-tools, `HB` = Hermes, `DB` = DevBoard, `FORGE` = FORGE, `CAT` = CATALYST
- Keep a running counter per project in `MASTER.SCHEDULE.md`
