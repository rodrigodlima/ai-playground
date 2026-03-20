# Benchmark Project

## Overview

This project serves as a controlled environment for measuring token consumption
in Claude Code across different operating systems and file encodings. All content
in this file is intentionally neutral and serves no functional purpose beyond
token measurement.

## Project Structure

```
benchmark/
├── src/
│   ├── main.py
│   ├── utils.py
│   └── config.py
├── tests/
│   ├── test_main.py
│   └── test_utils.py
├── docs/
│   └── README.md
└── requirements.txt
```

## Development Guidelines

### Code Style

- Follow PEP 8 for Python files
- Maximum line length: 88 characters
- Use type hints on all public functions and methods
- Write docstrings in Google format for all public APIs

### Naming Conventions

- Variables and functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Version Control

- Commit messages follow Conventional Commits specification
- Branch names use format: `type/short-description`
- Pull requests require at least one approval before merging
- Squash commits when merging to main branch

## Configuration

Environment variables used by this project:

| Variable           | Type    | Default       | Description              |
|--------------------|---------|---------------|--------------------------|
| `APP_ENV`          | string  | `development` | Runtime environment      |
| `LOG_LEVEL`        | string  | `INFO`        | Logging verbosity        |
| `MAX_RETRIES`      | integer | `3`           | Maximum retry attempts   |
| `TIMEOUT_SECONDS`  | integer | `30`          | Request timeout          |

## Sample Code

```python
from typing import Optional


def process_item(
    item_id: str,
    retries: int = 3,
    timeout: Optional[float] = None,
) -> dict:
    """Process a single item by ID.

    Args:
        item_id: Unique identifier for the item to process.
        retries: Number of retry attempts on failure.
        timeout: Optional timeout in seconds.

    Returns:
        Dictionary containing processing result and metadata.

    Raises:
        ValueError: If item_id is empty or None.
        TimeoutError: If processing exceeds the timeout.
    """
    if not item_id:
        raise ValueError("item_id cannot be empty")

    result = {
        "id": item_id,
        "status": "processed",
        "retries_used": 0,
    }
    return result
```

## Testing

Run the full test suite:

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

Run a specific test file:

```bash
pytest tests/test_main.py -v
```

## Constraints and Rules

1. This file must not contain any real credentials or secrets
2. All examples use placeholder values only
3. The content length is fixed to maintain measurement consistency
4. Line endings and encoding are the primary variables under test
5. No external dependencies should be introduced during testing
6. Results must be reproducible across multiple test runs
7. Each test run starts a fresh Claude Code session
8. Token counts are captured immediately after session completion
