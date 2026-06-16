# ADR-0004: Config-Driven Workflow

## Status: Accepted

## Context

Hardcoding workflow states (backlog, in-progress, review, done) makes the tool
inflexible for different teams with different processes.

## Decision

Use a `config.yml` file to define statuses, priorities, WIP limits, claim timeout,
and defaults. The board root is the directory containing `config.yml`.

## Consequences

- **Pros**: Flexible, teams can customize their workflow
- **Cons**: More complex than hardcoded values
- **Mitigation**: Sensible defaults are provided; most teams won't need to customize

## Alternatives Considered

- **Hardcoded values**: Too inflexible
- **CLI flags per command**: Would require repeating flags everywhere
- **Environment variables**: Less discoverable than a config file
