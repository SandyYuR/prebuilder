#!/usr/bin/env python3
"""Prepare isolated pinned source worktrees; never reset the caller's source tree."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path)
parser.add_argument('--without-plugins', action='store_true')
args = parser.parse_args()
out = args.output.resolve()
if out.exists():
    raise SystemExit(f'Refusing to overwrite an existing source snapshot: {out}')
out.mkdir(parents=True)

def git(where, *options):
    return subprocess.check_output(['git', '-C', str(where), *options], text=True).strip()

def snapshot(name, target):
    source = root / name
    pin = git(root, 'rev-parse', 'HEAD:' + name)
    # Verify the chosen upstream pin, without changing the source checkout.
    if git(source, 'rev-parse', 'HEAD') != pin:
        raise SystemExit(f'{name}: checkout does not match the prebuilder gitlink')
    subprocess.run(['git', '-C', str(source), 'worktree', 'add', '--detach', str(target), pin], check=True)
    return pin

def apply(target, name):
    patch = root / 'patches' / name
    subprocess.run(['git', '-C', str(target), 'apply', '--check', str(patch)], check=True)
    subprocess.run(['git', '-C', str(target), 'apply', str(patch)], check=True)
    return {'name': name, 'sha256': hashlib.sha256(patch.read_bytes()).hexdigest()}

record = {'prebuilder_commit': git(root, 'rev-parse', 'HEAD'), 'plugins': {}}
record['upstream_commit'] = snapshot('librime', out / 'librime')
series = [p.strip() for p in (root / 'patches/librime-series').read_text().splitlines()
          if p.strip() and not p.startswith('#')]
assert series[-1] == 'librime-detect-modifications-fingerprint.patch'
record['patches'] = [apply(out / 'librime', p) for p in series]
if not args.without_plugins:
    for module, directory, patch in [('librime-lua', 'lua', 'librime-lua.patch'),
        ('librime-octagram', 'octagram', 'librime-octagram.patch'),
        ('librime-predict-leveldb', 'predict', 'librime-predict.patch')]:
        pin = snapshot(module, out / module)
        record['plugins'][module] = {'commit': pin, 'patch': apply(out / module, patch)}
        (out / 'librime/plugins' / directory).symlink_to(out / module, target_is_directory=True)
(out / 'source-manifest.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
