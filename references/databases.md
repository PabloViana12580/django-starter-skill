# Databases

Any PostgreSQL 14+ works. The user pastes the URI into `.env` (`DATABASE_URL=`), never in chat.

## Supabase (default)

- Use **Dashboard > Connect > Session pooler > URI**:
  `postgresql://postgres.<project-ref>:<password>@aws-<n>-<region>.pooler.supabase.com:5432/postgres`.
  The `aws-0`/`aws-1` prefix differs between projects: copy it, don't guess.
- Not the direct host `db.<ref>.supabase.co`: it is IPv6-only, failed DNS lookups on this
  Windows machine and is unreachable from Render's free tier. `dbcheck` warns about it.
- Not the transaction pooler (port 6543): settings reject it (Django needs session semantics).
- The `postgres` role can create the temporary test database. Tests then create `test_postgres`;
  Supavisor keeps a connection open, so `config/test_runner.py` drops it `WITH (FORCE)`. After an
  interrupted run: `DROP DATABASE IF EXISTS test_postgres WITH (FORCE);` from any SQL client.
- Free projects pause after about a week without activity; resume them from the dashboard.
- Optional hardening: download the project's CA certificate and set `DB_SSLMODE=verify-full`,
  `DB_SSLROOTCERT=<path>`.
- Never use a Supabase API key (anon, service_role) as a database password.

## Neon

- Dashboard > Connect; keep `sslmode=require&channel_binding=require` (settings pass every
  query parameter to the driver). Prefer the direct host over the `-pooler` one.
- `DB_SSLMODE=verify-full` with `DB_SSLROOTCERT=system` works (public CA).

## Aiven, Render Postgres, Railway, others

- Use the URI they show and make sure it ends with `?sslmode=require`.
- Render's free PostgreSQL expires after a limited period; fine for demos, not for production.
- If the role cannot create databases, `dbcheck` says so: run tests against a local PostgreSQL.

## Local PostgreSQL

`postgresql://<user>:<password>@localhost:5432/<db>?sslmode=disable`. Create a dedicated role
with `CREATEDB` (for tests) and a database it owns; the user runs that SQL with their own
superuser password.

## Checks

- `manage.py dbcheck --before-migrate`: connection, version, TLS, CREATEDB, isolation (no foreign tables).
- `manage.py dbcheck` after `migrate`: also row level security on every table.
