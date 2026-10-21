#!/usr/bin/env python3
"""Check the same source contract used by the isolated and full builders."""
import json
from pathlib import Path
import sys
from librime_source import git, verify_source

root = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'librime'
pin = git(root, 'rev-parse', 'HEAD:librime')
repository = git(root, 'config', '--file', '.gitmodules', 'submodule.librime.url')
print(json.dumps(verify_source(source, pin, repository), indent=2))
