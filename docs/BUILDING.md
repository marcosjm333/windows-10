# Build, execution and debugging

The freestanding target is `x86_64-pc-windows-msvc`. LLD emits PE32+ EFI application
images; it resolves every symbol without a default library or host CRT. Kernel C
does not use SSE/MMX; the compiler emits unwind tables, frame pointers and debug
symbols. Boot transition and terminal exception assembly are explicit unwind
boundaries. No source pretends to implement SEH or a runtime unwinder.

`python scripts/build.py --config CHECKED --host --analyze` builds the EFI image,
host-core test library, and runs Clang's path-sensitive static analyzer. This is
the implementation behind CMake's targets, so the two paths do not drift.
Host libraries on Windows use the same Microsoft ABI. Linux hosted exports use
the platform ABI, while the dedicated C-to-assembly probe uses `ms_abi`.

Build outputs are `build/debug`, `build/checked` and `build/release`. No generated
binary is source-controlled. `.tools`, `.venv`, disk images and Windows test inputs
are ignored. LLVM 21.1.8 was used for local validation; CI records its compiler.
The official LLVM installer SHA-256 used locally was
`7a5386c26497db1691f320121e5b113364dd0274b98e55f15f4dbc00c0450113`.

## VM and serial

The QEMU runner uses q35, software emulation and a private FAT ESP, with an OVMF
pflash code image and copied variables image. It supports 128 MiB and larger
test configurations. The firmware must admit the project's development EFI
image. No host firmware security setting is changed by the runner.

Serial logs live in `build/<config>/<scenario>/serial.log`. Records contain a
monotonic event sequence, category, level, event name and two unsigned parameters.
CPU is `boot`, and thread, IRQL and timestamp are `NA` until those facilities
exist. Do not interpret event sequence as elapsed time. Transport polling is
bounded; unavailable serial stops output. Concurrent/reentrant records are dropped
and counted instead of spinning on an interrupted writer.

`--debug` enables `-S` and a loopback GDB stub. Keep ELF/COFF-aware symbol tools
available; firmware relocation means runtime image base must be discovered before
setting symbolic breakpoints. Inspect the serial transcript and relocated image
addresses, and use LLVM objdump/readobj against the matching EFI image.

## Toolchain provisioning

On Ubuntu: install `clang lld cmake ninja-build qemu-system-x86 ovmf`, then create
a Python venv and install `requirements-dev.txt`. For the LLVM 21 lane, install
versioned clang/lld packages and set `NW_LLVM_BIN` accordingly.
On Windows: use the official LLVM 21 package, CMake/Ninja and QEMU with EDK2.
The scripts detect the local `.tools/llvm/bin` extraction and QEMU's standard
installation path. CMake and Ninja must be on PATH when using presets.
