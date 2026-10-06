# Novere

An independent x86-64 kernel in C, developed in the `windows-10` repository.
Its long-term objective is progressive binary compatibility with a fixed Windows
NT environment. Novere is the project's working name. It is experimental and is
not a Microsoft product or an existing Windows distribution.

## Current capabilities

The foundation transfers control from UEFI to an owned kernel stack, installs
GDT/IDT/TSS/IST exception infrastructure, validates the firmware memory map and
manages conventional frames through a sparse reference-counted PFN database.
Structured COM1 logs and terminal crash context support diagnostics. There are
no NT exports, runnable processes, Windows drivers or compatibility claims yet.

The kernel uses C17 and narrow x64 assembly, the Microsoft x64 ABI, and no host
CRT. All firmware allocations are pinned through the boot ownership boundary.
Firmware page tables remain active until the owned VMM milestone is implemented.

## Build and tests

Prerequisites: Python 3.11+, Clang/LLD 18+, CMake 3.24+, Ninja, QEMU and EDK2/OVMF.
Set `NW_LLVM_BIN` to LLVM's `bin` directory if it is not on PATH. A locally
extracted LLVM under `.tools/llvm/bin` is also detected. Kernel sources contain
no Zig or Rust. Python drives reproducible compiler/linker invocations.

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python scripts/metadata.py --check
cmake --preset checked
cmake --build --preset checked
ctest --preset checked
.venv/Scripts/python scripts/validate.py --qemu --record
```

On Linux, use `.venv/bin/python`. The direct build entrypoint works without
CMake: `python scripts/build.py --config CHECKED --host --analyze`.
`DEBUG`, `CHECKED` and `RELEASE` select O0/O1/O2 respectively, retain symbols,
retain contract checks and reject compiler warnings. CHECKED is the CI default.

## Run in an isolated VM

```powershell
python scripts/qemu.py --config CHECKED --memory 256 --cpus 1
python scripts/qemu.py --config CHECKED --debug
```

Configure `NW_QEMU`, `NW_OVMF` and `NW_OVMF_VARS` when automatic discovery does
not match your installation. Use a matching firmware code/variables pair. The
runner creates a private ESP and variables copy under `build/`, disables guest
networking, captures serial logs and never attaches a physical host disk.
The debug option pauses QEMU and binds the GDB stub to loopback port 1234.
See [building and debugging](docs/BUILDING.md).

## Documentation and compatibility

- [Foundation architecture](docs/architecture/FOUNDATION.md)
- [Subsystem contracts](docs/architecture/SUBSYSTEMS.md)
- [Invariants](docs/invariants/FOUNDATION.md)
- [Microsoft x64 ABI](docs/abi/X64.md)
- [Target: Windows 10 Pro 22H2, 19045.4046, x86-64](docs/TARGET_WINDOWS_BUILD.md)
- [Compatibility](docs/COMPATIBILITY.md), [roadmap](docs/ROADMAP.md), [changelog](CHANGELOG.md)
- [Validation and review](docs/VALIDATION.md)

`data/compatibility.json` is the editable compatibility source. Markdown and the
portal are generated from it. `data/validation.json` holds measured evidence,
including a source digest; compiling alone never promotes compatibility status.

## Official portal

Build the twelve-section portal with `.venv/Scripts/python website/scripts/build.py`.
Output lives in `website/dist`. Serve it with
`python website/scripts/serve.py` and open `http://127.0.0.1:8765/windows-10/`.
Deployment targets [GitHub Pages](https://marcosjm333.github.io/windows-10/).
That is the intended URL; deployment must be confirmed in GitHub Actions before
claiming it is available. See [publication setup](docs/DEPLOYMENT.md).

## Security, provenance and license

Original code is MIT licensed; see [LICENSE](LICENSE). Proprietary binaries remain
read-only in ignored `local/windows-build/` and are never committed or published.
Only reviewed hashes, versions, contracts and results belong in the repository.
Code Integrity, HVCI, Secure Boot and signature checks are not bypass targets.
See [SECURITY](SECURITY.md), [CONTRIBUTING](CONTRIBUTING.md) and
[public research sources](docs/research/SOURCES.md).
