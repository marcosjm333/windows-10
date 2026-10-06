"""Validate the sole compatibility source and render its Markdown projections."""
import argparse
import json
from pathlib import Path
import sys
import jsonschema

ROOT = Path(__file__).resolve().parents[1]

def load():
    data = json.loads((ROOT / "data/compatibility.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "data/compatibility.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(data)
    subsystems = {item["id"] for item in data["subsystems"]}
    if len(subsystems) != len(data["subsystems"]):
        raise ValueError("Duplicate subsystem identifier")
    if len({a['name'] for a in data['apis']}) != len(data['apis']):
        raise ValueError("Duplicate API name")
    for api in data["apis"]:
        if api["subsystem"] not in subsystems:
            raise ValueError(f"Unknown subsystem: {api['name']}")
        if api["status"] in {"VALIDATED", "REGRESSION_TESTED"} and (
                not api["tests"] or not api["last_validated_commit"]):
            raise ValueError("Validated API needs tests and a commit")
        if api["status"] == "STUB" and not api["notes"]:
            raise ValueError("Stub needs a missing-behavior description")
    target = data["target"]
    expected = f"{target['build']}.{target['revision']}"
    for record in data["binaries"] + data["drivers"]:
        if record["windows_build"] != expected:
            raise ValueError("Mixed Windows builds are forbidden")
    return data

def projections(data):
    t = data["target"]
    target = f"""# Target Windows build

Generated from `data/compatibility.json`; do not edit this projection.

- Windows version: {t['version']} {t['release']}
- Edition: {t['edition']}
- Build: {t['build']}
- Revision: {t['revision']}
- Architecture: {t['architecture']}
- Corpus acquisition: {t['acquisition']}

This is a fixed research target, not a claim about the Windows installation on
the development host. No proprietary binaries are present in the repository.
No binary hashes are invented. Populate `binaries` only after lawful acquisition,
read-only SHA-256 inventory and provenance checks against this exact installation.
Version resources alone do not prove a component's servicing origin.

[Microsoft servicing reference]({t['source']}).
"""
    compatibility = "# Compatibility\n\nGenerated from `data/compatibility.json`.\n\n"
    compatibility += "| Subsystem | Status | Scope |\n| --- | --- | --- |\n"
    for s in data["subsystems"]:
        compatibility += f"| {s['name']} | {s['status']} | {s['notes']} |\n"
    compatibility += "\n## NT API contracts\n\n"
    for api in data["apis"]:
        compatibility += f"### {api['name']}\n\n```c\n{api['prototype']}\n```\n\n"
        compatibility += f"Status: {api['status']}. IRQL: {api['irql']}\n\n{api['blocking']}\n\n{api['notes']}\n\n[Contract source]({api['source']}).\n\n"
    compatibility += f"Drivers tested: {len(data['drivers'])}. Proprietary binary inventory: {len(data['binaries'])}.\n"
    roadmap = "# Roadmap\n\nGenerated from `data/compatibility.json`. Milestones are dependency gates, not date promises.\n\n"
    for m in data["milestones"]:
        roadmap += f"## {m['id']}: {m['title']}\n\nStatus: {m['status']}.\n\n{m['deliverables']}\n\n"
    changelog = "# Changelog\n\nGenerated from `data/compatibility.json`. Development versions are not releases.\n\n"
    for entry in data["changelog"]:
        changelog += f"## {entry['version']} — {entry['date']}\n\n"
        changelog += "".join(f"- {change}\n" for change in entry['changes']) + "\n"
    return {"docs/TARGET_WINDOWS_BUILD.md": target, "docs/COMPATIBILITY.md": compatibility,
            "docs/ROADMAP.md": roadmap, "CHANGELOG.md": changelog}

def generate(check=False):
    for name, content in projections(load()).items():
        content = content.rstrip() + '\n'
        path = ROOT / name
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise ValueError(f"Generated documentation is stale: {name}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    print("Compatibility schema and documentation: PASS")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    try:
        generate(p.parse_args().check)
    except (ValueError, jsonschema.ValidationError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
