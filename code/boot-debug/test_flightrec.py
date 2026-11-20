#!/usr/bin/env python3
import hashlib
import unittest

from flightrec import (EVENT_CAPACITY, PAGE_SIZE, Event, classify, crc32c,
                       decode_page, new_page)


class FlightRecorderTests(unittest.TestCase):
    def page(self, events):
        return new_page(boot_nonce=bytes(range(16)), target="iPad4,2/16H81",
                        payload_sha256=hashlib.sha256(b"payload").digest(),
                        config_sha256=hashlib.sha256(b"config").digest(),
                        events=events)

    def test_known_crc32c(self):
        self.assertEqual(crc32c(b"123456789"), 0xE3069283)

    def test_round_trip(self):
        source = [Event(0x0100, 1, 1, counter=10),
                  Event(0x0200, 1, 2, current_el=4, mpidr=0),
                  Event(0x0620, 2, 3, arg0=0x80E600000)]
        page = self.page(source)
        self.assertEqual(len(page), PAGE_SIZE)
        header, events = decode_page(page)
        self.assertEqual(header.target, "iPad4,2/16H81")
        self.assertEqual(events, source)
        result = classify(events)
        self.assertEqual(result["boundary"], "LINUX_ENTRY_CONTRACT")

    def test_corrupt_event_refused(self):
        page = bytearray(self.page([Event(0x0100, 1, 1)]))
        page[300] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC"):
            decode_page(bytes(page))

    def test_torn_sequence_refused(self):
        page = bytearray(self.page([Event(0x0100, 1, 1)]))
        page[256 + 12] = 2
        with self.assertRaises(ValueError):
            decode_page(bytes(page))

    def test_capacity(self):
        events = [Event(0x0100, 1, i + 1) for i in range(EVENT_CAPACITY)]
        self.assertEqual(len(decode_page(self.page(events))[1]), EVENT_CAPACITY)

    def test_empty_classification(self):
        self.assertEqual(classify([])["status"], "NO_VALID_RECORDER_EVENT")


if __name__ == "__main__":
    unittest.main()
