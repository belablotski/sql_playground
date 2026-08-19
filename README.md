# SQL Playground

A small sandbox for experimenting with SQL — primarily targeting the
**Microsoft SQL Server (T-SQL)** dialect — backed by a synthetic retail /
e-commerce dataset.

## What's here

- [`sql/schema.sql`](sql/schema.sql) — T-SQL DDL defining the database schema
  (Customers, Employees, Categories, Products, Orders, OrderItems).
- [`sql/sample_queries.sql`](sql/sample_queries.sql) — example queries
  (joins, aggregates, window functions, CTEs, self-joins) to explore.
- [`scripts/generate_data.py`](scripts/generate_data.py) — Python script that
  generates synthetic test data (CSV files + a T-SQL insert script).
- [`scripts/build_sqlite_db.py`](scripts/build_sqlite_db.py) — builds a local
  SQLite database from the generated CSVs, for quick experimentation without
  a SQL Server instance.
- [`docs/DB_STRUCTURE.md`](docs/DB_STRUCTURE.md) — full description of the
  schema and the generated data.

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate test data

```bash
python scripts/generate_data.py
```

This writes CSV files to `data/csv/` and a T-SQL insert script to
`data/insert_data.sql`. Customize volumes and the random seed:

```bash
python scripts/generate_data.py --customers 200 --orders 1000 --seed 7
```

### 3a. Load into SQL Server

```bash
sqlcmd -S <server> -d <database> -i sql/schema.sql
sqlcmd -S <server> -d <database> -i data/insert_data.sql
```

### 3b. Or build a local SQLite database instead

If you don't have a SQL Server instance handy, build an equivalent SQLite
database to run queries locally:

```bash
python scripts/build_sqlite_db.py
sqlite3 data/playground.db
```

> Note: the SQLite version adapts a few dialect-specific pieces (e.g.
> `IDENTITY` → `INTEGER PRIMARY KEY`, `BIT` → `INTEGER`). `sql/schema.sql`
> remains the source of truth for the SQL Server dialect.

### 4. Run sample queries

Open [`sql/sample_queries.sql`](sql/sample_queries.sql) in your SQL Server
client (or adapt slightly for SQLite — see notes at the top of the file) and
run the queries to explore joins, aggregations, window functions, and CTEs.

## Repository layout

```
sql/                 T-SQL schema and sample queries
scripts/             Python data-generation & SQLite build scripts
docs/                Documentation (schema & data description)
data/                Generated CSVs / SQL / SQLite DB (git-ignored)
requirements.txt     Python dependencies
```
