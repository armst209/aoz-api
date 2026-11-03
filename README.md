# aoz-api

A read-only REST API for all things *Advance of Zeta*: mobile weapons, support weapons, characters and model kits.

It's built with [FastAPI](https://fastapi.tiangolo.com/) and stores its data in [Supabase](https://supabase.com/) (Postgres). Every resource has a fuzzy search endpoint backed by `pg_trgm` trigram similarity, so typos and partial names still find results.

## Tech stack

- **Python 3.14**
- **FastAPI** + **Uvicorn**: the web framework and ASGI server
- **Pydantic v2**: response models (camelCase JSON, snake_case Python)
- **Supabase** (`supabase-py`): the database client
- **PostgreSQL `pg_trgm`**: the fuzzy search functions, defined in SQL migrations

## Project structure

```
aoz-api/
├── app/
│   ├── main.py              # FastAPI app, CORS, router registration, /health
│   ├── db.py                # Supabase client (reads SUPABASE_URL / SUPABASE_KEY)
│   ├── schemas.py           # Pydantic response models
│   └── routes/
│       ├── mobile_weapons.py
│       ├── support_weapons.py
│       ├── characters.py
│       └── model_kits.py
├── data/                    # Source JSON data used for seeding
├── scripts/                 # Seed scripts that load data/*.json into Supabase
└── supabase/migrations/     # Table definitions and search_* SQL functions
```

## Getting started

### 1. Create a virtual environment and install dependencies

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install "fastapi[standard]" supabase python-dotenv
```

### 2. Configure environment variables

Create a `.env` file in the repo root:

```env
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_KEY=<your-supabase-key>
```

The API only reads data, so the `anon` key is enough if your RLS policies allow reads. The seed scripts write to the tables, so they need the `service_role` key if RLS is on.

> `.env` is git-ignored. Never commit your keys.

### 3. Set up the database

Apply the migrations in [supabase/migrations/](supabase/migrations/) in filename order. You can use the Supabase CLI (`supabase db push`) or paste each one into the SQL editor. They create the tables and the `search_*` functions, and enable `pg_trgm`.

### 4. Seed the data

Run these from the repo root:

```bash
python -m scripts.seed_characters
python -m scripts.seed_support_weapons
python -m scripts.seed_model_kits
```

You can safely re-run them: records are upserted by `id`, and their child rows are replaced.

### 5. Run the API

```bash
uvicorn app.main:app --reload --env-file .env
```

The API is served at `http://127.0.0.1:8000`, with interactive docs at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Testing

The tests use FastAPI's `TestClient` (built on Starlette) and pytest. They swap the Supabase client for an in-memory fake, so they need no database, network or `.env`.

```bash
pip install pytest
pytest
```

## API reference

All resource endpoints live under `/api/v1`.

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/health` | Health check, returns `{"status": "ok"}` |
| GET | `/api/v1/mobile_weapons/` | List all mobile weapons |
| GET | `/api/v1/mobile_weapons/search` | Fuzzy-search mobile weapons |
| GET | `/api/v1/support_weapons/` | List all support weapons |
| GET | `/api/v1/support_weapons/search` | Fuzzy-search support weapons |
| GET | `/api/v1/characters/` | List all characters |
| GET | `/api/v1/characters/search` | Fuzzy-search characters |
| GET | `/api/v1/model_kits/` | List all model kits |
| GET | `/api/v1/model_kits/search` | Fuzzy-search model kits |

### Search

Search endpoints combine every filter you pass and return results ranked best match first. You must pass **at least one** filter, or the endpoint returns `400`.

Every search endpoint also accepts these parameters:

| Param | Default | Description |
| ----- | ------- | ----------- |
| `threshold` | `0.3` | The minimum match score (0–1) each filter must reach |
| `limit` | `20` | The maximum number of results (1–100) |

The filters each resource supports:

| Resource | Filters |
| -------- | ------- |
| Mobile weapons | `id`, `name`, `modelNumber`, `codename`, `faction`, `era`, `pilots` |
| Support weapons | `id`, `name`, `modelNumber`, `codename`, `faction`, `era`, `pilots` |
| Characters | `id`, `name`, `japaneseName`, `gender`, `birthdate`, `deathdate`, `status`, `affiliations`, `rank`, `age` |
| Model kits | `id`, `name`, `series`, `line`, `grade`, `scale`, `manufacturer`, `releaseDate`, `price` |

Some model kit filters accept loose formats:

- **`scale`**: `1/144`, `144` or `1:144` (or `Mixed`)
- **`releaseDate`**: a year or month, such as `2004`, `2004-01`, `01/2004` or `Jan 2004`
- **`price`**: `2200` or `¥2,200`. Nearby prices also match.

### Examples

```bash
# Typos still match
curl "http://127.0.0.1:8000/api/v1/characters/search?name=hazle"

# Combine filters
curl "http://127.0.0.1:8000/api/v1/mobile_weapons/search?faction=Titans&era=UC&limit=5"

# Model kits by scale and release year
curl "http://127.0.0.1:8000/api/v1/model_kits/search?scale=144&releaseDate=2004"
```

Responses use camelCase keys, for example `modelNumber`, `unitType` and `imageUrl`.

### Errors

| Status | Meaning |
| ------ | ------- |
| `400` | A search request had no filters |
| `422` | A query parameter was invalid, such as a malformed UUID or an out-of-range `limit` |
| `502` | The upstream Supabase request failed |

## Notes

- CORS is open (`allow_origins=["*"]`). Restrict it before you deploy publicly.
