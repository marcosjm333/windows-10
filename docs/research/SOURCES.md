# Public technical sources

Consulted 2026-10-05. No proprietary source code is used.

- [UEFI 2.10A boot services](https://uefi.org/specs/UEFI/2.10_A/07_Services_Boot_Services.html): memory descriptors, allocation, map keys and ExitBootServices.
- [Microsoft x64 calling convention](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention): register arguments, shadow store, nonvolatile registers and unwind requirements.
- [PE/COFF](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format): PE32+ headers and image directories.
- [Clang manual](https://clang.llvm.org/docs/UsersManual.html): freestanding targets and compiler diagnostics.
- [Intel manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html): privileged CPU operations; consult relevant chapters before architecture changes.
- [GitHub Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages): artifact and deployment permissions.

Public documentation establishes requirements; local test evidence establishes
only the behavior actually exercised. Target Windows differential tests are
required before claiming NT behavioral compatibility.
