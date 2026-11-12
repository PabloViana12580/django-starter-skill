# Business modules

`python scripts/scaffold.py --list-modules` prints the live catalog. Roadmap:

| Module | Stage | Status | Depends on |
| --- | --- | --- | --- |
| Website (`pages`) | v1 | available | - |
| CRM (`crm`) | v1 | available | - |
| Catalog (`catalog`) | v2 | planned (pilot: cleaning-service) | - |
| Scheduling (`scheduling`) | v2 | planned (pilot: cleaning-service) | crm, catalog |
| Commerce (`commerce`) | v3 | planned (first client selling online) | crm, catalog |

Planned scope:
- **Catalog**: categories; items of kind product or service; Decimal prices with currency;
  stock for products; duration for services; photos.
- **Scheduling**: staff/teams with their own calendars, weekly hours, days off, appointment
  requests confirmed by staff, PostgreSQL exclusion constraint (btree_gist) against overlapping
  appointments per staff member, signed confirm/cancel links, .ics files, time zones. Contacts
  and timeline entries go through `crm.services`.
- **Commerce**: session cart, guest checkout, orders with price snapshots, status workflow,
  payment provider adapters (pay later; Stripe hosted Checkout with signed webhooks and
  idempotency), email receipts.

## Anatomy of a module

```
template/modules/<name>/
  module.json            name, order, title, summary, stage, status, apps, urls, depends_on,
                         personal_data, requirements, env, settings, controls
  <app>/                 a normal Django app: models, migrations, admin, services.py, views,
                         urls, templates/<app>/, static/<app>/, tests/, locale/
```

- `settings` lines are appended to `config/settings.py` (they may use `env_str`, `env_int`,
  `env_bool`, `env_list`, and the site settings).
- `env` lines are appended to `.env.example`; `controls` rows to `docs/security/CONTROLS.md`.
- Migrations need no row level security code: `core/rls.py` covers every table.
- Other modules call `services.py` functions, never another module's models directly.
- Before marking a module "available": its tests pass in a generated project with and without
  its optional neighbours, and it has been used in a real (pilot) project.

## Adding a module to an existing project

Copy `<app>/` into the project, add the app and URLs to `config/modules.py` (and
`MODULES_HOLD_PERSONAL_DATA`), append its `settings`, `env`, and `controls` lines, add its
requirements to `requirements.in` and recompile, then `migrate`, `dbcheck`, and test.
