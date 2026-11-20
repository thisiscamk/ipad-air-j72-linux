#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from observe import recorder_events, usb_snapshot
from flightrec import Event, new_page


class ObserverTests(unittest.TestCase):
    def test_usb_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dev = root / "1-2"
            dev.mkdir()
            (dev / "idVendor").write_text("1209\n")
            (dev / "idProduct").write_text("316d\n")
            (dev / "devnum").write_text("24\n")
            self.assertEqual(usb_snapshot(root)[0]["identity"], "M1N1_PROXY")

    def test_incremental_recorder(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.bin"
            kwargs = dict(boot_nonce=bytes(16), target="iPad4,2/16H81",
                          payload_sha256=bytes(32), config_sha256=bytes(32))
            path.write_bytes(new_page(events=[Event(0x0400, 1, 1)], **kwargs))
            events, sequence, error = recorder_events(path, 0)
            self.assertIsNone(error)
            self.assertEqual((len(events), sequence), (1, 1))
            events, sequence, error = recorder_events(path, sequence)
            self.assertEqual((events, sequence, error), ([], 1, None))


if __name__ == "__main__":
    unittest.main()
