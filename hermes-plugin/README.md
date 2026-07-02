# DevBoard Hermes Plugin

The DevBoard Hermes plugin provides 8 tools + 2 hooks for integrating
DevBoard into your Hermes Agent sessions.

## Installation

```bash
cd path/to/DevBoard/hermes-plugin
./install.sh
```

Or manually:

```bash
mkdir -p ~/.hermes/plugins/rapidwebs-devboard
cp -r rapidwebs-devboard/* ~/.hermes/plugins/rapidwebs-devboard/
```

## Enable in config

Add to `~/.hermes/config.yaml` under `plugins: enabled:`:

```yaml
plugins:
  enabled:
    - rapidwebs-devboard
```

## Tools

| Tool | Description |
|------|-------------|
| `devboard_status` | Show board overview with counts per status |
| `devboard_pick` | Auto-pick a task from backlog |
| `devboard_claim` | Claim a specific task by ID |
| `devboard_complete` | Mark a task done |
| `devboard_add` | Add a new task |
| `devboard_show` | Show full task details |
| `devboard_move` | Move task between statuses |
| `devboard_log` | View activity log |
| `devboard_agent_name` | Generate a random agent name |

## Hooks

| Hook | Purpose |
|------|---------|
| `on_session_start` | Log board status at session start |
| `on_session_end` | Auto-update MASTER.SCHEDULE.md |
