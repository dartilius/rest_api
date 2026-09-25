# Repository Guidelines

## Project Structure & Module Organization

This is a Django REST API. `rmc_rest_api/` holds project settings, URL routing, ASGI/WSGI entry points, Celery configuration, and database routing. Domain apps such as `nomenclatures/`, `orders/`, `users/`, `files/`, and `placement_order/` contain models, serializers, views, URLs, admin registrations, filters, tasks, and migrations. Put cross-cutting API utilities in `api/`; external-service integrations belong in `services/`. API documentation templates live in `templates/`. Tests are centralized in `tests/`, with shared pytest fixtures in `tests/fixtures/`.

## Build, Test, and Development Commands

Install the pinned dependencies used by the Docker image:

```powershell
python -m pip install -r updated_req.txt
python manage.py migrate
python manage.py runserver
```

Run all tests with `pytest`; run a focused file with `pytest tests/test_orders.py`. Django reads configuration from environment variables (including PostgreSQL, MinIO, Redis/Celery, and `SECRET_KEY`); set these before running commands that initialize the application. Build the production container with `docker build -t rmc-rest-api .`.

## Coding Style & Naming Conventions

Use Python with four-space indentation and follow the style already used in the affected app. Use `snake_case` for modules, functions, variables, and model fields; use `PascalCase` for Django models, serializers, and test classes. Keep endpoint wiring in each app's `urls.py`, and create migrations through `python manage.py makemigrations <app>` rather than hand-writing them. Run `flake8` and `isort .` before submitting changes; both tools are listed in `updated_req.txt`.

## Testing Guidelines

The project uses pytest and pytest-django (`pytest.ini` sets `rmc_rest_api.settings` and limits discovery to `tests/`). Name files `test_<feature>.py`, classes `Test<Feature>`, and tests `test_<behavior>`. Mark database tests with `@pytest.mark.django_db`; reuse the clients and model fixtures registered in `tests/conftest.py`. Add regression coverage for each API, serializer, filter, or model behavior change. No coverage threshold is configured.

## Commit & Pull Request Guidelines

Recent commits favor Conventional Commit prefixes, especially `feat:`, `fix:`, and `refactor:`; use an imperative, specific summary (Russian descriptions are common in this history). Keep commits focused and include generated migrations with their model changes. Pull requests should explain the behavior change, list migration or configuration implications, link the relevant issue when available, and state the tests run. Include request/response examples or screenshots for user-visible API or documentation changes.

## Security & Configuration

Never commit secrets or live service credentials. Use environment variables for `SECRET_KEY`, database credentials, storage access keys, and external endpoints. Review permission and authentication changes carefully because REST framework defaults require JWT authentication.

# Backend agent instructions

## Django work

For every Django or Django REST Framework task, use the `django-pro` skill before editing, reviewing, or validating code. This includes models, migrations, ORM queries, serializers, views/viewsets, permissions, URLs, admin, signals, tasks, and settings.

## Verification

Use the repository virtual environment for backend checks:

```powershell
.\.venv\Scripts\python.exe backend\manage.py check
```

Run the narrowest relevant test suite after a change unless the user explicitly
asks not to run tests. Report any unavailable dependency or failed verification.

## Change scope

Preserve unrelated working-tree changes. Do not modify files outside the requested
backend scope without explicit user direction.
