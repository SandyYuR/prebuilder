"""Validate committed downstream engine sources without modifying their checkout."""
import hashlib
import json
from pathlib import Path
import re
import subprocess


def git(source, *args):
    return subprocess.check_output(['git', '-C', str(source), *args], text=True).strip()


def verify_source(source: Path, pin: str, repository: str):
    if git(source, 'rev-parse', 'HEAD') != pin:
        raise ValueError('librime checkout does not match the prebuilder gitlink')
    if subprocess.run(['git', '-C', str(source), 'diff', '--quiet', 'HEAD', '--']).returncode:
        raise ValueError('librime has modified tracked files; commit source changes first')
    manifest = source / 'downstream/manifest.json'
    data = json.loads(manifest.read_text())
    normalize = lambda value: value.removesuffix('/').removesuffix('.git')
    if data.get('schema_version') != 1 or normalize(data['repository']) != normalize(repository):
        raise ValueError('downstream metadata does not match the configured librime repository')
    if data.get('upstream_repository') != 'https://github.com/rime/librime':
        raise ValueError('unexpected official librime repository')
    if not re.fullmatch(r'[0-9a-f]{40}', data.get('upstream_commit', '')):
        raise ValueError('upstream_commit must be an exact official commit')
    for patch in data['migration']['imported_patches']:
        if not re.fullmatch(r'[0-9a-f]{40}', patch['commit']) or not re.fullmatch(r'[0-9a-f]{64}', patch['sha256']):
            raise ValueError('invalid imported patch provenance')
    header = (source / 'src/rime_api.h').read_text()
    if not all(name in header for name in ('get_input_tabs', 'free_input_tabs', 'select_tab', 'clear_tabs', 'delete_candidate')):
        raise ValueError('the pinned source lacks required tabs/forget APIs')
    return {
        'librime_repository': repository,
        'librime_commit': pin,
        'upstream_repository': data['upstream_repository'],
        'upstream_commit': data['upstream_commit'],
        'source_tree': git(source, 'rev-parse', 'HEAD^{tree}'),
        'downstream_manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
        'core_patch_mode': 'committed-source',
        'patches': [],
        'integrated_patches': data['migration']['imported_patches'],
    }
