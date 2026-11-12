# django-starter

A [Claude Code](https://claude.com/claude-code) skill that creates new business websites from one
proven foundation: **Django 5.2 LTS + any PostgreSQL (Supabase by default) + server-rendered
HTML/Bootstrap**, with a security baseline, tests, CI, documentation, and a public GitHub
repository, plus optional business modules.

## What every project gets

- Configuration from environment variables, hosting-agnostic (`Procfile`, `Dockerfile`, platform host detection).
- PostgreSQL with TLS, row level security on every table, and a `dbcheck` command (connection, TLS, isolation).
- Staff sign-in with Argon2id passwords, lockout after repeated failures, two-factor login (authenticator apps), session timeouts.
- Strict Content Security Policy (`'self'` only, self-hosted Bootstrap and fonts), HSTS, secure cookies, security headers.
- Health and readiness probes, security event logging, generic error pages.
- Spam protection for public forms, email notifications, image optimization (metadata removed).
- One language per site (English or Spanish interface included).
- CI: ruff, `check --deploy`, tests on PostgreSQL with a coverage gate, bandit, pip-audit, SBOM, gitleaks.
- GitHub hardening: Dependabot, secret scanning with push protection, CodeQL, private vulnerability reporting, protected default branch.
- Docs: owner README, developer guide, CLAUDE.md/AGENTS.md, security controls matrix (OWASP ASVS 5.0 L1 + selected L2, mapped to NIST SSDF, NIST CSF 2.0, ISO/IEC 27002:2022, CIS, ISO/IEC 25010, ITIL 4), threat model, runbook.

## Business modules

| Module | Status |
| --- | --- |
| Website: home, about, privacy, terms | available (v1) |
| CRM: contacts, timeline, contact form leads, pipeline, tasks, CSV export, consent | available (v1) |
| Catalog: products and services | planned (v2) |
| Scheduling: appointments with staff calendars | planned (v2) |
| Commerce: cart, checkout, payments | planned (v3) |

## Install

Clone this repository and link it into your Claude Code skills folder:

```powershell
git clone https://github.com/PabloViana12580/django-starter-skill.git
New-Item -ItemType Junction -Path "$HOME\.claude\skills\django-starter" -Target ".\django-starter-skill"
```

Then ask Claude Code to "start a new project with django-starter". Requirements: Python 3.13,
Git, GitHub CLI (`gh auth login --web --git-protocol https --scopes workflow`), and a PostgreSQL
database per project.

## Use without Claude

```bash
python scripts/scaffold.py --list-modules
python scripts/scaffold.py --name "Example Shop" --modules website,crm --tagline "..." --language en
```

## Development

```bash
python -m unittest discover -s tests      # scaffold tests (no database needed)
```

The generated project's own tests need PostgreSQL. CI (`.github/workflows/ci.yml`) runs the scaffold
tests and generates a project for each module combination, then runs its lint, checks, tests,
bandit, and pip-audit on PostgreSQL 17. See `CHANGELOG.md` for versions.

## License

MIT (see LICENSE). Bootstrap is MIT-licensed (template/base/static/vendor/bootstrap/LICENSE).
