# ADR 0002: sparse physical frame ownership

Accepted: 2026-10-05.

Store metadata for eligible conventional frames in a sorted sparse array. A
single ticket lock protects reference/generation transitions; handles include
physical address and generation. This supports durable ownership without a
discardable early bump allocator or metadata proportional to MMIO holes.

The allocation policy scans from a rotating cursor. This is correct but has O(n)
worst-case cost and one shared lock. A later free bitmap, buddy index or per-node
cache may accelerate selection while preserving handle validation and lifetime.
Such a change needs new SMP and pressure tests. Contiguous allocation, DMA zones,
zeroed-page guarantees, NUMA and reclaim are not part of the current API.

Initialization receives externally allocated final metadata and publishes the
database only after validating all ranges and capacity. Firmware-backed metadata
is LoaderData, so it cannot enter its own free set. No boot-services memory is
reclaimed until the kernel owns page tables and can prove reservation lifetimes.
