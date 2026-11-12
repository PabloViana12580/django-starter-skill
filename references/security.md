# Security baseline

The generated project targets **OWASP ASVS 5.0 level 1 plus selected level 2** requirements and
maps its controls to NIST SSDF, NIST CSF 2.0, ISO/IEC 27002:2022, CIS (applicable parts),
ISO/IEC 25010:2023, and ITIL 4. The full matrix (control, implementation, verification,
framework IDs, known gaps) is the project's `docs/security/CONTROLS.md`; the threat model is
`docs/security/THREAT_MODEL.md`.

Wording rule: docs say "mapped to", never "compliant" or "certified" (those need an audit of an
organization).

## What verifies what

| Layer | Verification |
| --- | --- |
| Configuration, database, auth, two-factor, sessions, headers, probes, logging, spam | `manage.py test` (core tests) |
| Module controls | each module's tests |
| Deployment settings | `check --deploy --fail-level WARNING` with production variables |
| Code | ruff (with security rules), bandit, CodeQL (GitHub) |
| Dependencies | hashed pins, pip-audit, Dependabot, SBOM |
| Secrets | `prepublish_check.py`, gitleaks in CI, GitHub push protection |
| Repository | ruleset on the default branch, private vulnerability reporting |

## When adding features to a project

- New public form: extend `core.spam.SpamProtectedForm`, rate limit the view, test both.
- New personal data: update the threat model's data inventory, the privacy page, and CONTROLS.md;
  keep `MODULES_HOLD_PERSONAL_DATA` true so staff two-factor stays on.
- New external service: adapter module, credentials in env, tests with a fake.
- New table: nothing for RLS (automatic after migrate); `dbcheck` and the tests confirm it.
