"""Boot only an isolated directory-backed ESP; no host block device passthrough."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

def locate(env, candidates):
    value = os.environ.get(env)
    if value:
        candidates = [value]
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return path.resolve()
    raise RuntimeError(f"Missing {env}; set it to a valid local path")

def smoke(config="CHECKED", memory=256, cpus=1, exception=False, debug=False):
    qemu = locate("NW_QEMU", [shutil.which("qemu-system-x86_64") or "missing",
                               "C:/Program Files/qemu/qemu-system-x86_64.exe"])
    firmware = locate("NW_OVMF", ["C:/Program Files/qemu/share/edk2-x86_64-code.fd",
                                   "/usr/share/OVMF/OVMF_CODE_4M.fd", "/usr/share/OVMF/OVMF_CODE.fd"])
    out = ROOT / "build" / config.lower()
    test_id = f"{'exception' if exception else 'boot'}-{memory}m-{cpus}cpu"
    esp = out / test_id / "esp"
    target = esp / "EFI/BOOT/BOOTX64.EFI"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(out / ("exception.efi" if exception else "BOOTX64.EFI"), target)
    serial = (out / test_id / "serial.log").resolve()
    # Truncate evidence from a previous run before starting a new VM.
    serial.write_bytes(b"")
    variables_template = locate("NW_OVMF_VARS", ["C:/Program Files/qemu/share/edk2-i386-vars.fd",
                     "/usr/share/OVMF/OVMF_VARS_4M.fd", "/usr/share/OVMF/OVMF_VARS.fd"])
    variables = out / test_id / "vars.fd"
    shutil.copyfile(variables_template, variables)
    args = [str(qemu), "-machine", "q35,accel=tcg", "-cpu", "qemu64", "-m", str(memory),
            "-smp", str(cpus), "-drive", f"if=pflash,format=raw,readonly=on,file={firmware}",
            "-drive", f"if=pflash,format=raw,file={variables.resolve()}", "-drive",
            f"format=raw,file=fat:rw:{esp.resolve()}", "-display", "none", "-monitor", "none",
            "-serial", f"file:{serial}", "-net", "none", "-no-reboot", "-no-shutdown"]
    if debug:
        args += ["-S", "-gdb", "tcp:127.0.0.1:1234"]
        print("GDB paused at boot on 127.0.0.1:1234; Ctrl+C to stop.")
        subprocess.run(args, check=True)
        return
    required = ["event=KERNEL_ENTER", "event=TABLES_READY", "event=PFN_SELFTEST_PASS", "event=ABI_SELFTEST_PASS"]
    required += ["event=EXCEPTION a=0x0000000000000006"] if exception else ["event=FOUNDATION_READY"]
    started = time.monotonic()
    with (out / test_id / "qemu.log").open("wb") as errors:
        process = subprocess.Popen(args, stdout=errors, stderr=errors)
        output = ""
        try:
            deadline = started + 60
            while time.monotonic() < deadline:
                output = serial.read_text(errors="replace")
                if all(marker in output for marker in required):
                    break
                if process.poll() is not None:
                    break
                time.sleep(0.2)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
    passed = all(marker in output for marker in required)
    if not exception and ("event=BUGCHECK" in output or "event=EXCEPTION" in output):
        passed = False
    record = {"test": test_id, "status": "PASS" if passed else "FAIL", "memory_mib": memory,
              "virtual_cpus": cpus, "active_kernel_cpus": 1,
              "seconds": round(time.monotonic() - started, 3), "markers": required,
              "firmware_sha256": __import__("hashlib").sha256(firmware.read_bytes()).hexdigest()}
    (out / test_id / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record))
    if not passed:
        print(output[-8000:])
        raise RuntimeError(f"QEMU contract failed; inspect {out / test_id}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="CHECKED")
    p.add_argument("--memory", type=int, default=256)
    p.add_argument("--cpus", type=int, default=1)
    p.add_argument("--exception", action="store_true")
    p.add_argument("--debug", action="store_true")
    a = p.parse_args()
    smoke(a.config, a.memory, a.cpus, a.exception, a.debug)
