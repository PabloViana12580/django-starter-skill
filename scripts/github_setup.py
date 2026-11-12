#!/usr/bin/env python3
"""
GitHub repository setup through the GitHub CLI (gh). Standard library only.

    python github_setup.py create PATH/TO/PROJECT     # public repo named after the folder, remote 'origin', no push
    python github_setup.py harden PATH/TO/PROJECT     # after the first push: security settings and branch ruleset

`harden` turns on Dependabot alerts and security updates, secret scanning with
push protection, private vulnerability reporting, CodeQL default setup, and a
ruleset that blocks force-pushes and deletion of the default branch. Each step
is reported; one failing step does not stop the others.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def gh(*args, input_json=None, cwd=None):
    result = subprocess.run(
        ['gh', *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        input=json.dumps(input_json) if input_json is not None else None,
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def require_gh():
    ok, output = gh('auth', 'status')
    if not ok:
        raise SystemExit('GitHub CLI is not signed in. Run: gh auth login --web --git-protocol https --scopes workflow')
    if 'workflow' not in output:
        print(
            'Warning: the gh token may lack the "workflow" scope; pushing .github/workflows can fail. '
            'Fix with: gh auth refresh --scopes workflow'
        )


def repo_name(project):
    ok, output = gh('repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner', cwd=project)
    if not ok:
        raise SystemExit(f'No GitHub repository for {project}: {output}')
    return output


def create(project):
    require_gh()
    name = project.name
    ok, output = gh(
        'repo', 'create', name, '--public', '--source', str(project), '--remote', 'origin', '--description', f'{name} website'
    )
    print(output)
    if not ok:
        raise SystemExit('Repository creation failed (does a repository with this name already exist?).')
    return 0


def harden(project):
    require_gh()
    repo = repo_name(project)
    ok, default_branch = gh('repo', 'view', repo, '--json', 'defaultBranchRef', '--jq', '.defaultBranchRef.name')
    default_branch = default_branch if ok and default_branch else 'main'
    steps = [
        ('Dependabot alerts', ('api', '-X', 'PUT', f'repos/{repo}/vulnerability-alerts'), None),
        ('Dependabot security updates', ('api', '-X', 'PUT', f'repos/{repo}/automated-security-fixes'), None),
        (
            'Secret scanning + push protection',
            ('api', '-X', 'PATCH', f'repos/{repo}', '--input', '-'),
            {
                'security_and_analysis': {
                    'secret_scanning': {'status': 'enabled'},
                    'secret_scanning_push_protection': {'status': 'enabled'},
                },
            },
        ),
        ('Private vulnerability reporting', ('api', '-X', 'PUT', f'repos/{repo}/private-vulnerability-reporting'), None),
        (
            'CodeQL default setup',
            ('api', '-X', 'PATCH', f'repos/{repo}/code-scanning/default-setup', '--input', '-'),
            {'state': 'configured', 'query_suite': 'default'},
        ),
        (
            f'Ruleset protecting {default_branch}',
            ('api', '-X', 'POST', f'repos/{repo}/rulesets', '--input', '-'),
            {
                'name': 'Protect default branch',
                'target': 'branch',
                'enforcement': 'active',
                'conditions': {'ref_name': {'include': ['~DEFAULT_BRANCH'], 'exclude': []}},
                'rules': [{'type': 'deletion'}, {'type': 'non_fast_forward'}],
            },
        ),
    ]
    failures = 0
    for label, args, body in steps:
        ok, output = gh(*args, input_json=body)
        if ok:
            print(f'  ok    {label}')
        else:
            failures += 1
            print(f'  FAIL  {label}: {output[:300]}')
    print(f'{repo}: {len(steps) - failures} of {len(steps)} settings applied.')
    return 1 if failures else 0


def main(argv):
    if len(argv) != 3 or argv[1] not in ('create', 'harden'):
        print(__doc__)
        return 2
    project = Path(argv[2]).resolve()
    return create(project) if argv[1] == 'create' else harden(project)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
