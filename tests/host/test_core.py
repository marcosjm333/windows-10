"""Contract, boundary, model, ABI and concurrent ownership tests of real C code."""
import argparse
import concurrent.futures
import ctypes as C
import json
import os
from pathlib import Path
import random
import struct
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
U64, U32, SIZE = C.c_uint64, C.c_uint32, C.c_size_t
OK, INVALID, RANGE, CAPACITY, CORRUPT, EXHAUSTED, STALE, OVERFLOW = range(8)
EFI_ERROR = 1 << 63
AVAILABLE_CPUS = len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else (os.cpu_count() or 1)
STRESS_WORKERS = min(8, AVAILABLE_CPUS)
STRESS_ITERATIONS = 25000

class Range(C.Structure):
    _fields_ = [("base", U64), ("pages", U64), ("attributes", U64), ("type", U32), ("reserved", U32)]
class Pfn(C.Structure):
    _fields_ = [("physical", U64), ("generation", U64), ("references", U32), ("retired", U32)]
class Frame(C.Structure):
    _fields_ = [("physical", U64), ("generation", U64)]
class Lock(C.Structure):
    _fields_ = [("next", U32), ("serving", U32)]
class Database(C.Structure):
    _fields_ = [("lock", Lock), ("entries", C.POINTER(Pfn)), ("count", SIZE), ("free_count", SIZE), ("cursor", SIZE)]
GETMAP = C.CFUNCTYPE(U64, C.POINTER(SIZE), C.c_void_p, C.POINTER(SIZE), C.POINTER(SIZE), C.POINTER(U32))
EXIT = C.CFUNCTYPE(U64, C.c_void_p, SIZE)
class Transaction(C.Structure):
    _fields_ = [("get_map", GETMAP), ("exit_boot", EXIT), ("image", C.c_void_p), ("buffer", C.c_void_p),
                ("capacity", SIZE), ("length", SIZE), ("stride", SIZE), ("version", U32), ("attempts", U32),
                ("exit_attempted", C.c_bool), ("exited", C.c_bool)]
class Aggregate(C.Structure):
    _fields_ = [("a", U64), ("b", U64), ("c", U64)]

def descriptor(base, pages=1, kind=7, attr=8, stride=48):
    return struct.pack("<IIQQQQ", kind, 0, base, 0, pages, attr) + bytes(stride - 40)

class Contracts(unittest.TestCase):
    def parse(self, data, stride=48, version=1, capacity=16, offset=0):
        raw = C.create_string_buffer(bytes(offset) + data)
        output = (Range * max(1, capacity))()
        count = SIZE(999)
        status = lib.nw_map_parse(C.byref(raw, offset), len(data), stride, version, output, capacity, C.byref(count))
        return status, output, count.value

    def database(self, count=64):
        ranges = (Range * 1)(Range(0x100000, count, 8, 7, 0))
        storage, db = (Pfn * count)(), Database()
        self.assertEqual(lib.nw_pfn_init(C.byref(db), storage, count, ranges, 1), OK)
        return db, storage

    def test_map_sort_unaligned_extended_stride(self):
        s, out, n = self.parse(descriptor(0x5000) + descriptor(0x1000, 2), offset=1)
        self.assertEqual((s, n), (OK, 2))
        self.assertEqual([out[i].base for i in range(n)], [0x1000, 0x5000])

    def test_map_rejects_bad_shape(self):
        good = descriptor(0x1000)
        for data, stride, version in [(b"", 48, 1), (good[:-1], 48, 1), (good, 32, 1),
                                       (good, 47, 1), (good, 48, 2)]:
            self.assertEqual(self.parse(data, stride, version)[0], INVALID)
        self.assertEqual(self.parse(good, capacity=0)[0], CAPACITY)

    def test_map_overflow_alignment_and_overlap(self):
        for data in [descriptor(1), descriptor(0x1000, 0), descriptor(0xfffffffffffff000),
                     descriptor(0, 1 << 63)]:
            self.assertEqual(self.parse(data)[0], RANGE)
        self.assertEqual(self.parse(descriptor(0x1000, 3) + descriptor(0x2000, kind=0))[0], CORRUPT)
        self.assertEqual(self.parse(descriptor(0x1000) * 2)[0], CORRUPT)

    def test_map_fuzz_rejects_untrusted_bytes(self):
        rng = random.Random(20261005)
        for _ in range(5000):
            raw = rng.randbytes(rng.randrange(0, 200))
            s, _, count = self.parse(raw)
            self.assertIn(s, (INVALID, RANGE, CORRUPT, CAPACITY, OK))
            if s != OK:
                self.assertEqual(count, 0)

    def test_reservations(self):
        for kind in range(17):
            r = Range(0, 1, 8, kind, 0)
            self.assertEqual(lib.nw_range_usable(C.byref(r)), kind == 7)
        for attr in [0, 8 | (1 << 63), 8 | 0x1000, 8 | 0x2000, 8 | 0x8000, 8 | 0x20000]:
            r = Range(0, 1, attr, 7, 0)
            self.assertFalse(lib.nw_range_usable(C.byref(r)))

    def test_pfn_sparse_and_failure_atomicity(self):
        ranges = (Range * 3)(Range(0x1000, 2, 8, 7, 0), Range(0x3000, 5, 8, 2, 0),
                             Range(0x100000000, 3, 8, 7, 0))
        storage, db = (Pfn * 5)(), Database()
        C.memset(C.byref(db), 0x5a, C.sizeof(db))
        before = bytes(db)
        self.assertEqual(lib.nw_pfn_init(C.byref(db), storage, 4, ranges, 3), CAPACITY)
        self.assertEqual(bytes(db), before)
        self.assertEqual(lib.nw_pfn_init(C.byref(db), storage, 5, ranges, 3), OK)
        self.assertEqual([p.physical for p in storage], [0x1000, 0x2000, 0x100000000, 0x100001000, 0x100002000])

    def test_pfn_exhaustion_and_stale_generation(self):
        db, storage = self.database(1)
        f, other = Frame(), Frame(123, 456)
        self.assertEqual(lib.nw_frame_alloc(C.byref(db), C.byref(f)), OK)
        self.assertEqual(lib.nw_frame_alloc(C.byref(db), C.byref(other)), EXHAUSTED)
        self.assertEqual((other.physical, other.generation), (123, 456))
        self.assertEqual(lib.nw_frame_release(C.byref(db), f), OK)
        self.assertEqual(lib.nw_frame_release(C.byref(db), f), STALE)
        self.assertEqual(lib.nw_frame_alloc(C.byref(db), C.byref(other)), OK)
        self.assertEqual(lib.nw_frame_retain(C.byref(db), f), STALE)
        self.assertEqual(lib.nw_frame_release(C.byref(db), f), STALE)
        self.assertGreater(other.generation, f.generation)
        self.assertEqual(lib.nw_frame_release(C.byref(db), other), OK)
        self.assertEqual(lib.nw_pfn_check(C.byref(db)), OK)

    def test_reference_overflow_and_generation_retirement(self):
        db, storage = self.database(1)
        f = Frame()
        self.assertEqual(lib.nw_frame_alloc(C.byref(db), C.byref(f)), OK)
        storage[0].references = 0xffffffff  # exclusive white-box boundary injection
        self.assertEqual(lib.nw_frame_retain(C.byref(db), f), OVERFLOW)
        self.assertEqual(storage[0].references, 0xffffffff)
        storage[0].references = 1
        self.assertEqual(lib.nw_frame_release(C.byref(db), f), OK)
        storage[0].generation = 0xffffffffffffffff
        self.assertEqual(lib.nw_frame_alloc(C.byref(db), C.byref(f)), EXHAUSTED)
        self.assertEqual(storage[0].retired, 1)
        self.assertEqual(lib.nw_pfn_check(C.byref(db)), OK)

    def test_reference_model(self):
        db, storage = self.database(32)
        rng, live = random.Random(314159), {}
        for _ in range(20000):
            action = rng.randrange(3)
            if action == 0:
                f = Frame()
                s = lib.nw_frame_alloc(C.byref(db), C.byref(f))
                if len(live) == 32:
                    self.assertEqual(s, EXHAUSTED)
                else:
                    self.assertEqual(s, OK)
                    self.assertNotIn(f.physical, live)
                    live[f.physical] = [f, 1]
            elif live:
                address = rng.choice(list(live))
                f, refs = live[address]
                if action == 1:
                    self.assertEqual(lib.nw_frame_retain(C.byref(db), f), OK)
                    live[address][1] += 1
                else:
                    self.assertEqual(lib.nw_frame_release(C.byref(db), f), OK)
                    if refs == 1:
                        del live[address]
                    else:
                        live[address][1] -= 1
            self.assertEqual(lib.nw_pfn_free_count(C.byref(db)), 32 - len(live))
        self.assertEqual(lib.nw_pfn_check(C.byref(db)), OK)

    def test_parallel_ownership_stress(self):
        db, storage = self.database(128)
        busy = (U32 * 128)()
        def worker(_):
            return lib.nw_pfn_stress(C.byref(db), busy, 0x100000, STRESS_ITERATIONS)
        with concurrent.futures.ThreadPoolExecutor(max_workers=STRESS_WORKERS) as pool:
            self.assertEqual(list(pool.map(worker, range(STRESS_WORKERS))), [0] * STRESS_WORKERS)
        self.assertEqual(lib.nw_pfn_check(C.byref(db)), OK)
        self.assertEqual(lib.nw_pfn_free_count(C.byref(db)), 128)
        self.assertEqual(sum(busy), 0)

    def test_ticket_wrap(self):
        db, storage = self.database(4)
        db.lock.next = db.lock.serving = 0xfffffffe
        for _ in range(10):
            f = Frame()
            self.assertEqual(lib.nw_frame_alloc(C.byref(db), C.byref(f)), OK)
            self.assertEqual(lib.nw_frame_release(C.byref(db), f), OK)
        self.assertEqual(lib.nw_pfn_check(C.byref(db)), OK)

    def transaction(self, exit_results, map_failure=0, malformed=False):
        order, exits = [], iter(exit_results)
        def get_map(length, buf, key, stride, version):
            order.append("map")
            length[0], key[0], stride[0], version[0] = (41 if malformed else 48), len(order), 48, 1
            return map_failure
        def exit_boot(image, key):
            order.append("exit")
            return next(exits)
        get, leave = GETMAP(get_map), EXIT(exit_boot)
        buf = C.create_string_buffer(128)
        t = Transaction(get, leave, 1, C.addressof(buf), 128, 0, 0, 0, 0, False, False)
        result = lib.nw_boot_exit(C.byref(t))
        return result, t, order, (get, leave, buf)

    def test_boot_stale_key_retry(self):
        status, t, order, keep = self.transaction([EFI_ERROR | 2, 0])
        self.assertEqual(status, 0)
        self.assertEqual(order, ["map", "exit", "map", "exit"])
        self.assertTrue(t.exited)
        self.assertEqual(t.attempts, 2)
        self.assertEqual(lib.nw_boot_exit(C.byref(t)), EFI_ERROR | 2)

    def test_boot_failure_paths_and_retry_bound(self):
        s, t, order, keep = self.transaction([EFI_ERROR | 2] * 4)
        self.assertEqual((s, t.attempts), (EFI_ERROR | 2, 4))
        self.assertFalse(t.exited)
        s, t, order, keep = self.transaction([], map_failure=EFI_ERROR | 5)
        self.assertFalse(t.exit_attempted)
        self.assertEqual((s, order), (EFI_ERROR | 5, ["map"]))
        s, t, order, keep = self.transaction([], malformed=True)
        self.assertEqual((s, order), (EFI_ERROR | 2, ["map"]))
        s, t, order, keep = self.transaction([EFI_ERROR | 7])
        self.assertEqual((s, order), (EFI_ERROR | 7, ["map", "exit"]))

    def test_abi_c_to_assembly(self):
        self.assertEqual(lib.nw_abi_from_c(), 91)
        if os.name == "nt":
            self.assertEqual(lib.nw_abi_probe(1, 2, 3, 4, 5, 6), 91)

    def test_abi_aggregate(self):
        result = lib.nw_abi_aggregate(Aggregate(11, 22, 33), 5)
        self.assertEqual((result.a, result.b, result.c), (16, 27, 38))

    def test_abi_nonvolatile_registers(self):
        self.assertEqual(lib.nw_abi_nonvolatile(), 1)

def setup(config):
    global lib
    path = ROOT / "build" / config.lower() / ("nwcore.dll" if os.name == "nt" else "libnwcore.so")
    lib = C.CDLL(str(path))
    signatures = {
        "nw_map_parse": ([C.c_void_p, SIZE, SIZE, U32, C.POINTER(Range), SIZE, C.POINTER(SIZE)], C.c_int),
        "nw_range_usable": ([C.POINTER(Range)], C.c_bool),
        "nw_pfn_init": ([C.POINTER(Database), C.POINTER(Pfn), SIZE, C.POINTER(Range), SIZE], C.c_int),
        "nw_frame_alloc": ([C.POINTER(Database), C.POINTER(Frame)], C.c_int),
        "nw_frame_retain": ([C.POINTER(Database), Frame], C.c_int),
        "nw_frame_release": ([C.POINTER(Database), Frame], C.c_int),
        "nw_pfn_check": ([C.POINTER(Database)], C.c_int),
        "nw_pfn_free_count": ([C.POINTER(Database)], SIZE),
        "nw_pfn_stress": ([C.POINTER(Database), C.POINTER(U32), U64, U32], U32),
        "nw_boot_exit": ([C.POINTER(Transaction)], U64),
        "nw_abi_from_c": ([], U64),
        "nw_abi_nonvolatile": ([], U64),
        "nw_abi_aggregate": ([Aggregate, U64], Aggregate),
    }
    if os.name == "nt":
        signatures["nw_abi_probe"] = ([U64] * 6, U64)
    for name, (args, result) in signatures.items():
        f = getattr(lib, name)
        f.argtypes, f.restype = args, result

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="CHECKED")
    args = p.parse_args()
    setup(args.config)
    started = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contracts)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"suite": "host-contracts", "passed": result.testsRun - len(result.failures) - len(result.errors),
              "total": result.testsRun, "status": "PASS" if result.wasSuccessful() else "FAIL",
              "seconds": round(time.monotonic() - started, 3), "stress_workers": STRESS_WORKERS,
              "stress_iterations": STRESS_WORKERS * STRESS_ITERATIONS, "model_operations": 20000, "fuzz_inputs": 5000,
              "host": sys.platform, "config": args.config}
    (ROOT / "build" / args.config.lower() / "host-tests.json").write_text(json.dumps(report, indent=2) + "\n")
    sys.exit(0 if result.wasSuccessful() else 1)
