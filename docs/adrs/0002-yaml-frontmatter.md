# ADR-0002: YAML Frontmatter Task Format

## Status: Accepted

## Context

The initial design used plain text headers with sections (## AGENT, ## DEPENDENCIES, etc.).
This was fragile — parsing broke easily when users added or reordered sections.

## Decision

Switch to YAML frontmatter (between `---` delimiters) for structured metadata,
with a free-form Markdown body below.

## Consequences

- **Pros**: Structured, parseable, extensible, standard format
- **Cons**: Slightly more complex than plain text headers
- **Mitigation**: The `devboard add` command generates the frontmatter automatically

## Alternatives Considered

- **Plain text headers**: Too fragile, parsing breaks easily
- **JSON frontmatter**: Less human-readable than YAML
- **TOML frontmatter**: Less common, fewer tools support it
