# Changelog

Versions of the django-starter skill and its template ([SemVer](https://semver.org/)).
Projects record the version they were created with in `.starter.json`.

## [Unreleased]

### Changed
- `prepublish_check.py`: clearer variable names (CodeQL read a count of checked values as logged secrets).

## [0.1.0] - 2026-11-12

### Added
- Stage v1: core template (configuration, PostgreSQL with RLS and `dbcheck`, staff sign-in with
  Argon2id, lockout and TOTP two-factor, sessions, CSP and security headers, probes, security
  logging, spam protection, email, image optimization, Spanish interface catalog, CI, GitHub
  hardening, docs and security controls matrix) and the Website and CRM modules.
- Scripts: `scaffold.py`, `prepublish_check.py`, `github_setup.py`.
- CI for the skill: scaffold tests, and a generated project per module combination checked on PostgreSQL.
