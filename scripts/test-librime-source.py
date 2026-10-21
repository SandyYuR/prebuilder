#!/usr/bin/env python3
"""Protect source pins and committed-source ownership during builder migration."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from librime_source import git, verify_source


class SourceContract(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / 'downstream').mkdir()
        (self.root / 'src').mkdir()
        (self.root / 'src/rime_api.h').write_text('get_input_tabs free_input_tabs select_tab clear_tabs delete_candidate\n')
        self.repository = 'https://github.com/SandyYuR/librime.git'
        self.metadata = {'schema_version': 1, 'repository': self.repository,
                         'upstream_repository': 'https://github.com/rime/librime',
                         'upstream_commit': '1' * 40,
                         'migration': {'imported_patches': [{'name': 'historical.patch', 'commit': '2' * 40, 'sha256': '3' * 64}]}}
        self.write_metadata()
        self.commit()

    def write_metadata(self):
        (self.root / 'downstream/manifest.json').write_text(json.dumps(self.metadata))

    def commit(self):
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Source contract test',
                        '-c', 'user.email=source-contract@users.noreply.github.com',
                        'commit', '-qm', 'source fixture'], check=True)
        self.pin = git(self.root, 'rev-parse', 'HEAD')

    def test_committed_features_are_provenance_not_reapplied_patches(self):
        result = verify_source(self.root, self.pin, self.repository)
        self.assertEqual(result['patches'], [])
        self.assertEqual(result['core_patch_mode'], 'committed-source')
        self.assertEqual(result['integrated_patches'], self.metadata['migration']['imported_patches'])

    def test_wrong_pin_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'gitlink'):
            verify_source(self.root, '0' * 40, self.repository)

    def test_dirty_source_is_rejected_without_resetting_it(self):
        header = self.root / 'src/rime_api.h'
        contents = header.read_text() + '// uncommitted edit\n'
        header.write_text(contents)
        with self.assertRaisesRegex(ValueError, 'modified tracked files'):
            verify_source(self.root, self.pin, self.repository)
        self.assertEqual(header.read_text(), contents)

    def test_unrelated_repository_cannot_supply_the_source(self):
        self.metadata['repository'] = 'https://github.com/rime/librime'
        self.write_metadata()
        self.commit()
        with self.assertRaisesRegex(ValueError, 'configured librime repository'):
            verify_source(self.root, self.pin, self.repository)

    def test_untracked_compilation_input_is_rejected_without_deleting_it(self):
        source = self.root / 'src/extra.cc'
        source.write_text('// not part of the pinned source\n')
        with self.assertRaisesRegex(ValueError, 'untracked source files'):
            verify_source(self.root, self.pin, self.repository)
        self.assertTrue(source.exists())


if __name__ == '__main__':
    unittest.main()
