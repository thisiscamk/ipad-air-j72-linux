#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compile the actual candidate emitter with controlled Linux input calls."""
from pathlib import Path
import subprocess
import sys
import tempfile

source = Path(sys.argv[1])
text = source.read_text()
start = text.index('static bool emit_touch_input(')
end = text.index('/* Acquisition retries', start)
emitter = text[start:end]
prefix = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include "j72-classic-contacts.h"
typedef unsigned char u8;
#define MT_TOOL_FINGER 0
#define ABS_MT_POSITION_X 0
#define ABS_MT_POSITION_Y 1
#define clamp(v,lo,hi) ((v)<(lo)?(lo):((v)>(hi)?(hi):(v)))
static void *touch_input;
static bool input_active, slots[256];
static unsigned input_bad_layouts,input_frames,contact_state1_frames,contact_state2_frames;
static unsigned events,positions,syncs,selected,last_input_frame,jiffies;
static int input_mt_get_slot_by_key(void *p,unsigned id){(void)p;return id;}
static void input_mt_slot(void *p,int slot){(void)p;selected=slot;events++;}
static void input_mt_report_slot_state(void *p,int tool,bool active){
 (void)p;(void)tool;slots[selected]=active;events++;
}
static void input_report_abs(void *p,int axis,int value){
 (void)p;(void)axis;(void)value;positions++;events++;
}
static void input_mt_sync_frame(void *p){(void)p;syncs++;events++;}
static void input_sync(void *p){(void)p;syncs++;events++;}
static void reset(void){
 memset(slots,0,sizeof(slots));input_active=false;
 events=positions=syncs=input_bad_layouts=input_frames=contact_state1_frames=contact_state2_frames=0;
}
'''
suffix = r'''
int main(int argc,char **argv){
 unsigned char p[324]={0};unsigned state,i,len;
 p[0]=0x44;p[2]=24;p[17]=30;p[16]=1;p[24]=9;
 /* Every byte value: only the observed state is added; active states stay 3/4. */
 for(state=0;state<256;state++){
  reset();p[25]=state;
  bool known=state==0||state==1||state==2||state==3||state==4||state==5||state==7;
  assert(emit_touch_input(p,54)==known);
  if(!known){assert(events==0&&input_bad_layouts==1&&input_frames==0);continue;}
  assert(slots[9]==(state==3||state==4));
  assert(positions==((state==3||state==4)?2:0));
  assert(input_frames==1&&contact_state1_frames==(state==1)&&contact_state2_frames==(state==2));
 }
 /* A state-1 report releases an already active slot without coordinates. */
 reset();p[25]=3;assert(emit_touch_input(p,54)&&slots[9]);
 unsigned before=positions;p[25]=1;assert(emit_touch_input(p,54));
 assert(!slots[9]&&!input_active&&positions==before&&contact_state1_frames==1);
 p[25]=4;assert(emit_touch_input(p,54)&&slots[9]);
 before=positions;p[25]=2;assert(emit_touch_input(p,54)&&!slots[9]&&positions==before&&contact_state2_frames==1);
 /* Full report validation: an invalid second contact emits no partial event. */
 reset();p[16]=2;p[25]=1;p[54]=10;p[55]=6;
 assert(!emit_touch_input(p,84)&&events==0&&contact_state1_frames==0);
 p[55]=4;p[54]=9;reset();assert(!emit_touch_input(p,84)&&events==0);
 /* Every truncated length, bad header, count, image and stride still fails. */
 p[16]=1;p[25]=1;
 for(len=0;len<54;len++){reset();assert(!emit_touch_input(p,len)&&events==0);}
 for(i=0;i<256;i++)if(i!=24){p[2]=i;reset();assert(!emit_touch_input(p,54)&&events==0);}
 p[2]=24;
 for(i=0;i<256;i++)if(i!=30){p[17]=i;reset();assert(!emit_touch_input(p,54)&&events==0);}
 p[17]=30;p[14]=1;reset();assert(!emit_touch_input(p,54)&&events==0);p[14]=0;
 for(i=11;i<256;i++){p[16]=i;reset();assert(!emit_touch_input(p,sizeof(p))&&events==0);}
 /* Mixed contacts: only 3/4 are active; state 1 never reports coordinates. */
 p[16]=10;
 for(i=0;i<10;i++){p[24+i*30]=i;p[25+i*30]=(i==0?1:4);}
 reset();assert(emit_touch_input(p,sizeof(p))&&positions==18&&!slots[0]);
 assert(contact_state1_frames==1);
 for(int arg=1;arg<argc;arg++){
  FILE *f=fopen(argv[arg],"rb");assert(f);size_t size=fread(p,1,sizeof(p),f);assert(!ferror(f));fclose(f);
  reset();assert(emit_touch_input(p,size)&&input_frames==1);
  assert(contact_state1_frames==(p[25]==1)&&contact_state2_frames==(p[25]==2));
  assert(positions==0&&!input_active);
 }
 puts("PASS actual emitter: all 256 states, active-to-inactive release, atomic rejection, truncation/header/count/stride/image guards, mixed contacts and optional private state1/state2 report replay");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='j72-state1-emitter-') as directory:
    p = Path(directory)
    (p/'test.c').write_text(prefix+emitter+suffix)
    subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                    '-fsanitize=undefined,bounds','-fno-sanitize-recover=all',
                    '-I',str(source.parent),str(p/'test.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test'),*sys.argv[2:]],check=True)
