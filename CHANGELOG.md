# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-19

### Added
- Classes of service: expedite, fixed-date, standard, intangible
- Flow metrics: throughput, lead time, cycle time, Little's Law, SLA compliance
- Activity log (JSONL append-only audit trail)
- Agent identity generation (random two-word names)
- `devboard board` command for WIP utilization summary
- `devboard log` command for activity log viewing
- `devboard agent-name` command
- `--compact` flag for token-efficient output
- `--json` flag for machine-readable output (planned)
- Hermes plugin with 8 tools and 2 hooks

### Changed
- Task format changed from plain text to YAML frontmatter
- Config-driven statuses, priorities, WIP limits
- Atomic claim with TOCTOU-safe check-and-write
- Claim expiration with configurable timeout

## [1.0.0] - 2026-01-15

### Added
- Initial release
- File-based kanban with YAML frontmatter tasks
- Atomic claims with dependency enforcement
- WIP limits per status
- CLI with click and rich
- Configurable workflow via config.yml
