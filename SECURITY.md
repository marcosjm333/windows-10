# Security policy

Novere is experimental kernel research, not a hardened operating system.
Use isolated disposable VMs with no sensitive guest data or host disk passthrough.
No release currently has a production security support commitment.

Use GitHub's private vulnerability reporting on the official repository when
available. If it is unavailable, contact the owner privately before disclosing
exploit details. Public issues may describe non-sensitive reliability bugs.
Do not include credentials, proprietary binaries, personal dumps or private keys.

Code Integrity and signature validation must retain their normal trust model.
No patches to ci.dll, HVCI, PatchGuard or Secure Boot, signature falsification or
unauthorized loading mechanisms are acceptable contributions. The unsigned
development image is tested in an isolated development OVMF VM. This does not
change host firmware policy; secure-boot admission and signing remain future work.

Treat firmware tables, PE files, driver requests, lengths and counts as untrusted
at their subsystem boundary. Kernel memory-corruption fixes need regression tests,
failure cleanup review and explicit compatibility-impact notes.
