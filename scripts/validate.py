"""Single reproducible acceptance command; every result comes from an executed check."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

def source_digest():
    paths = []
    for directory in ('boot', 'kernel', 'include', 'tests', 'tools', 'scripts', 'website'):
        paths += [p for p in (ROOT / directory).rglob('*') if p.is_file() and
                  not any(x in p.parts for x in ('__pycache__', 'dist', 'node_modules')) and p.suffix != '.pyc']
    paths += [ROOT / p for p in ('CMakeLists.txt', 'CMakePresets.json', 'VERSION', 'requirements-dev.txt',
                                'data/compatibility.json', 'data/compatibility.schema.json',
                                'requirements-browser.txt', '.github/workflows/validate.yml')]
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode() + b'\0')
        # Git text attributes normalize to LF; evidence is portable across checkouts.
        digest.update(path.read_bytes().replace(b'\r\n', b'\n') + b'\0')
    return digest.hexdigest()

def validate(qemu=False, record=False):
    checks = []
    def run(name, args, detail=''):
        start = time.monotonic()
        subprocess.run([sys.executable, *args], cwd=ROOT, check=True)
        checks.append({'name': name, 'status': 'PASS', 'seconds': round(time.monotonic() - start, 3), 'detail': detail})
    initial_digest = source_digest()
    for config in ('DEBUG', 'CHECKED', 'RELEASE'):
        run(f'build-analysis-{config}', ['scripts/build.py', '--config', config, '--host', '--analyze'], 'Clang warnings-as-errors and path-sensitive analysis')
        run(f'host-{config}', ['tests/host/test_core.py', '--config', config])
        host = json.loads((ROOT / 'build' / config.lower() / 'host-tests.json').read_text())
        checks[-1].update({k: host[k] for k in ('passed', 'total', 'stress_iterations', 'fuzz_inputs')})
        checks[-1]['detail'] = '8 workers, 200000 ownership cycles, 20000 model operations, 5000 fuzz inputs'
        run(f'pe-audit-{config}', ['tools/peinspect/inspect.py', f'build/{config.lower()}/BOOTX64.EFI', '--kernel', '--output', f'build/{config.lower()}/pe-audit.json'])
    run('tool-contracts', ['tests/host/test_tools.py'], 'PE malformed/truncated cases and 2000 mutations')
    if qemu:
        for config, memory, cpus in [('DEBUG', 128, 1), ('CHECKED', 256, 1), ('RELEASE', 512, 4)]:
            run(f'qemu-{config}-{memory}m-{cpus}cpu', ['scripts/qemu.py', '--config', config, '--memory', str(memory), '--cpus', str(cpus)], 'BSP execution only; not kernel SMP validation')
        run('build-exception-image', ['scripts/build.py', '--config', 'CHECKED', '--exception'])
        run('qemu-exception', ['scripts/qemu.py', '--config', 'CHECKED', '--exception'], 'Intentional UD2; fatal vector 6 and context required')
    else:
        checks.append({'name': 'qemu', 'status': 'NOT_RUN', 'detail': 'Pass --qemu to exercise firmware and kernel'})
    run('documentation', ['scripts/metadata.py', '--check'])
    run('website-build', ['website/scripts/build.py'])
    run('website-links', ['scripts/check_site.py'])
    if initial_digest != source_digest():
        raise RuntimeError('Sources changed during validation; report rejected')
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    except subprocess.CalledProcessError:
        commit, dirty = None, True
    result = {'schema_version': 1, 'status': 'PASS' if qemu else 'PARTIAL', 'tested_commit': commit,
              'working_tree_changes': dirty, 'source_sha256': initial_digest, 'checks': checks,
              'unexecuted': ['Windows differential contracts', 'third-party drivers', 'kernel SMP', 'real hardware'],
              'host': sys.platform,
              'toolchains': {c: json.loads((ROOT / 'build' / c.lower() / 'toolchain.json').read_text()) for c in ['DEBUG', 'CHECKED', 'RELEASE']}}
    destination = ROOT / ('data/validation.json' if record else 'build/validation.json')
    destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if record:
        # Include the newly measured evidence in the portal; no source code changes.
        subprocess.run([sys.executable, 'website/scripts/build.py'], cwd=ROOT, check=True)
        subprocess.run([sys.executable, 'scripts/check_site.py'], cwd=ROOT, check=True)
    print(f'Validation {result["status"]}: {destination}')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--qemu', action='store_true')
    p.add_argument('--record', action='store_true')
    a = p.parse_args()
    validate(a.qemu, a.record)
