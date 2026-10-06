# PE32+ structural inspector

`python tools/peinspect/inspect.py build/checked/BOOTX64.EFI --kernel`

Read-only audit of AMD64 PE32+ headers, sections, directory extents, entry point,
runtime-function ranges and relocation blocks. Kernel mode also rejects imports,
missing relocation/unwind tables and sections combining write and execute flags.
Firmware page permissions are not proven by image flags.

This is not an import resolver or a driver loader. General images using unusual
alignment or directory layouts may be rejected. Import/export contents, recursive
forwarders, unwind opcode semantics, signatures and certificate chains are not
validated yet. No image is executed by this tool.
