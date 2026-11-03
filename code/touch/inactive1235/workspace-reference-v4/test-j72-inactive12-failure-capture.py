#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import base64
import importlib.util
from pathlib import Path
import tempfile
import unittest
import j72_inactive12_failure_capture as capture

spec = importlib.util.spec_from_file_location('audit_shapes', Path(__file__).with_name('analyze-j72-reader-audit.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def snapshot(done=1):
    h = dict.fromkeys(audit.FIELDS, 0)
    h.update(magic=0x4a373253, version=3, done=done, records=1,
             info_end=int(done==1), frames=1)
    rx = bytearray(audit.DATA_BYTES)
    rx[0:5] = bytes([0xeb, 1, 26, 0, (-0xeb-1-26)&255])
    rx[5] = 0x45  # Synthetic checksum-valid but non-native report type.
    rx[7] = 24
    rx[22] = 30
    rx[29:31] = sum(rx[5:29]).to_bytes(2, 'little')
    tx = bytes([0xeb,1,1])+bytes(13)
    first = audit.RECORD.pack(100, 2, 31, 0x900, 31, 0, tx, bytes(rx))
    return audit.HEADER.pack(*(h[k] for k in audit.FIELDS))+first+bytes(63*audit.RECORD.size)


class FakeTransport:
    def __init__(self, *, baseline=True, state='0', stop_error=False, size_error=False):
        self.baseline=baseline;self.state=state;self.stop_error=stop_error
        self.size_error=size_error;self.calls=[]
    def __call__(self, body, timeout):
        self.calls.append(body)
        if body==capture.scoped_shell(capture.BASELINE):
            if not self.baseline:raise RuntimeError('Baseline not restored')
            return b'BASELINE_PASS\n'
        if body in (capture.scoped_shell(capture.STOP_DESKTOP),capture.scoped_shell('/sbin/j72-touch-session stop')):
            if self.stop_error:raise RuntimeError('Normal stop API failed')
            return b'normal stop\n'
        if body==capture.scoped_shell(capture.STATUS):
            return ('session_state='+self.state+'\ninput_frames=10\ninput_recoveries=0\ninput_bad_layouts=1\ninput_timeouts=0\nlayout_anomalies=1\nwire_anomalies=0\nxfer_errors=0\nfirmware_healthy='+('0' if self.stop_error else '1')+'\ncleanup_ok='+('N' if self.stop_error else 'Y')+'\nhardware_cleanup_ok='+('N' if self.stop_error else 'Y')+'\nrecovery_stop_reason=0\n').encode()
        if body==capture.scoped_shell(capture.EXPORT):
            data=snapshot(3 if self.stop_error else 1)
            return base64.b64encode(data[:-1] if self.size_error else data)
        raise AssertionError('Unexpected operation')


class CaptureTests(unittest.TestCase):
    def run_capture(self, transport):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.out=Path(self.temp.name)/'capture'
        return capture.capture(transport,self.out)
    def test_real_analyzer_classifies_stable_synthetic_layout(self):
        t=FakeTransport();r=self.run_capture(t)
        self.assertEqual(r['status'],'STOPPED_RING_CAPTURED')
        self.assertTrue(r['analysis_pass'])
        self.assertFalse(r['original_failure_cleared'])
        import json
        a=json.loads((self.out/'analysis.json').read_text())
        self.assertEqual(a['layout_refusals'],{'type_or_short':1})
        self.assertEqual(len(t.calls),5)
    def test_unrestored_baseline_prevents_stop_or_export(self):
        t=FakeTransport(baseline=False);r=self.run_capture(t)
        self.assertEqual(r['status'],'NOT_CAPTURED');self.assertEqual(len(t.calls),1)
    def test_active_session_never_exports_after_stop_error(self):
        t=FakeTransport(state='2',stop_error=True);r=self.run_capture(t)
        self.assertEqual(r['status'],'NOT_CAPTURED')
        self.assertNotIn(capture.scoped_shell(capture.EXPORT),t.calls)
    def test_failed_api_not_relabelled_by_successful_state4_capture(self):
        t=FakeTransport(state='4',stop_error=True);r=self.run_capture(t)
        self.assertEqual(r['status'],'STOPPED_RING_CAPTURED')
        self.assertFalse(r['input-stop_api_pass']);self.assertTrue(r['analysis_pass'])
        self.assertEqual(r['touch_status']['cleanup_ok'],'N')
    def test_bad_export_size_refused(self):
        r=self.run_capture(FakeTransport(size_error=True))
        self.assertEqual(r['status'],'NOT_CAPTURED')
        self.assertFalse((self.out/'touch-anomalies.bin').exists())
    def test_capture_shells_parse_without_execution(self):
        import subprocess
        for body in (capture.BASELINE,capture.STOP_DESKTOP,capture.STATUS,capture.EXPORT):
            subprocess.run(['/bin/sh','-n'],input=body,text=True,check=True)


if __name__=='__main__':
    unittest.main()
