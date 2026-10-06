# Foundation contract

Status: PARTIAL. Implementation evidence is maintained in `data/validation.json`.

The project is a C17 x86-64 NT-like kernel with separate internal contracts and
future NT binary-facing adapters. Internal structures are not Windows ABI
structures. No NT compatibility is implied by internal API availability.

## Boot and lifetime

The firmware loads one relocatable PE32+ EFI application containing the boot
adapter and linked kernel. This intentionally avoids a premature private PE
loader. The handoff boundary remains explicit and versioned so a separate loader
can later supply the same contract. Firmware owns the CPU until ExitBootServices.
All allocation happens before the final map/exit transaction. A stale map key
permits a bounded GetMemoryMap/ExitBootServices retry with the existing buffer.
After the first exit attempt, fatal failure halts rather than returning into
partially shut down firmware. No console/protocol call occurs inside the retry.

The map buffer, PFN metadata, image and boot stack are pinned LoaderData/Code.
Only conventional memory with acceptable attributes enters the free PFN set.
BootServices memory, ACPI, runtime, MMIO, persistent and unknown types remain
reserved. This is conservative ownership, not evidence they are unusable forever.
Firmware page tables remain pinned and active in this phase. Reclamation requires
own address space, stacks, exception infrastructure and explicit reservations.

## Physical memory

The PFN database is sparse by usable frames, not indexed by highest physical
address. Caller supplies aligned metadata storage and owns its lifetime. Boot
allocates its final backing from firmware; the kernel never uses a bump allocator.
Frames have physical address, generation, reference count and allocation state.
Allocation issues a (physical address, generation) handle. Retain requires an
existing live reference; release consumes exactly one reference. Last release
returns the frame to the free set. Stale generations and invalid addresses fail.
Generation exhaustion retires a frame, preventing wraparound ABA. Possession of
a handle alone does not authorize retaining after its last owned reference ends.

The free count and all mutable PFN fields are protected by one FIFO ticket lock
with acquire/release ordering. Initialization requires exclusive ownership;
database destruction is allowed only after all callers have quiesced. Caller
must prevent local interrupt/preemption reentry when running in the kernel.
NMI and bugcheck paths must never acquire this lock. No IRQL API is exposed yet.
The scan allocation policy is O(n); later indexed free lists can change policy
without changing ownership, generation or lifetime contracts.

The parser reads descriptor bytes without assuming input alignment, checks
stride/version, overflow, alignment, counts and overlap including reserved
descriptors. It sorts into caller storage and publishes count only on success.
On failure, output storage may be modified but is not a valid map. Capacity
limits fail explicitly; no memory range is silently truncated.

## CPU and diagnostics

The initial execution domain is the boot processor with interrupts disabled.
An owned GDT, IDT and TSS install terminal handlers for all vectors. Separate IST
stacks serve double fault, NMI and machine check. Static stacks remain pinned;
guard pages and fault recovery require the VMM milestone. The descriptor-table
transition is a short non-unwindable boot boundary. Other interrupt vectors are
not dispatched to device drivers yet.
AP startup, scheduling and NT IRQL are separate milestones. SMP correctness of
PFN mutation is tested under host concurrency; this does not validate kernel SMP.
Serial is a bounded polled 16550 transport for the QEMU PC platform. Structured
records carry subsystem, level, event and parameters. Missing thread/IRQL/process
context is marked unavailable, never fabricated. Crash records are versioned,
statically allocated, single-writer and consumable by a future dump writer.

## Failure and validation

No partial initialization is published. Firmware errors preserve the original
status. In-kernel contract violations enter a terminal diagnostic path. No
external drivers load, so no trust or signature decision is bypassed.
Tests cover malformed maps, reservation policy, exhaustion, stale handles,
reference overflow, concurrency, ABI calls and actual UEFI execution in QEMU.
The same freestanding core sources compile in hosted tests. Sanitizers and static
analysis supplement tests. Test reports identify the source tree and tool versions.
