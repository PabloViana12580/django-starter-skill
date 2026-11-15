# Changelog

Versions of the django-starter skill and its template ([SemVer](https://semver.org/)).
Projects record the version they were created with in `.starter.json`.

## [Unreleased]

Fixes found by the first real project made with the skill (a Spanish site).

### Fixed
- Tests failed on non-English sites: assertions on interface text met the translations. The test
  runner (now `ProjectTestRunner`) runs tests with the interface in English; translation tests pick
  their language.
- Original images in `src/images/` were committed with their hidden data. `optimize_images` now
  removes it in place without re-encoding (EXIF and GPS, XMP, IPTC, comments, C2PA content
  credentials, data after the image), keeping color profiles and orientation; a test fails while a
  committed image still carries any.
- Dropping the test database could fail with "permission denied to terminate process" when
  autovacuum was working in it and the role is not a superuser; the drop is retried.
- A long tagline made `config/settings.py` fail the line-length lint; the line is wrapped.
- `src/images/README.md` named the code's copyright holder as the images' owner; it names the
  business.
- `scaffold.py` built the virtualenv from whichever Python ran it (possibly another project's
  virtualenv); it now defaults to the base interpreter.

### Added
- `src/images/crops.json`: publish only regions of an original (the photo inside a social-media
  graphic). Web copies no original produces any more are removed.
- `SITE_WHATSAPP`: an optional WhatsApp number, shown as a link in the footer and on the contact
  page.
- References: check the brand's own spelling at intake; read a reference site's real colors and
  fonts by rendering it; treat counters and testimonials on template sites as unconfirmed.

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
