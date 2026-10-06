# Engineering rules

This is an original x86-64 C17 kernel, not Windows source. Keep public NT-facing
contracts separate from internal structures. No fake success, disposable
allocators or unproven compatibility claims. Assembly belongs only at architecture
boundaries. No proprietary binary or credential may be committed.

Before subsystem implementation: requirements, interfaces, invariants, ownership,
lifetime, synchronization, failure cleanup, debugging and test plan. Keep design
status honest in `data/compatibility.json`. Update generated docs with
`scripts/metadata.py`. Do not manually duplicate compatibility data in the portal.

After changes: build DEBUG/CHECKED/RELEASE, run appropriate host/VM/stress/ABI
tests, Clang analysis and technical self-review. The acceptance command is
`python scripts/validate.py --qemu --record` in the development venv. Broaden tests
when changes introduce new risks. Check source digest before reusing evidence.

Before commit/push: inspect git status, diff and staged diff; run the publication
policy check; preserve user changes and existing history. Official destination:
https://github.com/marcosjm333/windows-10.git, main. No force pushes. Confirm push
and deployment independently. No requirement in this file overrides a user's
explicit decision to defer publication.
