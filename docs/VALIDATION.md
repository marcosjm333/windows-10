# Validation and review

Run `python scripts/validate.py --qemu --record` with the development dependencies
installed. It records command results, source digest, compiler versions, host
tests, PE audit and VM evidence. The report reflects that source tree; it must not
be relabeled as evidence for unrelated later code. `tested_commit` can be null for
an uncommitted tree; the source digest remains authoritative for local evidence.

Host tests cover map byte alignment, descriptor stride/version/length, overlap,
overflow, protected regions, sparse storage, exhaustion, stale generations,
reference overflow, ticket wrap, random model operations and concurrent live
ownership. Deterministic fuzzing is a bounded smoke corpus, not coverage-guided
fuzzing. Up to eight workers (bounded by available CPUs) execute 25,000 cycles
each; reports record the actual worker and operation count. Eight-worker local
runs exercise 200,000 alloc/retain/release cycles. This is host
SMP evidence only. Windows tests exercise the Microsoft aggregate ABI.

QEMU scenarios require serial markers from actual kernel initialization and test
execution. The exception image deliberately executes UD2 and must report vector
6. Normal images fail if a bugcheck/exception marker appears. The multi-vCPU case
only demonstrates successful BSP boot on that VM configuration.

No differential Windows tests or third-party driver tests have run. Their status
is NOT_RUN, not PASS or zero failures. Sanitizer lanes are recorded separately;
Clang static analysis does not establish absence of all memory bugs.

## Architecture and invariant self-review

The foundation uses fixed lifetime boot allocations and no reclamation before
VMM ownership. Its parser and PFN code avoid unchecked addition, mutable input
publication and generation wrap. Locking has one order and no nested blocking
path. Concurrent tests check uniqueness independently of the PFN lock. Fatal
logging drops reentrant writes rather than waiting for a suspended writer.

Review includes race/reentry, UAF/double free, pointer bounds/alignment, integer
overflow/truncation, references, lock order, starvation, cancellation, error
cleanup, interrupt safety, memory ordering, ABI, stack size and C undefined
behavior. Current context constraints are part of the contract; future callers
must not assume IRQ/preemptibility guarantees that do not exist yet.

The terminal boot state, pinned firmware mappings, bounded memory-map capacity,
unguarded static emergency stacks and absence of NT semantics are known
limitations. Remaining risk includes real firmware differences, hardware faults
during early descriptor-table transition and undetected bugs outside the test
corpus. This is an implementer's self-review, not independent approval.

## Hosted stress scheduling

The first CI attempt used eight workers even on smaller virtual runners and did
not complete promptly. It was cancelled without declaring a pass. Ticket locks
assume the owner can run: oversubscribing busy-wait workers on a hosted OS can
cause severe scheduling convoys. The harness now bounds workers by available
CPUs and enforces a timeout. The eight-worker local result remains recorded.
This is not evidence of preemption-safe kernel locking; that integration remains
an explicit scheduler/IRQL milestone.
