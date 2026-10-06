"""Reject private inputs, executable artifacts, large files and common secret formats."""
import argparse
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BANNED_DIRS = {'.tools', '.venv', 'local', 'secrets', 'credentials', 'build', 'out', 'bin', 'obj', 'node_modules', 'dist'}
BANNED_SUFFIXES = {'.dll', '.sys', '.exe', '.efi', '.pdb', '.o', '.obj', '.lib', '.a', '.iso', '.img', '.vhd', '.vhdx', '.qcow2', '.fd', '.dmp', '.dump'}
PATTERNS = [rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
            rb'gh[pousr]_[A-Za-z0-9]{30,}', rb'github_pat_[A-Za-z0-9_]{50,}', rb'AKIA[0-9A-Z]{16}']

def review(tracked=False):
    command = ['git', 'ls-files', '-z'] if tracked else ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z']
    names = subprocess.check_output(command, cwd=ROOT).decode('utf-8').split('\0')
    total = 0
    for name in filter(None, names):
        path = Path(name)
        if any(p in BANNED_DIRS for p in path.parts) or path.suffix.lower() in BANNED_SUFFIXES or path.name.startswith('.env'):
            raise ValueError(f'Forbidden publication path: {name}')
        content = subprocess.check_output(['git', 'show', ':' + name], cwd=ROOT)
        if len(content) > 2 * 1024 * 1024:
            raise ValueError(f'Oversized source artifact: {name}')
        if content.startswith(b'MZ') or any(re.search(pattern, content) for pattern in PATTERNS):
            raise ValueError(f'Binary or secret signature: {name}')
        total += 1
    print(f'Publication source policy: PASS ({total} files); manual diff review still required')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--tracked', action='store_true')
    review(p.parse_args().tracked)
