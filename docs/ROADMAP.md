# Roadmap

Generated from `data/compatibility.json`. Milestones are dependency gates, not date promises.

## M0: Foundation and evidence

Status: PARTIAL.

UEFI ownership transition, PFN contracts, CPU exceptions, diagnostics, host/VM tests and official portal.

## M1: Owned address space

Status: DESIGN.

Page-table manager, explicit mappings, guard pages, W^X, TLB invalidation, pools, MDLs and reservation reclamation.

## M2: Interrupts and execution

Status: DESIGN.

ACPI, APIC, timers, AP startup, per-CPU state, IRQL, scheduler and DPC.

## M3: Executive and object lifetimes

Status: DESIGN.

Processes, dispatcher waits, APC, Object Manager, handles and security primitives.

## M4: Native driver model

Status: RESEARCH.

PE loader, module lifetime, I/O, cancellation, PnP, registry and native test drivers.

## M5: Differential NT compatibility

Status: RESEARCH.

Pinned Windows corpus, legitimate intact drivers and per-contract differential evidence.

## M6: Advanced stacks and integrity

Status: UNKNOWN.

Storage, filesystems, NDIS, WDF, graphics and ci.dll with normal trust checks.
