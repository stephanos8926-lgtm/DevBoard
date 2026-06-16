# ADR-0001: File-Based Task Storage

## Status: Accepted

## Context

We needed a task storage format that works for both humans and AI agents,
supports version control, and requires no external dependencies (no database).

## Decision

Store tasks as Markdown files with YAML frontmatter in a `tasks/` directory.

## Consequences

- **Pros**: Human-readable, git-friendly, no database, works offline, easy to backup
- **Cons**: No built-in querying (must scan files), potential for file system races
- **Mitigation**: Atomic claim operations via check-and-write pattern

## Alternatives Considered

- **SQLite**: Requires a database file, harder to diff/merge in git
- **JSON files**: Less human-readable than Markdown
- **Database (Postgres/Redis)**: External dependency, overkill for task tracking
