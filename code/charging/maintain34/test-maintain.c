/* SPDX-License-Identifier: GPL-2.0-only */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "module/j72-maintain-core.h"
struct hw {unsigned value, reads, writes, overrides, restores;int read_error,write_error;bool fail_restore;};
static int rd(void *ctx,unsigned *v){struct hw*h=ctx;h->reads++;if(h->read_error)return h->read_error;*v=h->value;return 0;}
static int wr(void *ctx,unsigned v){struct hw*h=ctx;h->writes++;assert(v==J72_HANDOFF||v==J72_TRIAL);if(v==J72_HANDOFF)h->restores++;else h->overrides++;if(h->write_error)return h->write_error;if(h->fail_restore&&v==J72_HANDOFF)return -EIO;h->value=v;return 0;}
static struct hw h;static struct j72_maintain m;static struct j72_limit_state p;static struct j72_limit_io io={&h,rd,wr};
static unsigned cases;
static void reset(void){memset(&m,0,sizeof(m));memset(&p,0,sizeof(p));memset(&h,0,sizeof(h));h.value=J72_HANDOFF;m.enabled=true;m.sample_valid=true;int v[]={1,80,340,4000000,200000};memcpy(m.sample,v,sizeof(v));m.sample_at_ms=1000;}
static void step(u64 now){m.sample_at_ms=now;j72_maintain_step(&m,&p,&io,now,0,0);}
static void running(void){assert(m.enabled&&!m.fault&&p.active&&h.value==J72_TRIAL&&m.mode==J72_RUNNING);}
static void stopped(void){assert(!p.active&&!p.touched&&p.restored&&!p.restore_failed&&h.value==J72_HANDOFF);}
int main(void){
 reset();m.enabled=false;step(1000);assert(h.writes==0&&h.reads==0);cases++;
 reset();m.sample[1]=100;m.sample[3]=4274000;step(1000);assert(m.enabled&&!m.fault&&!p.active&&h.writes==0&&m.mode==J72_WAIT_FULL);cases++;
 reset();step(1000);running();assert(m.cycles==1);cases++;
 m.sample[1]=96;step(2000);stopped();assert(m.enabled&&m.mode==J72_WAIT_FULL);m.sample[1]=90;step(31999);assert(!p.active);step(32000);running();assert(m.cycles==2);cases++;
 m.sample[2]=381;step(33000);stopped();assert(m.mode==J72_WAIT_COOL);m.sample[2]=366;step(64000);assert(!p.active);m.sample[2]=365;step(65000);running();assert(m.cycles==3);cases++;
 reset();step(1000);m.sample[3]=4200001;step(2000);stopped();m.sample[3]=4100001;step(40000);assert(!p.active);m.sample[3]=4100000;step(41000);running();cases++;
 reset();step(1000);m.sample_at_ms=1000;j72_maintain_step(&m,&p,&io,7000,0,0);stopped();assert(m.fault&&!m.enabled);unsigned writes=h.writes;step(8000);assert(h.writes==writes);cases++;
 reset();step(1000);m.sample_error=-EIO;step(2000);stopped();assert(m.fault&&m.error==-EIO);cases++;
 reset();step(1000);j72_maintain_step(&m,&p,&io,1100,-ETIME,0);stopped();assert(m.fault&&!m.enabled);cases++;
 reset();step(1000);j72_maintain_step(&m,&p,&io,1100,0,-EPERM);stopped();assert(m.fault);cases++;
 int bad[][2]={{0,0},{1,9},{1,101},{2,199},{2,501},{3,3499999},{3,4400001},{4,-1500001},{4,1500001}};
 for(unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);i++){reset();step(1000);m.sample[bad[i][0]]=bad[i][1];step(2000);stopped();assert(m.fault&&!m.enabled);cases++;}
 reset();step(1000);h.fail_restore=true;m.sample[1]=96;step(2000);assert(m.fault&&!m.enabled&&p.restore_failed&&h.restores==3);writes=h.writes;step(50000);assert(h.writes==writes);cases++;
 reset();h.value=0x03;step(1000);assert(m.fault&&h.overrides==0);cases++;
 reset();h.write_error=-EIO;step(1000);assert(m.fault&&!m.enabled&&p.restore_failed);cases++;
 reset();step(1000);u64 end=p.deadline_ms;step(end);stopped();assert(m.mode==J72_WAIT_WINDOW&&m.stopped_at_ms==end);step(end+29999);assert(!p.active);step(end+30000);running();assert(m.cycles==2);cases++;
 reset();step(1000);m.sample_at_ms=5000;j72_maintain_step(&m,&p,&io,2000,0,0);stopped();assert(m.fault);cases++;
 reset();m.sample_valid=false;step(1000);assert(m.fault&&h.overrides==0);cases++;
 reset();m.sample[1]=91;step(1000);assert(!p.active&&h.overrides==0);m.sample[1]=90;step(2000);running();cases++;
 reset();step(1000);h.value=0x3e;step(2000);stopped();assert(m.fault);cases++;
 reset();step(1000);m.enabled=false;j72_maintain_pause(&m,&p,&io,2000,J72_OFF,0,false);stopped();assert(!m.enabled);cases++;
 reset();step(1000);j72_maintain_step(&m,&p,&io,1100,-ETIME,0);j72_maintain_pause(&m,&p,&io,1200,J72_OFF,0,false);assert(m.fault&&!m.enabled&&m.error==-ETIME);cases++;
 reset();step(1000);j72_maintain_step(&m,&p,&io,1100,-ETIME,0);m.sample_at_ms=1200;assert(j72_maintain_requalify(&m,&p,&io,1200,0,0)==0);assert(!m.fault&&!m.enabled&&!p.active&&h.value==J72_HANDOFF);cases++;
 reset();step(1000);j72_maintain_step(&m,&p,&io,1100,-ETIME,0);m.sample_at_ms=1200;assert(j72_maintain_requalify(&m,&p,&io,1200,-ETIME,0)!=0&&m.fault);cases++;
 reset();step(1000);h.fail_restore=true;j72_maintain_step(&m,&p,&io,1100,-ETIME,0);m.sample_at_ms=1200;assert(j72_maintain_requalify(&m,&p,&io,1200,0,0)!=0&&m.fault);cases++;
 reset();step(1000);assert(j72_maintain_requalify(&m,&p,&io,1100,0,0)!=0&&p.active);cases++;
 reset();step(1000);j72_maintain_step(&m,&p,&io,1100,-ETIME,0);m.sample_at_ms=1200;h.value=0x03;assert(j72_maintain_requalify(&m,&p,&io,1200,0,0)!=0&&m.fault);cases++;
 reset();step(1000);j72_maintain_step(&m,&p,&io,1100,-ETIME,0);m.sample_at_ms=1200;m.sample[0]=0;assert(j72_maintain_requalify(&m,&p,&io,1200,0,0)!=0&&m.fault);cases++;
 printf("PASS: %u actual-core maintenance scenarios; unchanged active pack limits; bounded windows; restoration/fault checks\n",cases);
 return 0;
}
