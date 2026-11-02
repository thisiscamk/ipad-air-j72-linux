#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import importlib.util,json,os,signal,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from j72_observation_health import Health,StopObservation,fields,restored,scoped_shell
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('observe',Path(__file__).with_name('run-j72-observation35.py'))
observe=importlib.util.module_from_spec(spec);spec.loader.exec_module(observe)
def valid():
 return dict(touch_session_state='2',touch_enabled='Y',touch_continuous='Y',touch_capture_seconds='3',touch_recovery_stop_reason='0',touch_xfer_errors='0',touch_input_bad_layouts='0',wifi_state='COMPLETED',desktop_ready='1',nbd_blocks='0',native_mounts='0',charge_ready='1',charge_fault='0',charge_restore_failed='0',governor='schedutil',brightness='802',touch_input_frames='100',touch_session_number='3',touch_input_recoveries='0',touch_wire_anomalies='0',touch_input_timeouts='0',battery_CAPACITY='80',battery_TEMP='330',battery_VOLTAGE_NOW='4000000',charge_enabled='0',charge_active='0')
class ObservationTests(unittest.TestCase):
 def test_initial_and_healthy_recovery_lifetime(self):
  h=Health(802);r=valid();h.check(r,initial=True)
  for i in range(1,12):
   r.update(touch_input_frames=str(100+i),touch_input_recoveries=str(i),charge_enabled='1',charge_active='1');h.check(r)
 def test_full_hot_and_high_voltage_defer_without_mutation(self):
  for key,value in [('battery_CAPACITY','100'),('battery_TEMP','366'),('battery_VOLTAGE_NOW','4100001'),('charge_enabled','1')]:
   r=valid();r[key]=value
   with self.subTest(key=key),self.assertRaises(StopObservation):Health(802).check(r,initial=True)
 def test_faults_wrong_workload_and_input_failure_stop(self):
  for key,value in [('touch_session_state','4'),('touch_recovery_stop_reason','1'),('touch_xfer_errors','1'),('charge_fault','1'),('charge_restore_failed','1'),('wifi_state','DISCONNECTED'),('nbd_blocks','123'),('native_mounts','1'),('desktop_ready','0'),('governor','conservative'),('brightness','1604')]:
   r=valid();r[key]=value
   with self.subTest(key=key),self.assertRaises(StopObservation):Health(802).check(r)
 def test_expected_protective_hold_is_not_input_failure(self):
  h=Health(802);r=valid();h.check(r,initial=True)
  r.update(charge_active='0',charge_mode='3',battery_TEMP='381',battery_VOLTAGE_NOW='4201000',touch_input_frames='101')
  h.check(r)
 def test_session_restart_regression_and_timeout_stop(self):
  for key,value in [('touch_session_number','4'),('touch_input_frames','99'),('touch_input_timeouts','1')]:
   h=Health(802);r=valid();h.check(r,initial=True);r[key]=value
   with self.subTest(key=key),self.assertRaises(StopObservation):h.check(r)
 def test_three_stalled_samples_stop(self):
  h=Health(802);r=valid();h.check(r,initial=True);h.check(r);h.check(r)
  with self.assertRaises(StopObservation):h.check(r)
 def test_fresh_frame_clears_stall_count(self):
  h=Health(802);r=valid();h.check(r,initial=True);h.check(r);h.check(r)
  r['touch_input_frames']='101';h.check(r);self.assertEqual(h.stalled,0)
 def test_duplicate_malformed_and_non_numeric_status_refused(self):
  for data in [b'a=1\na=2\n',b'a\n',b'=1\n']:
   with self.assertRaises(StopObservation):fields(data)
  r=valid();r['touch_input_frames']='abc'
  with self.assertRaises(StopObservation):Health(802).check(r)
 def test_independent_restoration_is_required_and_not_fault_reset(self):
  r=dict(enabled='0',active='0',armed='0',restore_failed='0',reg_04c0='02',cycles='1',restored='1',fault='1')
  restored(r);self.assertEqual(r['fault'],'1')
  for key,value in [('enabled','1'),('active','1'),('reg_04c0','3c'),('restored','0'),('restore_failed','1')]:
   with self.subTest(key=key),self.assertRaises(StopObservation):restored({**r,key:value})
 def test_failed_identity_guard_cannot_execute_later_body_lines(self):
  import shlex
  with tempfile.TemporaryDirectory() as d:
   flag=Path(d)/'must-not-exist'
   body='printf first\ntouch '+shlex.quote(str(flag))
   result=subprocess.run(['/bin/sh','-ec','false && '+scoped_shell(body)],capture_output=True)
   self.assertNotEqual(result.returncode,0);self.assertFalse(flag.exists());self.assertEqual(result.stdout,b'')
 def test_real_sigterm_enters_cleanup_and_repeated_signal_is_deferred(self):
  old=signal.getsignal(signal.SIGTERM)
  with observe.ObserverSignals() as guard:
   with self.assertRaises(KeyboardInterrupt):os.kill(os.getpid(),signal.SIGTERM)
   guard.closing=True
   os.kill(os.getpid(),signal.SIGTERM)
  self.assertEqual(signal.getsignal(signal.SIGTERM),old)
 def test_real_owned_process_group_interrupt_runs_finally_and_reaps_child(self):
  with tempfile.TemporaryDirectory() as d:
   body='''import subprocess,sys,time\nfrom pathlib import Path\np=Path(sys.argv[1])\nc=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])\n(p/'child').write_text(str(c.pid))\n(p/'ready').touch()\ntry:\n while True:time.sleep(.05)\nexcept KeyboardInterrupt:pass\nfinally:\n c.terminate();c.wait(timeout=2)\n (p/'finally').touch()\n'''
   with open(os.devnull,'wb') as log:
    p=subprocess.Popen([sys.executable,'-c',body,d],start_new_session=True,stdout=log,stderr=log)
    try:
     deadline=time.monotonic()+5
     while not (Path(d)/'ready').exists() and time.monotonic()<deadline:time.sleep(.02)
     self.assertTrue((Path(d)/'ready').exists());pid=int((Path(d)/'child').read_text())
     observe.stop_child(p);self.assertTrue((Path(d)/'finally').exists());self.assertIsNotNone(p.returncode)
     with self.assertRaises(ProcessLookupError):os.kill(pid,0)
    finally:
     if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
if __name__=='__main__':unittest.main()
