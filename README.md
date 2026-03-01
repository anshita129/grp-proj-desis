# Project notes and setup

This repository contains a single Django project (`backend`) with multiple apps. The database configuration is designed to use PostgreSQL by default; SQLite is only used if explicitly requested via `DB_ENGINE`.

## Default database (Postgres)

The `default` database connection uses the following environment variables:

- `DB_ENGINE` (default `django.db.backends.postgresql`)
- `DB_NAME` (default `default_db`)
- `DB_USER` (default `default_user`)
- `DB_PASSWORD` (default `changeit`)
- `DB_HOST` (default `localhost`)
- `DB_PORT` (default `5432`)

For a quick development start you can still force SQLite:

```powershell
$env:DB_ENGINE = 'django.db.backends.sqlite3'
# the NAME will then default to BASE_DIR/db.sqlite3 unless you set DB_NAME
```

Install Postgres driver in your Python environment:

```powershell
pip install psycopg2-binary
```

Create the Postgres database and user using `psql` or similar:

```sql
CREATE DATABASE default_db;
CREATE USER default_user WITH PASSWORD 'changeit';
GRANT ALL PRIVILEGES ON DATABASE default_db TO default_user;
```

Run standard migrations for apps that use the default DB:

```powershell
python backend/manage.py migrate
```

## Trading app database (optional)

The `trading` app is routed to a separate Postgres database; this is optional and can be removed if you prefer a single database.

Set these variables:

```powershell
$env:TRADING_DB_NAME = 'trading_db'
$env:TRADING_DB_USER = 'trading_user'
$env:TRADING_DB_PASSWORD = 'securepassword'
$env:TRADING_DB_HOST = 'localhost'
$env:TRADING_DB_PORT = '5432'
```

```powershell
pip install psycopg2-binary
```

- Create the Postgres database and user (example using `psql`):

```sql
CREATE DATABASE trading_db;
CREATE USER trading_user WITH PASSWORD 'securepassword';
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;
```

- Run migrations for the `trading` app against the Postgres DB:

```powershell
python backend/manage.py migrate --database=trading
```

Notes
- The router `core.db_routers.TradingRouter` ensures models in the `trading` app use the `trading` Postgres DB.
- To apply migrations to the default (Postgres) database, simply run `python backend/manage.py migrate`.

