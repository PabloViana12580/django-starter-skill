"""Tests for scripts/scaffold.py and scripts/prepublish_check.py (no database, no network)."""

import ast
import json
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / 'scripts'))

import prepublish_check  # noqa: E402
import scaffold  # noqa: E402


def generate(parent, *extra):
    args = ['--name', "Bob's Café & Co", '--tagline', 'Coffee "to go"', '--parent', str(parent), '--no-venv', '--no-git', *extra]
    scaffold.main(args)
    return parent / 'bobs-cafe-co'


class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.parent = Path(self.tmp.name)

    def test_project_with_modules_has_no_unfilled_tokens_and_valid_python(self):
        project = generate(self.parent, '--modules', 'website,crm', '--language', 'es', '--time-zone', 'America/Guatemala')
        for path in project.rglob('*.py'):
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        modules = (project / 'config/modules.py').read_text(encoding='utf-8')
        self.assertIn("MODULE_APPS = ['pages', 'crm']", modules)
        self.assertIn('MODULES_HOLD_PERSONAL_DATA = True', modules)
        settings = (project / 'config/settings.py').read_text(encoding='utf-8')
        self.assertIn('"Bob\'s Café & Co"', settings)  # quoted safely as a Python literal
        self.assertIn("'America/Guatemala'", settings)
        self.assertIn('CRM_NOTIFY_EMAILS', settings)
        manifest = json.loads((project / '.starter.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['modules'], ['website', 'crm'])

    def test_env_has_a_fresh_secret_and_an_empty_database_url(self):
        project = generate(self.parent)
        env = (project / '.env').read_text(encoding='utf-8')
        self.assertNotIn('replace-with-a-long-random-string', env)
        self.assertIn('\nDATABASE_URL=\n', env)
        self.assertIn('SITE_NAME="Bob\'s Café & Co"', env)
        self.assertIn('SITE_TAGLINE="Coffee \\"to go\\""', env)

    def test_git_ignores_only_the_env_file(self):
        project = generate(self.parent, '--modules', 'website,crm')
        subprocess.run(['git', 'init', '--quiet'], cwd=project, check=True)
        command = ['git', 'ls-files', '--others', '--ignored', '--exclude-standard']
        ignored = subprocess.run(command, cwd=project, capture_output=True, text=True, check=True).stdout.split()
        self.assertEqual(ignored, ['.env'])

    def test_core_only_project(self):
        project = generate(self.parent)
        self.assertFalse((project / 'crm').exists())
        self.assertIn('MODULES_HOLD_PERSONAL_DATA = False', (project / 'config/modules.py').read_text(encoding='utf-8'))
        self.assertIn('No business modules installed', (project / 'docs/security/CONTROLS.md').read_text(encoding='utf-8'))

    def test_refuses_unknown_planned_and_missing_dependency_modules(self):
        for modules, message in (('nope', 'Unknown module'), ('scheduling', 'Not available yet')):
            with self.subTest(modules=modules), self.assertRaises(SystemExit) as error:
                generate(self.parent, '--modules', modules)
            self.assertIn(message, str(error.exception))

    def test_refuses_existing_folder(self):
        generate(self.parent)
        with self.assertRaises(SystemExit):
            generate(self.parent)

    def test_invalid_language_and_time_zone(self):
        for extra in (('--language', 'english'), ('--time-zone', 'Mars/Base')):
            with self.subTest(extra=extra), self.assertRaises(SystemExit):
                generate(self.parent, *extra)

    def test_python_version_must_match_the_pinned_one(self):
        pinned = (scaffold.BASE_DIR / '.python-version').read_text(encoding='utf-8').strip()
        current = '{}.{}'.format(*sys.version_info[:2])
        if current == pinned:
            scaffold.check_python(sys.executable)  # passes silently
        older = subprocess.CompletedProcess([], 0, stdout='3.9\n')
        with unittest.mock.patch.object(scaffold.subprocess, 'run', return_value=older):
            with self.assertRaisesRegex(SystemExit, 'pins Python'):
                scaffold.check_python('python')
        with self.assertRaisesRegex(SystemExit, 'Cannot run'):
            scaffold.check_python(str(self.parent / 'no-such-python.exe'))
        self.assertEqual(list(self.parent.iterdir()), [])


class PrepublishCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = generate(Path(self.tmp.name), '--modules', 'website')
        subprocess.run(['git', 'init', '--quiet'], cwd=self.project, check=True)
        env = self.project / '.env'
        env.write_text(
            env.read_text(encoding='utf-8').replace(
                '\nDATABASE_URL=\n',
                '\nDATABASE_URL=postgresql://postgres.abcdref:S3cret-pass@aws-1-x.pooler.supabase.com:5432/postgres\n',
            ),
            encoding='utf-8',
        )

    def check(self):
        return prepublish_check.main(['prepublish_check.py', str(self.project)])

    def test_fails_on_placeholders_then_passes_when_resolved(self):
        self.assertEqual(self.check(), 1)  # the template's STARTER-TODO markers
        for path in self.project.rglob('*'):
            if path.is_file() and path.suffix in ('.html', '.md'):
                text = path.read_text(encoding='utf-8')
                if 'STARTER-TODO:' in text:
                    path.write_text(text.replace('STARTER-TODO:', 'Done:'), encoding='utf-8')
        self.assertEqual(self.check(), 0)

    def test_detects_leaked_database_password(self):
        for path in self.project.rglob('*'):
            if path.is_file() and path.suffix in ('.html', '.md'):
                path.write_text(path.read_text(encoding='utf-8').replace('STARTER-TODO:', 'Done:'), encoding='utf-8')
        (self.project / 'notes.md').write_text('db password: S3cret-pass', encoding='utf-8')
        self.assertEqual(self.check(), 1)


if __name__ == '__main__':
    unittest.main()
