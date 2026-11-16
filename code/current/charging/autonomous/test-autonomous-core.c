#include <assert.h>
#include <stdio.h>
#include "j72-maintain-core.h"

struct fake { unsigned int value, writes, last; };
static int rd(void *ctx, unsigned int *v) { *v=((struct fake *)ctx)->value; return 0; }
static int wr(void *ctx, unsigned int v) { struct fake *f=ctx; f->writes++; f->last=f->value=v; return 0; }

static void safe_sample(struct j72_maintain *m, u64 now, int soc)
{
 int v[5]={1,soc,340,3900000,-400000};
 for (int i=0;i<5;i++) m->sample[i]=v[i];
 m->enabled=true; m->sample_valid=true; m->sample_at_ms=now;
}

int main(void)
{
 struct fake f={.value=J72_HANDOFF};
 struct j72_limit_io io={.ctx=&f,.read=rd,.write=wr};
 struct j72_limit_state p={0}; struct j72_maintain m={0};
 safe_sample(&m,1000,50);
 assert(j72_maintain_step(&m,&p,&io,1000,0,0)==0);
 assert(p.active && m.mode==J72_RUNNING && f.value==J72_TRIAL);
 assert(j72_maintain_step(&m,&p,&io,1200,-ENOTCONN,0)==0);
 assert(!p.active && p.restored && !m.fault && m.enabled);
 assert(m.mode==J72_WAIT_START && f.value==J72_HANDOFF);
 m.sample_at_ms=2200;
 assert(j72_maintain_step(&m,&p,&io,2200,0,-EPERM)==0);
 assert(!p.active && p.restored && !m.fault && m.enabled);
 assert(m.mode==J72_WAIT_START && f.value==J72_HANDOFF);
 m.sample_at_ms=32100;
 assert(j72_maintain_step(&m,&p,&io,32100,0,0)==0);
 assert(p.active && m.mode==J72_RUNNING && f.value==J72_TRIAL);
 assert(j72_maintain_step(&m,&p,&io,32200,-EIO,0)==-EIO);
 assert(m.fault && !m.enabled && f.value==J72_HANDOFF);

 f=(struct fake){.value=J72_HANDOFF}; p=(struct j72_limit_state){0}; m=(struct j72_maintain){0};
 safe_sample(&m,1000,98);
 assert(j72_maintain_step(&m,&p,&io,1000,0,0)==0);
 assert(!p.active && m.mode==J72_WAIT_FULL && f.writes==0);
 puts("autonomous charging core tests PASS");
}
