---
name: backend-agent
description: use for all backend tasks
model: opus
color: green
---

System Instruction

Purpose

- Define a consistent, concise setup and working agreement for our backend (Python/FastAPI) and frontend codebases.
- Provide clear folder structures, technology choices, and conventions for contributors and coding agents.

Backend

- Stack
    - Python 3.12
    - pip for environment and dependency management
    - FastAPI for the ASGI application and API endpoints
    - PostgreSQL as the database
    - Pytest for testing; Ruff + Black + isort for linting/formatting

- Project structure
    - backend/
        - app/
            - main.py
            - core/
                - config.py
                - logging.py
            - api/
                - v1/
                    - health.py
                    - feature_one.py
            - models/
                - pydantic_types.py
            - services/
                - feature_one.py
        - db/
            - prisma/
                - schema.prisma
        - tests/
            - test_feature_one.py
            - test_health.py

- Conventions
    - Favor functional programming. Keep services as pure functions. Avoid classes unless strictly necessary.
    - Use snake_case for Python modules and directories. Filenames are lowercase.
    - Place request/response Pydantic models in `app/models`. Keep domain types separate from transport shapes when helpful.
    - Group API routes by feature under `app/api/v1`. Expose them under the `/api/v1` prefix.
    - Centralize configuration in `app/core/config.py` (reads from `.env`, e.g., `DATABASE_URL`).
    - Use standard `logging` configured in `app/core/logging.py`.
    - Add tests in `tests/` for each new service and route.
