# ADR 0001: durable foundation and explicit capability boundaries

Accepted: 2026-10-05.

Use C17 and Clang targeting x86_64-pc-windows-msvc with LLD, no host CRT, no red
zone and no floating point in kernel C. Microsoft x64 calling convention applies
to every compiled kernel function. Assembly is limited to privileged operations,
stack transfer and ABI probes. `clang-cl` uses the same backend but its MSVC-style
driver flags add no benefit to this cross-platform CMake build.

Keep the boot adapter and kernel linked into one firmware-loadable PE image until
a fully checked loader is available. Firmware relocation is not a kernel PE
loader implementation. Keep boot memory pinned until an owned virtual address
space makes reclaim safe. Do not export NT APIs until their required subsystems
exist. Adopt MIT for original code; third-party binaries retain their own terms.

Use JSON in `data/` as the sole editable compatibility source. Generate website
and Markdown from it. Validation reports are separate evidence, never invented
counts. GitHub Pages hosts static output from the same validation workflow.

Alternatives rejected: disposable allocator, success-returning NT stubs, copying
foreign kernel layouts into internal objects, and manually duplicated dashboards.
