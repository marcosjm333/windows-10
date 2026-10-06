# Contributing

Correctness, architecture, validation, debuggability and stability precede
performance and compatibility. Keep internal contracts separate from NT ABI
adapters. No proprietary code, binaries, credentials or patched Windows files.

Before implementation, document requirements, ownership, lifetime, invariants,
locking order, failure behavior, debugging and tests. Record architectural
decisions in `docs/adr/`. A compatibility export is not implemented merely because
a binary resolves its symbol. Prefer an absent export over silent fake success.

Use UNKNOWN, RESEARCH, DESIGN, STUB, PARTIAL, IMPLEMENTED, VALIDATED,
REGRESSION_TESTED or BROKEN. IMPLEMENTED describes complete scoped behavior;
VALIDATED requires documented evidence across the agreed cases. A regression
claim additionally requires historical regression coverage. Stubs, if unavoidable,
must log calls, describe missing behavior and known callers, and fail explicitly.

Use a feature branch for experimental changes. Submit coherent commits. Before
committing, review `git status`, `git diff` and `git diff --cached`; run the
validation suite; inspect staged files for private material and large artifacts.
Do not force-push main. Document failures instead of changing tests to hide them.

Every important change needs implementation, invariant and architecture review:
race/reentry, ownership, UAF/double release, overflow/truncation, alignment, ABI,
lock order/deadlock/starvation, cancellation, rollback, interrupt safety, memory
ordering, SMP, stack bounds and C undefined behavior. Ask: is it correct, or does
it only appear to work? Reviews by the implementing agent are self-reviews, not
independent approval. Independent review is still required for production use.

Run `scripts/metadata.py` after data changes and commit the generated Markdown.
Update the portal, known limitations and validation evidence in the same logical
change. Do not label unexecuted driver or differential tests as passing.
