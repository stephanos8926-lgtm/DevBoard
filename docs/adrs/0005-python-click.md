# ADR-0005: Python Package with Click CLI

## Status: Accepted

## Context

We needed a language and CLI framework that balances ease of development,
cross-platform compatibility, and rich terminal output.

## Decision

Build as a Python package using Click for the CLI and Rich for terminal output.

## Consequences

- **Pros**: Cross-platform, rich ecosystem, easy to install via pip
- **Cons**: Requires Python runtime (Go would produce a single binary)
- **Mitigation**: Python 3.10+ is widely available; pip install is simple

## Alternatives Considered

- **Go (like kanban-md)**: Single binary, but harder to extend and slower dev cycle
- **Rust**: Single binary, but steeper learning curve
- **Node.js**: Good ecosystem, but npm dependency management is less reliable
- **Shell scripts**: Not maintainable for this complexity level
