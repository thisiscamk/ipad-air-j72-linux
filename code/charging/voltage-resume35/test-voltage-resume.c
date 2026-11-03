/* SPDX-License-Identifier: GPL-2.0-only */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "j72-maintain-core.h"
struct hw {unsigned value,overrides;bool fail_restore;};
static struct hw h;static struct j72_maintain m;static struct j72_limit_state p;
static int rd(void *ctx,unsigned*v){struct hw*x=ctx;*v=x->value;return 0;}
static int wr(void *ctx,unsigned v){struct hw*x=ctx;assert(v==J72_HANDOFF||v==J72_TRIAL);if(v==J72_HANDOFF&&x->fail_restore)return -EIO;if(v==J72_TRIAL)x->overrides++;x->value=v;return 0;}
static struct j72_limit_io io={&h,rd,wr};
static void reset(void){memset(&m,0,sizeof(m));memset(&p,0,sizeof(p));memset(&h,0,sizeof(h));h.value=J72_HANDOFF;m.enabled=true;m.sample_valid=true;int v[]={1,90,345,4035000,300000};memcpy(m.sample,v,sizeof(v));}
static void step(u64 now){m.sample_at_ms=now;j72_maintain_step(&m,&p,&io,now,0,0);}
static void start(void){reset();step(1000);assert(p.active);}
static void full(void){m.sample[2]=367;m.sample[3]=4201000;step(2000);assert(!p.active&&p.restored&&!m.fault&&m.last_pause==J72_WAIT_FULL);m.sample[3]=4095000;}
int main(void){unsigned cases=0;
 reset();m.sample[2]=366;step(1000);assert(!p.active&&!h.overrides);m.sample[2]=365;step(2000);assert(p.active);cases++;
 reset();m.last_pause=J72_WAIT_FULL;m.sample[2]=366;step(1000);assert(!p.active&&!h.overrides);cases++;
 start();full();step(31999);assert(!p.active);step(32000);assert(p.active&&m.warm_full_resumes==1&&!m.thermal_latched);cases++;
 start();full();m.sample[2]=380;step(32000);assert(p.active);m.sample[2]=381;step(33000);assert(!p.active&&m.thermal_latched&&m.last_pause==J72_WAIT_COOL);cases++;
 start();full();m.sample[2]=381;step(3000);assert(m.thermal_latched);m.sample[2]=366;step(40000);assert(!p.active&&m.thermal_latched);m.sample[2]=365;step(41000);assert(p.active&&!m.thermal_latched&&!m.warm_full_resumes);cases++;
 start();m.sample[2]=381;step(2000);assert(m.thermal_latched);m.sample[2]=367;m.sample[3]=4201000;step(40000);assert(m.mode==J72_WAIT_FULL&&m.thermal_latched);m.sample[3]=4095000;step(41000);assert(!p.active&&m.thermal_latched);m.sample[2]=365;step(42000);assert(p.active&&!m.thermal_latched);cases++;
 start();full();step(32000);assert(p.active);u64 end=p.deadline_ms;step(end);assert(!p.active&&m.last_pause==J72_WAIT_WINDOW);step(end+30000);assert(!p.active);m.sample[2]=365;step(end+31000);assert(p.active);cases++;
 start();full();m.enabled=false;j72_maintain_pause(&m,&p,&io,3000,J72_OFF,0,false);assert(m.last_pause==J72_OFF);m.enabled=true;step(40000);assert(!p.active);cases++;
 start();full();m.sample_at_ms=40000;j72_maintain_step(&m,&p,&io,40000,-ETIME,0);assert(m.fault&&!m.enabled&&!p.active&&h.overrides==1);m.sample_at_ms=41000;assert(!j72_maintain_requalify(&m,&p,&io,41000,0,0));m.enabled=true;step(42000);assert(!p.active);cases++;
 start();full();m.sample_at_ms=40000;j72_maintain_step(&m,&p,&io,40000,0,-EPERM);assert(m.fault&&!p.active&&h.overrides==1);cases++;
 start();full();m.sample_at_ms=1000;j72_maintain_step(&m,&p,&io,40000,0,0);assert(m.fault&&!p.active&&h.overrides==1);cases++;
 start();h.fail_restore=true;m.sample[3]=4201000;step(2000);assert(m.fault&&p.restore_failed);h.fail_restore=false;m.sample[3]=4000000;step(40000);assert(!p.active&&h.overrides==1);cases++;
 start();full();h.value=0x3e;step(40000);assert(m.fault&&!p.active&&h.overrides==1);cases++;
 start();full();m.sample[1]=91;step(40000);assert(!p.active);m.sample[1]=90;m.sample[3]=4100001;step(41000);assert(!p.active);m.sample[3]=4100000;step(42000);assert(p.active);cases++;
 printf("PASS: %u cause-aware restart boundary/fault/latch scenarios\n",cases);return 0;
}
