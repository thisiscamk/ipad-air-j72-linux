/* SPDX-License-Identifier: GPL-2.0-only */
/* Recorded voltage-pause/late-wait vectors. Policy branch evidence only:
 * currents/temperatures from the old run cannot predict new physical behaviour.
 */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "j72-maintain-core.h"
static unsigned reg=J72_HANDOFF;
static int rd(void *ctx,unsigned *v){(void)ctx;*v=reg;return 0;}
static int wr(void *ctx,unsigned v){(void)ctx;assert(v==J72_HANDOFF||v==J72_TRIAL);reg=v;return 0;}
int main(void){
 struct j72_limit_io io={0,rd,wr};struct j72_limit_state p={0};
 struct j72_maintain m={.enabled=true,.sample_valid=true};
 int first[5]={1,90,345,4035000,-648000};memcpy(m.sample,first,sizeof(first));
 m.sample_at_ms=1000;j72_maintain_step(&m,&p,&io,1000,0,0);assert(p.active);
 int pause[5]={1,92,367,4201000,354000};memcpy(m.sample,pause,sizeof(pause));
 m.sample_at_ms=2000;j72_maintain_step(&m,&p,&io,2000,0,0);assert(!p.active&&p.restored&&m.mode==J72_WAIT_FULL);
 int later[5]={1,90,366,4095000,-638000};memcpy(m.sample,later,sizeof(later));
 m.sample_at_ms=40000;j72_maintain_step(&m,&p,&io,40000,0,0);
 assert(p.active==EXPECT_RESUME);
 if(!EXPECT_RESUME)assert(m.mode==J72_WAIT_COOL);
 printf("PASS: recorded-vector branch replay: resume=%d; no physical net-charge prediction\n",EXPECT_RESUME);
 return 0;
}
