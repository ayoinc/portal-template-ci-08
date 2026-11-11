# sample-python-api

The sample team's "items" API: stores, caches and serves items

## Overview

| Setting        | Value |
| -------------- | ----- |
| Service        | `sample-python-api` |
| Owner          | `group:default/platform-team` |
| Framework      | FastAPI, Python 3.12 (see `.python-version`) |
| Port           | `8000` |
| Storage        | PostgreSQL through SQLAlchemy 2 (async), Alembic migrations |
| Cache          | Redis when `REDIS_URL` is set, otherwise in memory |
| Authentication | JWT bearer tokens |
| Repository     | <https://github.com/example-org/sample-python-api> |

```d2
direction: right

client: Client {
  shape: oval
}

service: sample-python-api {
  health: "/health\n/health/ready"
  items: "/api/v1/items"
  auth: "/api/v1/auth/token"
  repository: "ItemRepository"
  items -> repository
}

database: PostgreSQL {
  shape: cylinder
}

cache: Redis {
  shape: cylinder
}

client -> service.items: HTTP 8000
client -> service.health
client -> service.auth: user name, password
service.repository -> database
service.health -> database: ready
service.repository -> cache: item reads
```

## Project structure

```
sample-python-api/
├── .github/workflows/
│   ├── ci.yaml               # Tests, image build and smoke test, dependency scan
│   ├── lint.yaml             # Ruff lint and format check
│   ├── typecheck.yaml        # mypy in strict mode
│   └── compose.yaml          # Starts the Compose stack and calls the API
├── docs/index.md             # This page
├── migrations/
│   ├── env.py                # Alembic environment (async engine)
│   └── versions/             # One file per migration
├── alembic.ini
├── scripts/smoke.sh          # Creates, reads and deletes an item on a running service
├── src/app/
│   ├── main.py               # create_app() and the ASGI application
│   ├── config.py             # Settings read from the environment
│   ├── dependencies.py       # Dependencies shared by the routes
│   ├── schemas.py            # Request and response models
│   ├── repository.py         # ItemRepository interface
│   ├── db.py                 # SQLAlchemy model, connection pool, SQL repository
│   ├── cache.py              # Cache interface, Redis and in-memory caches, cached repository
│   ├── security.py           # JWT bearer tokens
│   ├── rate_limit.py         # Rate limiting middleware
│   ├── security_headers.py   # Security headers middleware
│   ├── log.py                # JSON logging and request logging middleware
│   ├── metrics.py            # Prometheus metrics
│   └── api/
│       ├── auth.py           # /api/v1/auth/token
│       ├── health.py         # /health, /health/ready
│       └── items.py          # /api/v1/items
├── tests/                    # pytest tests of every module
├── .env.example
├── .python-version
├── Dockerfile
├── docker-compose.yaml
├── catalog-info.yaml
├── mkdocs.yml
└── pyproject.toml            # Dependencies and tool configuration
```

## Running locally

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
```

`docker compose up --build --wait` builds the image and starts the service, PostgreSQL and Redis; the service container applies the migrations before it starts.
`bash scripts/smoke.sh` then creates, reads and deletes an item through the API.

## Endpoints

| Method | Path                 | Description                                   |
| ------ | -------------------- | --------------------------------------------- |
| GET    | `/health`            | Liveness: the process is running              |
| GET    | `/health/ready`      | Readiness: checks the database and the cache, 503 on failure |
| POST   | `/api/v1/auth/token` | Exchange user name and password for a token   |
| GET    | `/api/v1/items`      | List items (`skip`, `limit`)                  |
| POST   | `/api/v1/items`      | Create an item                                |
| GET    | `/api/v1/items/{id}` | Read an item                                  |
| PUT    | `/api/v1/items/{id}` | Replace an item                               |
| DELETE | `/api/v1/items/{id}` | Delete an item                                |
| GET    | `/metrics`           | Prometheus metrics                            |
| GET    | `/docs`, `/redoc`    | Swagger UI and ReDoc                          |
| GET    | `/openapi.json`      | OpenAPI document                              |

## Authentication

The items routes require a bearer token. `POST /api/v1/auth/token` issues one for the
user configured with `AUTH_USERNAME` and `AUTH_PASSWORD`; it is signed with `JWT_SECRET`
(HS256) and expires after `JWT_EXPIRE_MINUTES`.

```bash
token="$(curl -s -d 'username=admin' -d 'password=change-me' \
  http://localhost:8000/api/v1/auth/token | python3 -c 'import json, sys; print(json.load(sys.stdin)["access_token"])')"
curl -H "Authorization: Bearer $token" http://localhost:8000/api/v1/items
```

## Database

Items are stored in PostgreSQL through SQLAlchemy 2 (async). The service connects on the first
query, so it starts without a reachable database; `/health/ready` reports whether the
database answers.

The schema is managed with Alembic migrations in `migrations/versions/`:

```bash
alembic upgrade head                              # apply all migrations
alembic revision --autogenerate -m "add a column" # create one after changing app/db.py
alembic downgrade -1                              # undo the last one
```

The tests run on an in-memory SQLite database and need no database server.

## Cache

Single items are read cache-aside (`CachedItemRepository` in `app/cache.py`): a read asks
the cache first and stores the item on a miss for `CACHE_TTL_SECONDS`; replacing or
deleting an item removes its entry. Lists are not cached. With `REDIS_URL` the cache is
Redis and `/health/ready` checks that it answers; without it each process caches in its
own memory.

## Configuration

Settings are environment variables, read by `src/app/config.py`. Copy `.env.example` to
`.env` to change them locally.

| Variable             | Default                      | Purpose                                             |
| -------------------- | ---------------------------- | --------------------------------------------------- |
| `APP_ENV`            | `development`                | `development`, `staging` or `production`            |
| `LOG_LEVEL`          | `INFO`                       | Lowest level that is logged                         |
| `DATABASE_URL`       | `postgresql+asyncpg://app:app@localhost:5432/app` | SQLAlchemy URL of the database |
| `REDIS_URL`          | not set                      | Redis used as cache; unset means an in-memory cache |
| `CACHE_TTL_SECONDS`  | `60`                         | How long a cached item is served                    |
| `AUTH_USERNAME`      | `admin`                      | User allowed to call the items API                  |
| `AUTH_PASSWORD`      | `change-me`                  | Password of that user                               |
| `JWT_SECRET`         | a development value          | Key that signs the tokens (HS256)                   |
| `JWT_EXPIRE_MINUTES` | `30`                         | Lifetime of a token                                 |
| `RATE_LIMIT`         | `100/minute`                 | Requests allowed per client address                 |
| `CORS_ORIGINS`       | `["http://localhost:3000"]`  | JSON list of allowed browser origins                |

With `APP_ENV=production` the service refuses to start while a setting marked in
`DEVELOPMENT_ONLY_DEFAULTS` (`src/app/config.py`) still has its development default.

## Middleware

- **Rate limiting**: every client address may send `RATE_LIMIT` requests; further requests
  get 429 with a `Retry-After` header. `/health` and `/health/ready` are exempt. Counters
  are kept per process.
- **CORS**: browsers on an origin listed in `CORS_ORIGINS` may call the API.
- **Security headers**: every response carries `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`,
  `Permissions-Policy` and `Strict-Transport-Security`.
- **Logging**: every request is logged as one JSON object (method, path, status code,
  duration) with structlog. `structlog.get_logger()` logs in the same format.
- **Metrics**: `/metrics` serves request counts and durations in the Prometheus format.

## Container image

The `Dockerfile` builds a `python:3.12-slim` image that runs as an unprivileged user and
listens on port 8000. The container starts without configuration; run `alembic upgrade head` in it once the database is reachable.

## Pipeline

Every push and pull request to `main` runs these workflows; none needs a secret or a
variable.

| Workflow | What it does |
| -------- | ------------ |
| `ci.yaml` | Installs the project on the Python version of `.python-version`, runs `pytest` with a 90 percent coverage threshold and starts the server; lints the `Dockerfile` with Hadolint, builds the image, starts the container and calls `/health`, reports image vulnerabilities with Trivy and, on a push, publishes the image to `ghcr.io/example-org/sample-python-api`; reports vulnerable dependencies with Trivy |
| `lint.yaml` | `ruff check .` and `ruff format --check .` |
| `typecheck.yaml` | `mypy` in strict mode on sources and tests |
| `compose.yaml` | `docker compose up --build --wait`, calls `/health/ready` and runs `scripts/smoke.sh` |

The Trivy reports list findings without failing the build, because the advisory database
changes daily.

## Owner

group:default/platform-team
