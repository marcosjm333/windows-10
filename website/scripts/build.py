"""Static portal renderer. Compatibility and documentation share one data source."""
import argparse
import html
import json
from pathlib import Path
import re
import shutil
from string import Template
import subprocess
import sys
import markdown

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from metadata import load, generate
ESC = html.escape

def badge(status):
    return f'<span class="badge {ESC(status.lower())}">{ESC(status)}</span>'

def heading(title, description, tag="ENGINEERING NOTEBOOK"):
    return f'<div class="hero"><p class="eyebrow">{ESC(tag)}</p><h1>{ESC(title)}</h1><p class="lead">{ESC(description)}</p></div>'

def table(headers, rows):
    return '<div class="table-wrap"><table><thead><tr>' + ''.join(f'<th scope="col">{ESC(h)}</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>' for row in rows) + '</tbody></table></div>'

def render_markdown(path):
    text = path.read_text(encoding="utf-8")
    # Repository Markdown links remain source links; documentation content is local.
    def link(match):
        label, target = match.groups()
        if target.startswith(("http:", "https:", "#")):
            return match.group(0)
        file = (path.parent / target).resolve()
        try:
            relative = file.relative_to(ROOT).as_posix()
        except ValueError:
            return label
        return f'[{label}](https://github.com/marcosjm333/windows-10/blob/main/{relative})'
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, text)
    return '<article class="document">' + markdown.markdown(text, extensions=["fenced_code", "tables"]) + '</article>'

def build(base="/windows-10", output=None):
    base = '/' + base.strip('/') if base.strip('/') else ''
    if not re.fullmatch(r'(?:/[a-zA-Z0-9_-]+)*', base):
        raise ValueError("Unsafe base path")
    generate(check=True)
    data = load()
    evidence = json.loads((ROOT / "data/validation.json").read_text(encoding="utf-8"))
    version = (ROOT / "VERSION").read_text().strip()
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short=10", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
        changed = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).splitlines()
        dirty = any(line[3:] != 'data/validation.json' for line in changed)
        if dirty:
            commit += " + local changes"
    except subprocess.CalledProcessError:
        commit = "uncommitted source"
    routes = json.loads((ROOT / "website/pages/routes.json").read_text())
    layout = Template((ROOT / "website/components/layout.html").read_text(encoding="utf-8"))
    out = Path(output) if output else ROOT / "website/dist"
    out.mkdir(parents=True, exist_ok=True)
    (out / "assets").mkdir(exist_ok=True)
    for source, target in [("src/style.css", "style.css"), ("src/app.js", "app.js"), ("public/favicon.svg", "favicon.svg")]:
        shutil.copyfile(ROOT / "website" / source, out / "assets" / target)
    (out / ".nojekyll").write_text("")
    (out / "data").mkdir(exist_ok=True)
    for source in ["compatibility.json", "validation.json"]:
        shutil.copyfile(ROOT / "data" / source, out / "data" / source)
    def url(route):
        return f"{base}/{route.strip('/')}/" if route else f"{base}/"
    def write(route, title, content):
        nav = ''.join(f'<a href="{url(r)}"' + (' aria-current="page"' if r == route else '') + f'>{ESC(t)}</a>' for r, t in routes)
        result = layout.substitute(title=ESC(title), base=base, navigation=nav, section=ESC(title.upper()), version=ESC(version), commit=ESC(commit), content=content)
        path = out / route / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result, encoding="utf-8", newline="\n")
    target = data["target"]
    target_string = f"{target['version']} {target['release']} {target['edition']}"
    target_build = f"{target['build']}.{target['revision']}"
    api_implemented = sum(a['status'] in {"IMPLEMENTED", "VALIDATED", "REGRESSION_TESTED"} for a in data['apis'])
    api_validated = sum(a['status'] in {"VALIDATED", "REGRESSION_TESTED"} for a in data['apis'])
    host = next((c for c in evidence.get('checks', []) if c.get('name') == 'host-CHECKED'), {})
    tests = str(host.get('passed', '—'))
    metrics = ''.join(f'<div class="metric"><strong>{value}</strong><span>{name}</span><small>{detail}</small></div>' for value, name, detail in [
        (api_implemented, 'NT APIs implemented', 'SCOPED CONTRACTS'), (api_validated, 'NT APIs validated', 'BEHAVIORAL EVIDENCE'),
        (len(data['drivers']), 'Drivers tested', 'PINNED WINDOWS TARGET'), (tests, 'Host tests passing', 'CHECKED CONFIGURATION')])
    home = '<div class="hero"><p class="eyebrow">INDEPENDENT KERNEL / PROJECT OVERVIEW</p><div class="hero-head"><h1>A foundation built<br>on explicit contracts.</h1>' + badge('PARTIAL') + '</div><p class="lead">Novere is an x86-64 kernel in C pursuing progressive Windows NT binary compatibility. Follow the architecture, inspect the contracts and see the evidence behind each milestone.</p></div>'
    home += f'<div class="metrics">{metrics}</div><div class="grid"><section class="panel"><h2>Current engineering phase</h2><p>UEFI ownership transfer, physical frame lifetimes and fatal exception handling.</p><p class="muted">The kernel has no NT exports or driver execution yet. Compatibility progresses only after the underlying contracts can be tested.</p><a href="{url("architecture")}">Explore the architecture</a><h3>Evidence on record</h3><p>{badge(evidence["status"])} <a href="{url("tests")}">Inspect validation results</a></p></section>'
    home += f'<section class="panel dark"><p class="eyebrow" style="color:#aac3ff">FIXED RESEARCH TARGET</p><h2>{ESC(target_string)}</h2><dl class="specs"><dt>Build / revision</dt><dd>{target_build}</dd><dt>Architecture</dt><dd>x86-64</dd><dt>Binary corpus</dt><dd>{target["acquisition"]}</dd><dt>Kernel toolchain</dt><dd>Clang / LLD</dd><dt>ABI</dt><dd>Microsoft x64</dd></dl></section></div>'
    home += f'<div class="section-head"><h2>Next engineering gates</h2><a href="{url("roadmap")}">Full roadmap</a></div><section class="panel">'
    for m in data['milestones'][:3]:
        home += f'<div class="phase"><span class="phase-id">{m["id"]}</span><div><h3>{ESC(m["title"])}</h3><p>{ESC(m["deliverables"])}</p>{badge(m["status"])}</div></div>'
    write('', 'Overview', home + '</section>')
    content = heading('Kernel architecture', 'Internal contracts remain separate from the future Windows binary interface.')
    layers = [('NT adapters', 'Build-specific ABI and behavioral contracts. No exports implemented.'), ('Executive', 'Objects, processes, waits, I/O and security. Design and research.'), ('Kernel mechanisms', 'Physical frames and terminal exceptions exist. Scheduling and virtual memory are pending.'), ('x64 / HAL', 'GDT, IDT, TSS, IST and serial diagnostics. APIC, SMP and timers are pending.'), ('UEFI handoff', 'Versioned boot information and a bounded ExitBootServices transaction.')]
    content += '<ol class="architecture">' + ''.join(f'<li><strong>{ESC(a)}</strong><span>{ESC(b)}</span></li>' for a, b in layers) + '</ol>'
    content += render_markdown(ROOT / 'docs/architecture/FOUNDATION.md')
    write('architecture', 'Architecture', content)
    content = heading('Compatibility by subsystem', 'Status describes the declared scope. A successful build is not binary compatibility.')
    content += '<div class="legend">' + ''.join(badge(s) for s in data['statuses']) + '</div>'
    content += table(['Subsystem', 'Status', 'Current scope'], [[ESC(s['name']), badge(s['status']), ESC(s['notes'])] for s in data['subsystems']])
    content += f'<p class="notice">Source of truth: <a href="{base}/data/compatibility.json">compatibility.json</a>. This also generates the technical compatibility document.</p>'
    write('compatibility', 'Compatibility', content)
    content = heading('NT API registry', 'Inspect prototypes, IRQL constraints, missing behavior and validation history. No API below is exported by the kernel.')
    options = ''.join(f'<option value="{s}">{s}</option>' for s in data['statuses'])
    subs = ''.join(f'<option value="{s["id"]}">{ESC(s["name"])}</option>' for s in data['subsystems'])
    content += f'<div class="filters"><label>Search contracts<input id="api-search" type="search" placeholder="Name, prototype or behavior" autocomplete="off"></label><label>Status<select id="api-status"><option value="">All statuses</option>{options}</select></label><label>Subsystem<select id="api-subsystem"><option value="">All subsystems</option>{subs}</select></label></div><p id="result-count" aria-live="polite">{len(data["apis"])} known API contracts</p>'
    content += '<div class="table-wrap"><table><thead><tr><th scope="col">API / contract</th><th scope="col">Subsystem</th><th scope="col">Status</th><th scope="col">IRQL</th></tr></thead><tbody>'
    for a in data['apis']:
        search = ESC(' '.join([a['name'], a['prototype'], a['notes'], a['blocking']]).lower(), quote=True)
        content += f'<tr data-api-row data-search="{search}" data-status="{a["status"]}" data-subsystem="{a["subsystem"]}"><td><code>{ESC(a["name"])}</code><details><summary>Inspect contract</summary><pre>{ESC(a["prototype"])}</pre><dl>'
        for label, value in [('Blocking', a['blocking']), ('Tests', ', '.join(a['tests']) or 'Not run'), ('Known callers', ', '.join(a['known_callers']) or 'Not established'), ('Last validated commit', a['last_validated_commit'] or 'None'), ('Notes', a['notes'])]:
            content += f'<dt>{label}</dt><dd>{ESC(value)}</dd>'
        content += f'</dl><a href="{ESC(a["source"], quote=True)}">Public contract source</a></details></td><td>{a["subsystem"]}</td><td>{badge(a["status"])}</td><td>{ESC(a["irql"])}</td></tr>'
    content += '</tbody></table></div><div id="no-results" class="empty" hidden>No contracts match these filters. Change the search or select all statuses.</div><noscript><p>All contracts are shown. Enable JavaScript to search and filter.</p></noscript>'
    write('compatibility/apis', 'NT API registry', content)
    content = heading('Driver registry', 'Test results belong to an exact binary hash, Windows target and kernel revision.')
    if not data['drivers']:
        content += '<div class="empty"><p class="eyebrow">NO DRIVER EVIDENCE YET</p><h2>No drivers have been tested.</h2><p>The driver loader, I/O manager and NT contracts must exist before legitimate binaries can be tested intact. A successful UEFI boot does not count as a driver test.</p></div>'
    else:
        content += table(['Driver', 'Vendor / version', 'Target / SHA-256', 'Load / entry', 'Runtime / failure', 'Commit'], [[ESC(d['name']), ESC(d['vendor'] + ' / ' + d['version']), ESC(d['windows_build']) + '<br><code>' + d['sha256'] + '</code>', ESC(d['load_result'] + ' / ' + d['driver_entry_result']), ESC(d['runtime_status'] + ' / ' + d['failure_reason']), ESC(d['last_tested_commit'] or 'None')] for d in data['drivers']])
    content += '<h2>Recorded for each future test</h2><p>Name, vendor, version, SHA-256, Windows build, load result, DriverEntry result, runtime status, failure reason and last tested commit. Proprietary binaries remain outside the published repository.</p>'
    write('compatibility/drivers', 'Driver registry', content)
    write('roadmap', 'Roadmap', heading('Roadmap', 'Dependency gates with explicit acceptance criteria. Dates are not evidence.') + render_markdown(ROOT / 'docs/ROADMAP.md'))
    content = heading('Builds and artifacts', 'Development images and their validation evidence. No production release is available.')
    content += '<section class="panel"><h2>Build configurations</h2>' + table(['Configuration', 'Optimization', 'Checks / symbols'], [['DEBUG', 'O0', 'Contract checks and debug symbols'], ['CHECKED', 'O1', 'Contract checks, static analysis and CI validation'], ['RELEASE', 'O2', 'Contract checks and debug symbols retained']])
    content += '<p class="notice">Download only artifacts produced by a successful workflow for the intended revision. No Windows or third-party driver binaries are distributed.</p><a href="https://github.com/marcosjm333/windows-10/actions">View workflow runs and artifacts</a></section>'
    write('builds', 'Builds', content)
    docs = sorted((ROOT / 'docs').rglob('*.md'))
    content = heading('Technical documentation', 'Contracts, invariants, research sources and reproducible development instructions.') + '<div class="doc-list">'
    for path in docs:
        route = 'docs/' + path.relative_to(ROOT / 'docs').with_suffix('').as_posix().lower()
        title = path.read_text(encoding='utf-8').splitlines()[0].lstrip('# ')
        content += f'<a href="{url(route)}">{ESC(title)}<small>{ESC(path.relative_to(ROOT).as_posix())}</small></a>'
        write(route, title, render_markdown(path))
    write('docs', 'Documentation', content + '</div>')
    write('development', 'Development', heading('Build with explicit contracts', 'A change is complete only when its implementation, evidence and documentation agree.') + render_markdown(ROOT / 'CONTRIBUTING.md') + '<h2>Build and debug</h2>' + render_markdown(ROOT / 'docs/BUILDING.md'))
    content = heading('Test evidence', 'Measured results are tied to a source digest. Unexecuted tests remain unexecuted.')
    content += f'<p>{badge(evidence["status"])} <span class="muted">Recorded validation state</span></p>'
    content += '<dl class="specs"><dt>Tested commit</dt><dd>' + ESC(evidence.get('tested_commit') or 'Uncommitted tree; see digest') + '</dd><dt>Source SHA-256</dt><dd>' + ESC(evidence.get('source_sha256') or 'Not recorded') + '</dd></dl>'
    content += '<ul class="evidence-list">'
    for check in evidence.get('checks', []):
        detail = check.get('detail', '')
        if 'total' in check:
            detail = f"{check.get('passed', 0)} / {check['total']} tests; " + detail
        content += f'<li><div>{ESC(check["name"])}<small>{ESC(detail)}</small></div>{badge(check["status"])}</li>'
    content += '</ul><p class="notice">Windows differential testing and third-party driver testing: NOT_RUN. Multi-vCPU VM boot does not establish kernel SMP support.</p>'
    write('tests', 'Test evidence', content)
    content = heading('Project status', 'An experimental foundation with an explicit boundary around what exists.')
    content += table(['Area', 'Current state'], [['Kernel', 'Foundation / PARTIAL'], ['NT APIs implemented', str(api_implemented)], ['NT APIs validated', str(api_validated)], ['Drivers tested', str(len(data['drivers']))], ['Target', ESC(target_string + ' ' + target_build)], ['Validation record', badge(evidence['status'])]])
    content += '<h2>Known limitations and remaining risk</h2><ul class="risk-list">' + ''.join(f'<li>{ESC(x)}</li>' for x in data['known_limitations']) + '</ul>'
    content += '<p class="notice">No separate confirmed open defect is currently recorded. This is not a claim that the kernel is bug-free. Review scope and untested behavior are documented.</p>'
    write('status', 'Project status', content)
    write('changelog', 'Changelog', heading('Changelog', 'Coherent development milestones, with no implied production-readiness claim.') + render_markdown(ROOT / 'CHANGELOG.md'))
    (out / '404.html').write_text((out / 'index.html').read_text(encoding='utf-8').replace('A foundation built<br>on explicit contracts.', 'Page not found.'), encoding='utf-8')
    print(f"Website built: {len(routes)} portal routes + {len(docs)} documentation routes -> {out}")
    return out

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--base', default='/windows-10')
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    build(a.base, a.output)
