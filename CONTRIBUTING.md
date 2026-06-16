# Contributing to DevBoard

Thank you for your interest in contributing! This document outlines how to participate.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/DevBoard.git`
3. Create a virtual environment: `python3 -m venv .venv && source .venv/bin/activate`
4. Install dependencies: `pip install -e ".[dev]"`
5. Run tests: `pytest`

## Development Workflow

1. Create a branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `pytest`
4. Run linter: `ruff check src/ tests/`
5. Commit with a descriptive message
6. Push and open a Pull Request

## Code Style

- Python 3.10+ type hints required
- Google-style docstrings
- Line length: 100 characters
- Use `ruff` for linting and formatting

## Testing

- All new features must include tests
- Run the full suite: `pytest`
- Maintain or improve code coverage

## Reporting Issues

- Use the [GitHub Issues](https://github.com/stephanos8926-lgtm/DevBoard/issues) page
- Include steps to reproduce, expected behavior, and actual behavior
- Include your Python version and OS

## Pull Request Guidelines

- One feature or fix per PR
- Include tests for new functionality
- Update documentation if needed
- Keep commits focused and descriptive

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code.
