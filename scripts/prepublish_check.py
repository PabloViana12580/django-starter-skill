#!/usr/bin/env python3
"""
Checks a project before its first commit and every push to a public repository.
Standard library only. Exits non-zero when something must be fixed.

    python prepublish_check.py PATH/TO/PROJECT

- .env exists and is ignored by Git.
- No value of a secret from .env (passwords, keys, tokens, the database URL and
  its host) appears in any file Git would commit.
- No `STARTER-TODO:` placeholder is left.
- No file Git would commit is larger than 10 MB.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

SECRET_NAME = re.compile(r'(SECRET|PASSWORD|TOKEN|KEY|DATABASE_URL)', re.IGNORECASE)
PLACEHOLDER = 'STARTER-TODO:'
MAX_BYTES = 10 * 1024 * 1024
MIN_SECRET_LENGTH = 8


def git(project, *args):
    return subprocess.run(['git', *args], cwd=project, capture_output=True, text=True)


def env_values(env_file):
    values = {}
    for line in env_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        name, _, value = line.partition('=')
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def sensitive_strings(values):
    """(label, text) pairs that must never appear in committed files."""
    found = []
    for name, value in values.items():
        if not value or not SECRET_NAME.search(name):
            continue
        if name == 'DATABASE_URL':
            parts = urlsplit(value)
            if parts.password:
                found.append(('database password', unquote(parts.password)))
            if parts.hostname and parts.hostname not in ('localhost', '127.0.0.1', '::1'):
                found.append(('database host', parts.hostname))
            if parts.username and '.' in parts.username:
                found.append(('database user (contains the project reference)', parts.username))
        elif len(value) >= MIN_SECRET_LENGTH:
            found.append((name, value))
    return found


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    project = Path(argv[1]).resolve()
    problems = []

    env_file = project / '.env'
    if not env_file.exists():
        problems.append('.env is missing.')
    elif git(project, 'check-ignore', '-q', '.env').returncode != 0:
        problems.append('.env is NOT ignored by Git. Fix .gitignore before committing.')

    listing = git(project, 'ls-files', '--cached', '--others', '--exclude-standard', '-z')
    if listing.returncode != 0:
        problems.append('Not a Git repository (run git init).')
        files = []
    else:
        files = [project / name for name in listing.stdout.split('\0') if name]

    # (label, value) pairs from .env that must not appear in any committable file.
    watched = sensitive_strings(env_values(env_file)) if env_file.exists() else []
    for path in files:
        if not path.is_file():
            continue
        if path.stat().st_size > MAX_BYTES:
            problems.append(f'{path.relative_to(project)} is larger than 10 MB.')
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(project)
        for label, value in watched:
            if value in text:
                problems.append(f'{relative} contains the {label} from .env.')
        if PLACEHOLDER in text:
            problems.append(f'{relative} still has a {PLACEHOLDER} placeholder.')

    if problems:
        print('Pre-publish check FAILED:')
        for problem in problems:
            print(f'  - {problem}')
        return 1
    print(f'Pre-publish check passed: {len(files)} files, {len(watched)} .env values checked.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
