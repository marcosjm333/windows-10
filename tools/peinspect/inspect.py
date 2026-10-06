"""Read-only bounded PE32+ structural audit. This does not load or execute images."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

class PeError(ValueError):
    pass

def inspect(data, kernel=False):
    def need(offset, size):
        if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
            raise PeError("File range outside input")
    def u16(offset):
        need(offset, 2)
        return struct.unpack_from("<H", data, offset)[0]
    def u32(offset):
        need(offset, 4)
        return struct.unpack_from("<I", data, offset)[0]
    need(0, 64)
    if data[:2] != b"MZ":
        raise PeError("Missing DOS signature")
    pe = u32(60)
    need(pe, 24)
    if pe < 64 or data[pe:pe + 4] != b"PE\0\0" or u16(pe + 4) != 0x8664:
        raise PeError("Not an AMD64 PE image")
    count, optional_size = u16(pe + 6), u16(pe + 20)
    if not 1 <= count <= 96 or optional_size < 112:
        raise PeError("Invalid PE header sizes")
    opt = pe + 24
    need(opt, optional_size)
    if u16(opt) != 0x20b:
        raise PeError("Not PE32+")
    directories = u32(opt + 108)
    if directories > 16 or 112 + directories * 8 > optional_size:
        raise PeError("Invalid directory table")
    section_alignment, file_alignment = u32(opt + 32), u32(opt + 36)
    image_size, headers = u32(opt + 56), u32(opt + 60)
    if not (512 <= file_alignment <= 65536 and file_alignment & (file_alignment - 1) == 0):
        raise PeError("Unsupported file alignment")
    if section_alignment < file_alignment or section_alignment & (section_alignment - 1):
        raise PeError("Invalid section alignment")
    table = opt + optional_size
    need(table, count * 40)
    need(0, headers)
    if headers < table + count * 40 or headers > image_size or headers % file_alignment or image_size % section_alignment:
        raise PeError("Invalid image/header extent")
    sections, virtual_ranges, file_ranges = [], [], []
    for i in range(count):
        s = table + i * 40
        name = data[s:s + 8].split(b"\0", 1)[0].decode("ascii", errors="replace")
        size, rva, raw_size, raw = [u32(s + j) for j in (8, 12, 16, 20)]
        extent = max(size, raw_size)
        if rva % section_alignment or rva < headers or rva + extent > image_size:
            raise PeError("Section outside image or misaligned")
        if raw_size:
            need(raw, raw_size)
            if raw < headers or raw % file_alignment or raw_size % file_alignment:
                raise PeError("Invalid section file extent")
            file_ranges.append((raw, raw + raw_size))
        virtual_ranges.append((rva, rva + extent))
        flags = u32(s + 36)
        if kernel and flags & 0x20000000 and flags & 0x80000000:
            raise PeError("Writable executable image section")
        sections.append({"name": name, "rva": rva, "size": size, "raw": raw, "raw_size": raw_size,
                         "flags": flags})
    for ranges in (file_ranges, virtual_ranges):
        ordered = sorted(ranges)
        if any(a[1] > b[0] for a, b in zip(ordered, ordered[1:])):
            raise PeError("Overlapping sections")
    def rva_file(rva, size):
        if rva < headers and size <= headers - rva:
            return rva
        for s in sections:
            delta = rva - s["rva"]
            if 0 <= delta <= s["raw_size"] and size <= s["raw_size"] - delta:
                return s["raw"] + delta
        raise PeError("Directory not file-backed")
    dirs = []
    for i in range(directories):
        rva, size = u32(opt + 112 + i * 8), u32(opt + 116 + i * 8)
        if bool(rva) != bool(size):
            raise PeError("Incomplete directory pair")
        if rva:
            need(rva, size) if i == 4 else rva_file(rva, size)
        dirs.append({"index": i, "rva": rva, "size": size})
    entry = u32(opt + 16)
    if not any(s["rva"] <= entry < s["rva"] + s["raw_size"] and s["flags"] & 0x20000000 for s in sections):
        raise PeError("Entry point outside executable file-backed section")
    if kernel:
        if u16(opt + 68) != 10 or len(dirs) < 13 or dirs[1]["size"] or dirs[12]["size"]:
            raise PeError("Kernel must be an import-free EFI application")
        if not dirs[3]["size"] or not dirs[5]["size"]:
            raise PeError("Kernel needs unwind and relocation directories")
        unwind = dirs[3]
        if unwind["size"] % 12:
            raise PeError("Invalid AMD64 runtime function table")
        pos = rva_file(unwind["rva"], unwind["size"])
        previous_end = 0
        for i in range(unwind["size"] // 12):
            begin, end, info = struct.unpack_from("<III", data, pos + i * 12)
            if begin < previous_end or end <= begin or end > image_size:
                raise PeError("Invalid runtime function range")
            rva_file(info, 4)
            previous_end = end
        reloc = dirs[5]
        pos, end = rva_file(reloc["rva"], reloc["size"]), rva_file(reloc["rva"], reloc["size"]) + reloc["size"]
        while pos < end:
            if end - pos < 8:
                raise PeError("Truncated relocation block")
            page, block_size = struct.unpack_from("<II", data, pos)
            if page % 4096 or block_size < 8 or block_size % 2 or block_size > end - pos:
                raise PeError("Invalid relocation block")
            for cursor in range(pos + 8, pos + block_size, 2):
                entry = u16(cursor)
                kind, offset = entry >> 12, entry & 0xfff
                if kind not in (0, 10) or (kind == 10 and page + offset + 8 > image_size):
                    raise PeError("Unsupported or out-of-bounds relocation")
            pos += block_size
    return {"sha256": hashlib.sha256(data).hexdigest(), "machine": "AMD64", "format": "PE32+",
            "subsystem": u16(opt + 68), "image_size": image_size, "sections": sections,
            "directories": dirs, "structural_audit": "PASS"}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("file", type=Path)
    p.add_argument("--kernel", action="store_true")
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    result = json.dumps(inspect(a.file.read_bytes(), a.kernel), indent=2) + "\n"
    if a.output:
        a.output.write_text(result, encoding="utf-8")
    else:
        print(result)
