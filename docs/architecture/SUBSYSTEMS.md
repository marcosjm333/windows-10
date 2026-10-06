# Subsystem design contracts

These are initial contracts, not completed implementation designs. Detailed data
layouts, proofs, failure matrices and test plans are mandatory before coding each
subsystem. Status is authoritative in `data/compatibility.json`.

## Virtual memory and pools

An address-space object owns page-table frames and its active-CPU mask. A mapping
owns references to backing frames. Unmap invalidates translations on every CPU
that can use the space; an acknowledgement barrier precedes frame reuse. Deferred
TLB generations cover CPUs entering an address space concurrently with unmap.
Never release a page table while a hardware walker can reach it. Separate MMIO
cache policy from RAM policy. W^X, nonpaged pools, stack guard pages and MDL pin
counts are required before admitting third-party code. Paged allocation may sleep;
nonpaged allocation reports pressure without violating interrupt constraints.

## CPU, IRQL and scheduling

Per-CPU state owns current thread, current interrupt priority, ready queues,
timer state and DPC queues. IRQL must control real interrupt masking and scheduler
preemption; a standalone integer is insufficient. AP startup publishes online
state only after stack, GDT, IDT, TSS, page tables and local APIC are ready.

Thread states: NEW, READY, RUNNING, WAITING, TERMINATING, DEAD. Exactly one CPU
owns a RUNNING thread. Queue ownership is transferred under the relevant queue
lock. Migration locks CPUs in ascending logical ID order. Priority queues use
bounded quanta, explicit affinity and documented starvation prevention. Idle
threads are real per-CPU threads. Context switch preserves ABI and architectural
state; no sleeping under spinlocks. The current terminal boot loop is not one of
these states and must not be counted as a scheduler implementation.

## Dispatcher and APC/DPC

A wait block holds references to its target objects and waiting thread until
completion. Signal, timeout, alert, cancellation and termination compete for one
completion transition. Queue insertion and releasing the run queue must not lose
a wakeup. Define signal consumption separately for events, mutexes and semaphores.
Order multi-object locks by stable object identity. Dequeue and wakeup must not
execute arbitrary callbacks while holding dispatcher locks.

DPC ownership transfers from producer to per-CPU queue to consumer. Cancellation
must distinguish queued from executing callbacks. Cross-CPU enqueue requires an
IPI and release/acquire publication. APCs belong to a live thread and have distinct
kernel/user delivery rules, disable counts and rundown behavior. Alertable waits
cannot be implemented until those interactions are testable.

## Objects, processes and threads

An internal object header owns a type reference, body lifetime, security hook,
pointer reference count and handle count. Internal layout is never assumed to
match Windows private headers. Names and namespace links hold references;
deletion unlinks first and performs type cleanup after the last reference and
rundown completion. Handle-table entries use generation checks and access masks.
No destructor runs while holding namespace or handle-table locks.

A process owns its address space, token and handle table. Threads hold process
references; termination prevents new work, cancels waits, performs APC rundown and
releases the stack only after no CPU can execute it. Quotas and rollback are part
of creation, not later compatibility fixes.

## PE and modules

Parsing yields an immutable validated image plan before mapping. File offsets and
RVAs are separate types at the API boundary. Check all extents, overlap, alignment,
relocations, imports, exports, forwarder cycles and unwind opcodes. Admission and
signature policy precede execution. Map writable staging pages, relocate/resolve,
register unwind and publish W^X mappings transactionally. Each dependency has a
module reference. Unload waits for execution/callback rundown and reverses every
publication step. A file accepted by the structural inspection tool is not yet
safe to load.

## I/O and PnP

Driver and device objects own dispatch tables and stable attachment references.
IRPs have explicit CREATED, DISPATCHED, PENDING, COMPLETING, COMPLETED and
CANCELLED transitions; cancellation and completion elect one owner. Stack
locations are bounded, completion runs in reverse order and may stop unwinding.
Do not free an IRP while any driver retains ownership. Pending propagation and
cleanup/cancel races require differential test drivers before NT exposure.

Device-tree nodes own PDO/FDO/filter references. Enumerated, started, stopping,
stopped, surprise-removed and removed transitions gate I/O and power requests.
Removal drains references, queued work and interrupt callbacks before release.
Device binding must use explicit IDs and supported resource descriptors.

## Registry, security and power

Registry handles own key references and access rights. Values are typed and
length-bounded; concurrent deletion uses rundown. Notifications hold cancellable
subscriptions and are delivered outside namespace locks. Persistence requires
transaction and recovery design before exposing durable semantics.

Tokens, SIDs, ACLs and security descriptors are validated representations with
immutable sharing where possible. Access checks return a decision derived from
requested rights and policy; unknown policy fails explicitly. Code Integrity
integration preserves normal trust, with no substitute allow-all path.

Power operations coordinate device quiescence, DMA completion, interrupt masking
and resume restoration. Suspend is not available until every participating
subsystem can restore its owned state.
