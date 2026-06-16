# ADR-0003: Atomic Claims via Check-and-Write

## Status: Accepted

## Context

Multiple agents may try to claim the same task simultaneously. A naive
read-then-write approach creates a TOCTOU (Time of Check to Time of Use) race.

## Decision

Use atomic check-and-write: read the file, verify availability, write the
updated file. The write operation is atomic at the filesystem level.

## Consequences

- **Pros**: Prevents double-claiming without file locking
- **Cons**: Not truly atomic (read and write are separate operations)
- **Mitigation**: In practice, the window is small enough that collisions are
  extremely rare. For high-contention scenarios, file locking can be added later.

## Alternatives Considered

- **File locking (flock)**: More robust but adds complexity and platform differences
- **Database transactions**: Would require a database (rejected in ADR-0001)
- **Optimistic concurrency**: Would require version numbers in task files
