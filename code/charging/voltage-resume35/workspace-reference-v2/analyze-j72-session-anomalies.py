#!/usr/bin/env python3
"""Validate private session anomaly rings; print counts, never raw packets."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
s=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('analyze-j72-reader-audit.py'))
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

def analyze(data,layouts,wires):
 if len(data)!=a.HEADER.size+64*a.RECORD.size:raise ValueError('session snapshot size')
 h=dict(zip(a.FIELDS,a.HEADER.unpack_from(data)))
 if h['magic']!=0x4a373253 or h['version']!=3 or h['done'] not in (1,2,3):raise ValueError('incomplete session snapshot')
 if layouts<0 or wires<0 or h['records']!=layouts+wires:raise ValueError('ring count mismatch')
 reasons=Counter()
 for base,count,layout in [(0,layouts,True),(32,wires,False)]:
  previous=-1
  for sequence in range(max(0,count-32),count):
   index=base+sequence%32
   ms,kind,length,flags,stored,res,tx,rx=a.RECORD.unpack_from(data,a.HEADER.size+index*a.RECORD.size)
   if res or kind not in (1,2) or stored!=length or not 7<=length<=2459 or ms<previous:raise ValueError('record metadata')
   previous=ms
   if tx[0]!=0xeb or tx[1] not in (1,2) or tx[2]!=(kind==2):raise ValueError('request metadata')
   if layout:
    if kind!=2 or flags&0x900!=0x900 or rx[0] not in (0xea,0xeb) or sum(rx[:5])&255 or int.from_bytes(rx[2:4],'little')+5!=length or sum(rx[5:length-2])&65535!=int.from_bytes(rx[length-2:length],'little'):raise ValueError('layout packet checksum')
    body=rx[5:length-2]
    if len(body)<24 or body[0]!=0x44:reason='type_or_short'
    elif body[2]!=24 or body[14:16]!=b'\0\0' or body[17]!=30:reason='header_image_or_stride'
    elif body[16]>10:reason='count_over_ten'
    else:
     try:contacts=a.classic_contacts(body)
     except ValueError:reason='truncation_or_duplicate_id'
     else:
      if any(c['state'] not in (0,3,4,5,7) for c in contacts):reason='unrecognized_contact_state'
      else:raise ValueError('layout rejection does not reproduce')
    reasons[reason]+=1
   elif not (kind==2 and flags&0x200 or kind==1 and flags&(0x10|0x20|0x40|0x80)):raise ValueError('wire anomaly classification')
 return {'complete':h['done']==1,'firmware_healthy':bool(h['info_end']),
  'counters':{k:h[k] for k in a.FIELDS[9:]},'layout_anomalies':layouts,
  'wire_anomalies':wires,'retained_layouts':min(layouts,32),'retained_wire':min(wires,32),
  'overwritten_layouts':max(0,layouts-32),'overwritten_wire':max(0,wires-32),
  'layout_refusals':dict(reasons)}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('snapshot',type=Path);p.add_argument('--layouts',type=int,required=True);p.add_argument('--wire',type=int,required=True);args=p.parse_args()
 print(json.dumps(analyze(args.snapshot.read_bytes(),args.layouts,args.wire),indent=2))
if __name__=='__main__':main()
