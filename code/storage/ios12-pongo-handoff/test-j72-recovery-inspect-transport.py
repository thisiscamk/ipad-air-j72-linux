#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise recovery transport refusal and cleanup with no USB or subprocesses."""
import contextlib, importlib.util, io, json, subprocess, tempfile, types
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def main():
 spec=importlib.util.spec_from_file_location('transport',ROOT/'tools/j72-recovery-inspect-live.py')
 transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
 cases=0
 for scenario in ('success','inspection_failure','daemon_failure','originally_inactive','missing_marker','missing_guard'):
  events=[]
  class Attempt:
   def __init__(self,folder):self.folder=folder;events.append('attempt')
   def ssh_args(self):return ['ssh','-o','PubkeyAcceptedAlgorithms=+ssh-rsa','root@127.0.0.1']
   def inspect(self):
    args=self.ssh_args();assert args[-1]=='root@127.0.0.1'
    assert 'PubkeyAcceptedAlgorithms=ssh-rsa' in args and args[-2]=='-vvv'
    events.append('inspect')
    if scenario!='missing_guard':
     guard={'profile':'j72-ram-mount-guard-v3','root_is_hfs_md0':True,'bootargs_approved':True,'device_numbers_match':1,'apfs_mounts':0}
     (self.folder/'commands.log').write_text('J72_GUARD_JSON '+json.dumps(guard)+'\n')
    if scenario=='inspection_failure':raise RuntimeError('simulated inspector failure')
   def close(self):events.append('close')
  class Server:
   pid=424242
   def poll(self):return 1 if scenario=='daemon_failure' else None
   def wait(self,timeout=None):events.append('wait');return 0
  def run(args,**kwargs):
   action=args[1];events.append(action)
   return subprocess.CompletedProcess(args,int(action=='is-active' and scenario=='originally_inactive'))
  def popen(args,**kwargs):
   assert args[-5:]==['/usr/sbin/usbmuxd','-f','-p','-U','usbmux']
   assert kwargs['start_new_session'] is True
   events.append('spawn');return Server()
  def target():
   events.append('target')
   if scenario=='missing_marker':raise RuntimeError('simulated absent recovery marker')
  with tempfile.TemporaryDirectory(prefix='j72-transport-test-') as tmp,contextlib.ExitStack() as stack:
   root=Path(tmp);(root/'private').mkdir();base=root/'private/recovery'
   folder=base/'pongo-route/handoff-v3/stage-test';folder.mkdir(parents=True)
   for obj,name,value in [(transport,'ROOT',root),(transport,'BASE',base),
       (transport,'target',target),(transport,'load_inspector',lambda:types.SimpleNamespace(Attempt=Attempt)),
       (transport.os,'geteuid',lambda:0),(transport.os,'killpg',lambda *a:events.append('kill')),
       (transport.subprocess,'run',run),(transport.subprocess,'Popen',popen),
       (transport.time,'sleep',lambda _:None)]:stack.enter_context(patch.object(obj,name,value))
   if scenario=='missing_marker':stack.enter_context(patch.object(transport.time,'monotonic',side_effect=[0,91]))
   failed=False
   with contextlib.redirect_stdout(io.StringIO()):
    try:transport.inspect_live(folder)
    except RuntimeError:failed=True
   assert failed==(scenario in ('inspection_failure','daemon_failure','missing_marker','missing_guard'))
   if scenario=='missing_marker':assert events==['target'],events
   else:
    assert events.count('stop')==1 and events.count('kill')==1 and events.count('wait')==1
    assert events.index('close')<events.index('kill')<events.index('wait')
    assert events.count('start')==int(scenario!='originally_inactive')
    if scenario!='originally_inactive':assert events[-1]=='start'
    if scenario in ('success','inspection_failure','originally_inactive'):assert (folder/'mount-guard.json').exists()
   cases+=1
 print(json.dumps({'status':'PASS','transport_cleanup_and_refusal_cases':cases,'usb_access':False,'real_subprocesses':False}))
if __name__=='__main__':main()
