"""Freestanding PE/COFF and shared host-core builds; no host CRT in the kernel."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CORE = ["kernel/runtime/memory.c", "kernel/memory/map.c", "kernel/memory/pfn.c",
        "boot/uefi/transaction.c"]
KERNEL = CORE + ["boot/uefi/entry.c", "kernel/executive/init.c",
                 "kernel/debug/serial.c", "kernel/debug/bugcheck.c",
                 "kernel/arch/x64/tables.c", "kernel/arch/x64/entry.S", "tests/abi/probe.S", "tests/abi/callee.c"]

def tool(name):
    suffix = ".exe" if os.name == "nt" else ""
    local = Path(os.environ.get("NW_LLVM_BIN", ROOT / ".tools/llvm/bin")) / (name + suffix)
    result = str(local) if local.is_file() else shutil.which(name)
    if not result:
        raise RuntimeError(f"Missing {name}; install LLVM 18+ or set NW_LLVM_BIN")
    return result

def run(args):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True)

def build(config, exception=False, host=False, analyze=False, sanitizer=False):
    clang, lld = tool("clang"), tool("lld-link")
    out = ROOT / "build" / config.lower()
    out.mkdir(parents=True, exist_ok=True)
    optimization = {"DEBUG": "-O0", "CHECKED": "-O1", "RELEASE": "-O2"}[config]
    common = ["-I", ROOT / "include", "-std=c17", "-Wall", "-Wextra", "-Werror",
              "-Wconversion", "-Wshadow", "-Wstrict-prototypes", "-ffreestanding",
              "-fno-builtin", "-fno-stack-protector", "-fno-omit-frame-pointer",
              "-mno-red-zone", optimization, "-g", f"-DNW_CONFIG_{config}=1"]
    target = ["--target=x86_64-pc-windows-msvc", "-mno-sse", "-mno-sse2", "-mno-mmx",
              "-fno-asynchronous-unwind-tables", "-funwind-tables", "-mno-stack-arg-probe"]
    flags = common + target
    if exception:
        flags += ["-DNW_TEST_EXCEPTION=1"]
    objects = []
    for source in KERNEL:
        obj = out / (source.replace("/", "_") + ".obj")
        run([clang, *flags, "-c", source, "-o", obj])
        objects.append(obj)
    image = out / ("exception.efi" if exception else "BOOTX64.EFI")
    run([lld, "/subsystem:efi_application", "/entry:efi_main", "/nodefaultlib",
         "/machine:x64", "/dynamicbase", "/nxcompat", "/fixed:no", "/timestamp:0",
         "/debug:dwarf", "/stack:65536", f"/out:{image}", *objects])
    if host:
        host_sources = CORE + ["tests/host/exports.c", "tests/abi/probe.S", "tests/abi/callee.c"]
        if os.name == "nt":
            host_objects = []
            for source in host_sources:
                obj = out / ("host_" + source.replace("/", "_") + ".obj")
                run([clang, *common, "--target=x86_64-pc-windows-msvc", "-DNW_HOST=1",
                     "-c", source, "-o", obj])
                host_objects.append(obj)
            run([lld, "/dll", "/noentry", "/nodefaultlib", "/machine:x64", "/export:nw_abi_probe",
                 f"/out:{out / 'nwcore.dll'}", *host_objects])
        else:
            extra = ["-fsanitize=undefined", "-fno-sanitize-recover=all"] if sanitizer else []
            run([clang, *common, "-DNW_HOST=1", "-shared", "-fPIC", *extra,
                 *host_sources, "-o", out / "libnwcore.so"])
    if analyze:
        for source in KERNEL:
            if not source.endswith(".c"):
                continue
            report = out / (source.replace("/", "_") + ".plist")
            run([clang, *flags, "--analyze", "-Xanalyzer", "-analyzer-output=plist",
                 "-o", report, source])
            import plistlib
            diagnostics = plistlib.loads(report.read_bytes())["diagnostics"]
            if diagnostics:
                raise RuntimeError(f"Static analysis findings: {source}: {diagnostics}")
    (out / ("exception-toolchain.json" if exception else "toolchain.json")).write_text(json.dumps({
        "compiler": subprocess.check_output([clang, "--version"], text=True).splitlines()[0],
        "linker": subprocess.check_output([lld, "--version"], text=True).strip(),
        "config": config, "exception_test": exception,
        "static_analysis": "PASS" if analyze else "NOT_RUN",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Built {image.relative_to(ROOT)}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", choices=["DEBUG", "CHECKED", "RELEASE"], default="CHECKED")
    p.add_argument("--host", action="store_true")
    p.add_argument("--analyze", action="store_true")
    p.add_argument("--exception", action="store_true")
    p.add_argument("--sanitizer", action="store_true")
    a = p.parse_args()
    try:
        build(a.config, a.exception, a.host, a.analyze, a.sanitizer)
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
