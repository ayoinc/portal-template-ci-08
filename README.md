# sample-python-api

The sample team's "items" API: stores, caches and serves items

FastAPI service on Python 3.12 with an `items` sample resource stored in PostgreSQL, protected by JWT bearer tokens.

## Getting started

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
```

The API listens on <http://localhost:8000>. Swagger UI is on <http://localhost:8000/docs>.

The default `DATABASE_URL` expects PostgreSQL on localhost with user, password and database `app`. `docker compose up --build --wait` starts the whole stack instead.

## Commands

- `pytest` runs the tests with coverage and fails below 90 percent
- `ruff check .` lints the code (`ruff check --fix .` fixes what it can)
- `ruff format --check .` checks the formatting (`ruff format .` applies it)
- `mypy` type-checks sources and tests in strict mode
- `alembic upgrade head` applies the database migrations
- `docker build -t sample-python-api .` builds the container image
- `bash scripts/smoke.sh` creates, reads and deletes an item on a running service

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

With `APP_ENV=production` the service refuses to start while `DATABASE_URL`, `AUTH_PASSWORD`, `JWT_SECRET`, still have their development defaults.

More in [docs/index.md](docs/index.md).

## Owner

group:default/platform-team
