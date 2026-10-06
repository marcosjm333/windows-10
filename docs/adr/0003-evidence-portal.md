# ADR 0003: one compatibility source and a static evidence portal

Accepted: 2026-10-05.

Keep compatibility contracts in schema-validated JSON. Generate target, roadmap,
changelog and compatibility Markdown plus the static website. Keep measured test
reports separate from implementation status: passing a narrow test must not
promote an API automatically.

The portal is static HTML/CSS with a small local script for API filters. GitHub
Pages needs no server, authentication, analytics or remote asset dependency.
Python Markdown and jsonschema are build dependencies only. The site includes
all requested routes and publishes no proprietary corpus or local absolute paths.

CI rebuilds the website after recording the results of that checkout. The
source digest covers executable sources, tests, build scripts, website sources,
compatibility data and tool requirements, with Git-style LF normalization. It
excludes its own validation report to avoid self-reference. Documentation prose
has separate freshness checks. A report for a dirty tree says so explicitly.
