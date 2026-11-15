# Intake: the project brief

Collect these before scaffolding. Ask only for what's missing, in one round.

| Field | Required | Default | Notes |
| --- | --- | --- | --- |
| Project name | Yes | - | Display name, e.g. "Brightwell Home Cleaning". The folder and repository use its slug (`brightwell-home-cleaning`); confirm the slug if the name has accents or symbols. Check the reference site and logo for the brand's own spelling (accents, capitals) and ask if it differs from the brief. |
| Tagline | Yes | - | One sentence: what the business does, for whom, where. Used in titles, meta description, footer. |
| Modules | Yes | `website,crm` for a business site | Show `scaffold.py --list-modules` and let the user choose. Planned modules can't be selected yet; say which stage brings them. |
| Language | No | `en` | Site and docs language (`es` for Spanish). CLAUDE.md/AGENTS.md stay English. |
| Time zone | No | `America/New_York` | The business's IANA zone (e.g. `America/Guatemala`, `Europe/Madrid`). Matters for scheduling. |
| Reference website | No | - | Structure and section order only; never copy its text, and use its images only if the user owns them. |
| Images | No | - | The user drops them into `<project>/src/images/` after Phase A. |
| Brand colors, fonts, logo | No | Claude decides | When given, they win. Otherwise follow the frontend-design skill. |
| Contact details | No | placeholders | Phone, email, address/area, hours: go into `.env` (`SITE_*`), not into templates. |
| Copyright holder | No | git `user.name` | For the MIT LICENSE. Business assets stay all rights reserved regardless. |

Validation:
- The target folder `%USERPROFILE%\OneDrive\Documentos\<slug>` must not exist (or be empty).
- No GitHub repository with the same name may exist on the user's account (`gh repo view <slug>`).
- Module dependencies must be included (the scaffold explains what's missing).
