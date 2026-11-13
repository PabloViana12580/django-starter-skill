---
name: django-starter
description: Creates a new client project from a proven starter pack - Django 5.2 LTS + any cloud PostgreSQL (Supabase by default) + server-rendered HTML/Bootstrap, with a security baseline (OWASP ASVS 5.0 L1 + selected L2), tests, CI, docs, and a public GitHub repository - plus optional business modules (Website, CRM; Catalog, Scheduling, Commerce planned). Use when the user wants to start, scaffold, bootstrap, or create a new project, website, or "starter pack" for a business, or asks which modules are available.
---

# django-starter

Builds the same secure, tested, documented foundation for every new project, then a branded
home page from the user's brief. Each project's own features come afterwards, per project.

Skill folder: this file's directory (`SKILL_DIR`). Scripts are standard-library Python:
`scripts/scaffold.py`, `scripts/prepublish_check.py`, `scripts/github_setup.py`.

## Ground rules

- Never ask for database passwords in chat. The user pastes `DATABASE_URL` into the project's
  `.env` themselves. If they paste credentials anyway, use them, never repeat them, and suggest
  rotating them.
- One database per project. `manage.py dbcheck` refuses a database holding other tables; never
  point a project at another project's database, and never drop or reset anything you didn't create.
- Repositories are **public**: nothing secret, no database hosts or project refs, no customers'
  personal data in any committed file. `prepublish_check.py` must pass before every push.
- Follow the generated project's `AGENTS.md` (CSP without inline code, tokens, services layer...).
- Report real results: don't call a step done unless its check ran and passed.

## Phase A: create the project

1. **Prerequisites.** `gh auth status` must show a signed-in account (scopes include `workflow`).
   If not, ask the user to run `gh auth login --web --git-protocol https --scopes workflow`.
   Python 3.13 and Git must be available.
2. **Intake** (see `references/intake.md`). From the user's message, collect: project name,
   one-line description (tagline), language (`en` default), time zone, modules, reference website,
   brand colors/fonts (optional), contact details (optional), copyright holder (optional).
   Always show the module list first: run `python SKILL_DIR/scripts/scaffold.py --list-modules`
   and present every module (available and planned) so the user chooses. Ask for anything missing
   in **one** AskUserQuestion round.
3. **Scaffold.**
   `python SKILL_DIR/scripts/scaffold.py --name "<Name>" --modules <a,b> --tagline "<tagline>" --language <xx> --time-zone <Area/City> [--copyright "<holder>"]`
   Default parent folder: `%USERPROFILE%\OneDrive\Documentos\`. It creates `.venv` with pinned,
   hashed dependencies (a few minutes), `.env` with a fresh secret key, `src/images/`, and `git init`.
4. **No-database checks** in the new folder (settings refuse to load without a database, and `check`
   never connects, so give it a placeholder):
   `DATABASE_URL=postgresql://check:check@localhost/check .venv/Scripts/python.exe manage.py check`.
5. **GitHub repository:** `python SKILL_DIR/scripts/github_setup.py create <project>`
   (public, remote `origin`, nothing pushed yet).
6. **Hand over and stop.** Tell the user, in one message:
   - paste the database URI into `<project>\.env` on the marked line (provider-specific
     instructions from `references/databases.md`; Supabase = Session pooler URI);
   - put the business's images into `<project>\src\images\`;
   - send the brief details still missing (reference site, colors, copy notes);
   - say "ready" when done.

## Phase B: finish (after the user says "ready")

1. **Database.** `manage.py dbcheck --before-migrate`, then `migrate`, then `dbcheck`, then the
   full test suite `manage.py test --noinput`. Fix failures before going on. If a test run is
   interrupted on a pooled database, drop the leftover `test_<db>` with `WITH (FORCE)`.
2. **Images.** `manage.py optimize_images` (WebP copies in `static/img/` + credits).
3. **Design pass** (read `references/design-pass.md` and load the `frontend-design` skill):
   take the reference site's structure (not its text or images unless the user owns them),
   choose palette and fonts unless given, self-host the fonts, set the tokens in
   `static/css/app.css` and `static/css/admin.css`, and rewrite every `STARTER-TODO:` page
   (home, about, privacy, terms) and the README in the site's language with the user's images.
   Legal pages stay drafts for the owner to confirm, and say so.
4. **Language.** If the site language isn't English, also translate `README.md` and `docs/`
   (CLAUDE.md and AGENTS.md stay English) and check the interface strings are translated
   (`locale/`).
5. **Verify** in the project (all must pass):
   - `ruff check .` and `ruff format --check .`
   - `manage.py makemigrations --check --dry-run`
   - `manage.py check --deploy --fail-level WARNING` with production variables
     (`DJANGO_DEBUG=false`, a long `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS=example.com`)
   - `coverage run manage.py test --noinput && coverage report`
   - `pip-audit --require-hashes -r requirements.txt --strict`
   - `bandit -c pyproject.toml -r . -x "./staticfiles,*/tests/*,*/tests.py" -ll`
   - run the server and check `/`, the module pages, `/accounts/login/`, `/healthz`, `/readyz`
     return 200 with the security headers; take screenshots (desktop 1440 px and narrow 520 px,
     headless Chrome) and review them against the brief. Fix and re-check.
6. **Publish.** `python SKILL_DIR/scripts/prepublish_check.py <project>` must pass. Then
   `git add -A`, commit "Initial project from django-starter <version>" (with the attribution
   trailer), tag `v0.1.0`, `git push -u origin main --tags`,
   `python SKILL_DIR/scripts/github_setup.py harden <project>`, wait for CI on the pushed commit
   (`gh run list --commit $(git rev-parse HEAD) --workflow CI --json databaseId -q '.[0].databaseId'`,
   then `gh run watch <id> --exit-status`; the run can take a few seconds to appear), and create the release:
   `gh release create v0.1.0 --title v0.1.0 --notes-file <notes from CHANGELOG>`.
7. **Report** to the user: local URL and how to start it, repository URL, CI result, what is
   placeholder (business details, prices, legal review), how to create the owner's account
   (`manage.py createsuperuser`, then two-factor setup at first sign-in), and next steps.

## References

- `references/intake.md`: the brief, defaults, validation.
- `references/databases.md`: connection strings per provider, pitfalls, test databases.
- `references/hosting.md`: deploying later (any platform), proxy settings.
- `references/design-pass.md`: the branding workflow, fonts, images, accessibility.
- `references/security.md`: the baseline, how it's verified, framework mapping.
- `references/modules.md`: module catalog, how modules are built and added.
