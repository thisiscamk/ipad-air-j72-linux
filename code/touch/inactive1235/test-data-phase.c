/* SPDX-License-Identifier: GPL-2.0-only */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "j72-data-phase.h"
struct fake {
 unsigned calls, headers, announced, second_announced, tag;
 unsigned first_wire, second_wire, fail_at;
 int bad_sum, first_data;
};
static struct fake f;
static unsigned char tx[J72_DATA_CAPACITY], rx[J72_DATA_CAPACITY];
static void header(unsigned char *p,unsigned length) {
 p[0]=0xe1;p[1]=length;p[2]=length>>8;
 unsigned sum=0;for(unsigned i=0;i<14;i++)sum+=p[i];
 p[14]=sum;p[15]=sum>>8;
}
static int xfer(void *ctx,unsigned char *t,unsigned char *r,unsigned wire) {
 struct fake *x=ctx;x->calls++;
 assert(wire>=7&&wire<=2459&&t[0]==0xeb&&t[1]==x->tag&&t[2]==1);
 unsigned sum=0;for(unsigned i=0;i<14;i++)sum+=i==wire-2||i==wire-1?0:t[i];
 assert(((unsigned)t[wire-2]|((unsigned)t[wire-1]<<8))==sum);
 if(x->calls==1)x->first_wire=wire;else x->second_wire=wire;
 if(x->fail_at==x->calls)return -5;
 if((x->calls==1&&!x->first_data)||(x->calls==2&&x->second_announced)) {
  if(wire>=16){header(r,x->calls==1?x->announced:x->second_announced);if(x->bad_sum)r[14]^=1;}
 } else r[0]=0xeb; /* Acquisition does NOT claim this is a valid full frame. */
 return 0;
}
static void seen(void *ctx,const unsigned char *t,const unsigned char *r,unsigned wire) {
 struct fake *x=ctx;x->headers++;
 assert(x->calls==1&&wire>=16&&t[1]==x->tag&&r[0]==0xe1);
}
static const struct j72_data_io io={&f,xfer,seen};
static void reset(unsigned tag) {memset(&f,0,sizeof(f));f.tag=tag;f.announced=26;}
static struct j72_data_result run(unsigned payload) {return j72_data_phase(&io,tx,rx,sizeof(tx),payload,f.tag);}
int main(void) {
 unsigned cases=0;struct j72_data_result r;
 for(unsigned tag=1;tag<=2;tag++) {
  reset(tag);r=run(26);assert(!r.error&&r.resynced&&f.calls==2&&f.headers==1&&r.wire==31);cases++;
  reset(tag);f.first_data=1;r=run(26);assert(!r.resynced&&f.calls==1);cases++;
  reset(tag);f.second_announced=26;r=run(26);assert(r.resynced&&f.calls==2&&rx[0]==0xe1);cases++;
  reset(tag);f.bad_sum=1;r=run(26);assert(!r.resynced&&f.calls==1);cases++;
  reset(tag);f.fail_at=1;r=run(26);assert(r.error==-5&&f.calls==1&&!f.headers);cases++;
  reset(tag);f.fail_at=2;r=run(26);assert(r.error==-5&&f.calls==2&&f.headers==1);cases++;
 }
 for(unsigned length=0;length<=65535;length++) {
  reset(1);f.announced=length;r=run(26);
  unsigned admit=length>=2&&length<=2454;
  assert(f.calls==1+admit&&r.resynced==admit&&f.headers==admit);
  if(admit)assert(f.second_wire==length+5);
 }
 cases++;
 for(unsigned length=2;length<11;length++) {
  reset(1);r=run(length);assert(f.calls==1&&!r.resynced);
 }cases++;
 for(unsigned tag=0;tag<=3;tag+=3) {reset(tag);r=run(26);assert(r.error&&!f.calls);}cases++;
 reset(1);r=run(2455);assert(r.error&&!f.calls);cases++;
 reset(1);r=j72_data_phase(&io,tx,rx,sizeof(tx)-1,26,1);assert(r.error&&!f.calls);cases++;
 reset(1);r=j72_data_phase(&io,tx,tx,sizeof(tx),26,1);assert(r.error&&!f.calls);cases++;
 reset(1);r=j72_data_phase(&io,tx,tx+1,sizeof(tx),26,1);assert(r.error&&!f.calls);cases++;
 printf("PASS: %u acquisition scenarios including all 65536 announced lengths; one-retry bound and unchanged tags\n",cases);
 return 0;
}
