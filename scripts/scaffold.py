#!/usr/bin/env python3
"""
Create a new Django project from the django-starter template.

Standard library only. Copies template/base plus the chosen business modules,
fills the __TOKENS__, writes .env with a fresh secret key (DATABASE_URL left
for the user), creates .venv with pinned and hashed dependencies, and runs
`git init`. Nothing is committed or pushed.

    python scaffold.py --list-modules
    python scaffold.py --name "Brightwell Home Cleaning" --modules website,crm \
        --tagline "Home cleaning in Hartford County" --language en --time-zone America/New_York
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import shutil
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / 'template'
BASE_DIR = TEMPLATE_DIR / 'base'
MODULES_DIR = TEMPLATE_DIR / 'modules'
PLANNED_MODULES_FILE = MODULES_DIR / 'planned.json'
DEFAULT_PARENT = Path.home() / 'OneDrive' / 'Documentos'
STARTER_VERSION = (SKILL_DIR / 'VERSION').read_text(encoding='utf-8').strip() if (SKILL_DIR / 'VERSION').exists() else 'dev'

TEXT_SUFFIXES = {
    '.py',
    '.html',
    '.txt',
    '.md',
    '.css',
    '.js',
    '.json',
    '.toml',
    '.yml',
    '.yaml',
    '.in',
    '.cfg',
    '.ini',
    '.example',
    '.po',
    '',
}
TEXT_NAMES = {
    '.gitignore',
    '.gitattributes',
    '.editorconfig',
    '.dockerignore',
    '.python-version',
    'Procfile',
    'Dockerfile',
    'LICENSE',
}
SKIP_PARTS = {'__pycache__', '.pytest_cache', '.ruff_cache'}
# Third-party files are copied unchanged and never scanned for tokens.
VENDOR_PARTS = {'vendor', '.venv'}
TOKEN = re.compile(r'__[A-Z][A-Z0-9_]*__')


# Modules ---------------------------------------------------------------------


def load_modules():
    modules = {}
    for manifest in MODULES_DIR.glob('*/module.json'):
        data = json.loads(manifest.read_text(encoding='utf-8'))
        data['path'] = manifest.parent
        modules[data['name']] = data
    return dict(sorted(modules.items(), key=lambda item: item[1].get('order', 99)))


def load_planned():
    if PLANNED_MODULES_FILE.exists():
        return json.loads(PLANNED_MODULES_FILE.read_text(encoding='utf-8'))
    return []


def list_modules():
    rows = [
        (m['name'], m['title'], m['stage'], 'available', ', '.join(m['depends_on']) or '-', m['summary'])
        for m in load_modules().values()
    ]
    rows += [
        (m['name'], m['title'], m['stage'], 'planned', ', '.join(m['depends_on']) or '-', m['summary']) for m in load_planned()
    ]
    print('Business modules (core is always included):\n')
    for name, title, stage, status, depends, summary in rows:
        print(f'- {name} ({title}) [{status}, {stage}] depends on: {depends}\n  {summary}\n')


def resolve_modules(requested, available):
    unknown = [name for name in requested if name not in available]
    if unknown:
        planned = {m['name'] for m in load_planned()}
        not_ready = [name for name in unknown if name in planned]
        if not_ready:
            raise SystemExit(f'Not available yet (planned): {", ".join(not_ready)}. Run --list-modules.')
        raise SystemExit(f'Unknown module(s): {", ".join(unknown)}. Run --list-modules.')
    ordered = []

    def visit(name, chain=()):
        if name in chain:
            raise SystemExit(f'Module dependency cycle: {" -> ".join((*chain, name))}')
        for dependency in available[name]['depends_on']:
            if dependency not in requested:
                raise SystemExit(f'Module {name!r} needs {dependency!r}; add it to --modules.')
            visit(dependency, (*chain, name))
        if name not in ordered:
            ordered.append(name)

    for name in requested:
        visit(name)
    return [available[name] for name in ordered]


# Text helpers ----------------------------------------------------------------


def slugify(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s_]+', '-', value).strip('-')


def env_value(value):
    """A value for a .env line, quoted when needed (python-dotenv syntax)."""
    if value and re.fullmatch(r'[\w@.:/+-]+', value):
        return value
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def is_text(path):
    return path.name in TEXT_NAMES or path.suffix.lower() in TEXT_SUFFIXES


def render(text, tokens, python=False):
    if python:
        # Quoted tokens become Python string literals, safe for any characters.
        for name, value in tokens.items():
            if isinstance(value, str):
                text = text.replace(f"'{name}'", repr(value))
    for name, value in tokens.items():
        text = text.replace(name, value if isinstance(value, str) else repr(value))
    return text


# Steps -----------------------------------------------------------------------


def copy_tree(source, target, exclude=()):
    for path in sorted(source.rglob('*')):
        relative = path.relative_to(source)
        if SKIP_PARTS & set(relative.parts) or relative.name in exclude or path.is_dir():
            continue
        destination = target / relative
        if destination.exists():
            raise SystemExit(f'Two template parts both provide {relative}; fix the template.')
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def build_tokens(args, modules):
    apps = [app for module in modules for app in module['apps']]
    urls = [tuple(entry) for module in modules for entry in module['urls']]
    settings_lines = [line for module in modules for line in module['settings']] or ['# (none)']
    env_lines = [line for module in modules for line in module['env']]
    holder = args.copyright or git_config('user.name') or args.name
    return {
        '__PROJECT_NAME_ENV__': env_value(args.name),
        '__PROJECT_TAGLINE_ENV__': env_value(args.tagline),
        '__PROJECT_NAME__': args.name,
        '__PROJECT_SLUG__': args.slug,
        '__PROJECT_TAGLINE__': args.tagline,
        '__LANGUAGE_CODE__': args.language,
        '__TIME_ZONE__': args.time_zone,
        '__YEAR__': str(date.today().year),
        '__CREATED_DATE__': date.today().isoformat(),
        '__COPYRIGHT_HOLDER__': holder,
        '__STARTER_VERSION__': STARTER_VERSION,
        '__MODULE_APPS__': apps,
        '__MODULE_URLS__': urls,
        '__MODULES_HOLD_PERSONAL_DATA__': any(module['personal_data'] for module in modules),
        '__MODULE_SETTINGS__': '\n'.join(settings_lines),
        '__MODULE_ENV__': ('\n# --- Business modules ---\n' + '\n'.join(env_lines)) if env_lines else '',
        '__MODULE_LIST__': ', '.join(module['title'] for module in modules) or 'none',
        '__MODULE_TABLE__': '\n'.join(
            f'| {module["title"]} | `{"`, `".join(module["apps"])}` | {module["summary"]} |' for module in modules
        )
        or '| (none) | | |',
        '__MODULE_CONTROLS__': '\n'.join(row for module in modules for row in module.get('controls', []))
        or '| - | No business modules installed | | | | | | |',
    }


def fill_tokens(project, tokens):
    for path in project.rglob('*'):
        if path.is_dir() or not is_text(path) or VENDOR_PARTS & set(path.parts):
            continue
        text = path.read_text(encoding='utf-8')
        if '__' not in text:
            continue
        new = render(text, tokens, python=path.suffix == '.py')
        if new != text:
            path.write_text(new, encoding='utf-8', newline='\n')
    leftovers = []
    for path in project.rglob('*'):
        if path.is_file() and is_text(path) and not VENDOR_PARTS & set(path.parts):
            leftovers += [
                f'{path.relative_to(project)}: {token}' for token in set(TOKEN.findall(path.read_text(encoding='utf-8')))
            ]
    if leftovers:
        raise SystemExit('Unfilled template tokens:\n  ' + '\n  '.join(sorted(leftovers)))


def append_module_requirements(project, modules):
    lines = [line for module in modules for line in module['requirements']]
    if lines:
        with (project / 'requirements.in').open('a', encoding='utf-8', newline='\n') as handle:
            handle.write('\n# Business modules\n' + '\n'.join(lines) + '\n')


def write_env(project):
    example = (project / '.env.example').read_text(encoding='utf-8')
    secret = secrets.token_urlsafe(50)
    env = example.replace('DJANGO_SECRET_KEY=replace-with-a-long-random-string', f'DJANGO_SECRET_KEY={secret}')
    env = env.replace(
        '\nDATABASE_URL=\n',
        '\n# >>> PASTE YOUR DATABASE URL ON THE NEXT LINE (see the notes above) <<<\nDATABASE_URL=\n',
    )
    env = env.replace(
        '# Copy to .env and fill in real values. Never commit .env.',
        '# Local settings for this machine. Git-ignored: never commit this file.',
    )
    (project / '.env').write_text(env, encoding='utf-8', newline='\n')


def write_manifest(project, args, modules):
    manifest = {
        'starter_version': STARTER_VERSION,
        'created': date.today().isoformat(),
        'name': args.name,
        'slug': args.slug,
        'language': args.language,
        'time_zone': args.time_zone,
        'modules': [module['name'] for module in modules],
    }
    (project / '.starter.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')


def run(command, cwd, quiet=False):
    print('  $ ' + ' '.join(str(part) for part in command))
    result = subprocess.run(command, cwd=cwd, capture_output=quiet, text=True)
    if result.returncode != 0:
        if quiet:
            print(result.stdout[-4000:], result.stderr[-4000:])
        raise SystemExit(f'Command failed: {command[0]} (exit {result.returncode})')


def check_python(python):
    """The virtualenv must use the Python version the project pins in .python-version."""
    wanted = (BASE_DIR / '.python-version').read_text(encoding='utf-8').strip()
    try:
        found = subprocess.run(
            [python, '-c', 'import sys; print("%d.%d" % sys.version_info[:2])'], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        raise SystemExit(f'Cannot run the Python interpreter {python!r}.') from None
    if found != wanted:
        raise SystemExit(
            f'The project pins Python {wanted}, but {python} is Python {found}. '
            f'Pass --python with the path of a Python {wanted} interpreter.'
        )


def create_venv(project, python):
    venv_python = (
        project
        / '.venv'
        / ('Scripts' if sys.platform == 'win32' else 'bin')
        / ('python.exe' if sys.platform == 'win32' else 'python')
    )
    run([python, '-m', 'venv', '.venv'], project)
    run([venv_python, '-m', 'pip', 'install', '--quiet', '--upgrade', 'pip', 'pip-tools'], project, quiet=True)
    for name in ('requirements', 'requirements-dev'):
        run(
            [
                venv_python,
                '-m',
                'piptools',
                'compile',
                '--quiet',
                '--generate-hashes',
                '--allow-unsafe',
                '--strip-extras',
                '--output-file',
                f'{name}.txt',
                f'{name}.in',
            ],
            project,
            quiet=True,
        )
    run(
        [
            venv_python,
            '-m',
            'pip',
            'install',
            '--quiet',
            '--require-hashes',
            '-r',
            'requirements.txt',
            '-r',
            'requirements-dev.txt',
        ],
        project,
        quiet=True,
    )
    return venv_python


def git_config(key):
    try:
        return subprocess.run(['git', 'config', '--get', key], capture_output=True, text=True).stdout.strip()
    except OSError:
        return ''


# Main ------------------------------------------------------------------------


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--list-modules', action='store_true', help='Show available and planned modules, then exit.')
    parser.add_argument('--name', help='Display name, e.g. "Brightwell Home Cleaning".')
    parser.add_argument('--slug', help='Folder and repository name (default: from --name).')
    parser.add_argument('--modules', default='', help='Comma-separated business modules, e.g. website,crm.')
    parser.add_argument('--tagline', default='', help='One line describing the business.')
    parser.add_argument('--language', default='en', help='Site language code, e.g. en or es.')
    parser.add_argument('--time-zone', default='America/New_York', help='IANA time zone of the business.')
    parser.add_argument('--copyright', default='', help='Copyright holder for LICENSE (default: git user.name).')
    parser.add_argument(
        '--parent', default=str(DEFAULT_PARENT), help=f'Folder to create the project in (default: {DEFAULT_PARENT}).'
    )
    parser.add_argument('--python', default=sys.executable, help='Python 3.13 interpreter for the virtualenv.')
    parser.add_argument('--no-venv', action='store_true', help='Skip creating .venv and installing dependencies.')
    parser.add_argument('--no-git', action='store_true', help='Skip git init.')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.list_modules:
        list_modules()
        return 0
    if not args.name or not args.name.strip():
        raise SystemExit('--name is required.')
    args.name = ' '.join(args.name.split())
    args.slug = args.slug or slugify(args.name)
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,62}', args.slug):
        raise SystemExit(f'Invalid slug {args.slug!r}: use lowercase letters, digits, and hyphens.')
    if not re.fullmatch(r'[a-z]{2,3}(-[a-z]{2,4})?', args.language):
        raise SystemExit(f'Invalid language code {args.language!r} (e.g. en, es, pt-br).')
    try:
        ZoneInfo(args.time_zone)
    except (ZoneInfoNotFoundError, ValueError):
        raise SystemExit(f'Unknown time zone {args.time_zone!r} (e.g. America/New_York).') from None

    requested = [name.strip() for name in args.modules.split(',') if name.strip()]
    modules = resolve_modules(requested, load_modules())

    if not args.no_venv:
        check_python(args.python)

    project = Path(args.parent).expanduser().resolve() / args.slug
    if project.exists() and any(project.iterdir()):
        raise SystemExit(f'{project} already exists and is not empty.')

    print(f'Creating {project}')
    print(f'  modules: {", ".join(m["name"] for m in modules) or "none (core only)"}')
    project.mkdir(parents=True, exist_ok=True)
    copy_tree(BASE_DIR, project)
    for module in modules:
        copy_tree(module['path'], project, exclude={'module.json'})
    append_module_requirements(project, modules)
    fill_tokens(project, build_tokens(args, modules))
    write_env(project)
    write_manifest(project, args, modules)

    if not args.no_venv:
        print('Creating .venv and installing pinned, hashed dependencies (a few minutes)...')
        create_venv(project, args.python)
    if not args.no_git:
        run(['git', 'init', '--quiet', '--initial-branch=main'], project)

    print(f'\nDone: {project}')
    print('Next: paste DATABASE_URL into .env, then: manage.py dbcheck --before-migrate, migrate, test.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
