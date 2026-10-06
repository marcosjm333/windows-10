import importlib.util
from pathlib import Path
import random
import struct
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('peinspect', ROOT / 'tools/peinspect/inspect.py')
pe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pe)

class PeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / 'build/checked/BOOTX64.EFI').read_bytes()

    def test_own_image(self):
        self.assertEqual(pe.inspect(self.image, True)['structural_audit'], 'PASS')

    def test_truncation(self):
        for n in [0, 1, 63, 64, 100, 256, 512, 1024]:
            with self.assertRaises(pe.PeError):
                pe.inspect(self.image[:n], True)

    def test_malicious_header_offsets(self):
        for offset in [0, 63, len(self.image), 0xffffffff]:
            damaged = bytearray(self.image)
            struct.pack_into('<I', damaged, 60, offset)
            with self.assertRaises(pe.PeError):
                pe.inspect(damaged, True)

    def test_directory_count_rejected_cleanly(self):
        for count in [0, 6, 12, 17, 0xffffffff]:
            damaged = bytearray(self.image)
            optional = struct.unpack_from('<I', damaged, 60)[0] + 24
            struct.pack_into('<I', damaged, optional + 108, count)
            with self.assertRaises(pe.PeError):
                pe.inspect(damaged, True)

    def test_bounded_fuzz(self):
        rng = random.Random(161803)
        for _ in range(2000):
            damaged = bytearray(self.image)
            for _ in range(rng.randrange(1, 8)):
                damaged[rng.randrange(min(len(damaged), 1024))] = rng.randrange(256)
            try:
                pe.inspect(damaged, True)
            except pe.PeError:
                pass
            # Any unexpected IndexError/struct.error is a parser failure.

if __name__ == '__main__':
    unittest.main(verbosity=2)
