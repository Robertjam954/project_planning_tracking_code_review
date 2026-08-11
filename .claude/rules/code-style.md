---
paths:
  - "agents/**/*.py"
  - "scripts/**/*.py"
  - "tests/**/*.py"
---

# Code style rules

- Prose and comments: single hyphen (-), never em dashes. No emojis.
- Type hints on every function signature. `from __future__ import annotations` at top.
- Format with `ruff` (a PostToolUse hook runs `ruff format` on save). Lint clean before commit.
- Naming: `snake_case` files/functions, `PascalCase` classes, `UPPER_SNAKE_CASE` constants.
- Imports grouped stdlib -> third-party -> local, matching the surrounding files.
- Docstrings: one line for simple functions, multi-line for complex logic; explain **why**, not what.
- Keep tools as thin `@tool` wrappers over the existing scripts - scripts stay the source of truth.
- Config is import-safe: reading `agents/config.py` must not require the LLM SDKs.
