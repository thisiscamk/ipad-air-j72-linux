/* SPDX-License-Identifier: GPL-2.0-only */
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include "j72-recovery-window.h"
int main(void)
{
 struct j72_recovery_window w={0}, saved;
 for(unsigned i=0;i<6;i++)assert(j72_recovery_admit(&w,1000+i));
 saved=w;
 assert(!j72_recovery_admit(&w,60999));
 assert(w.count==saved.count && w.next==saved.next);
 assert(j72_recovery_admit(&w,61000)); /* exact oldest expiry */
 assert(!j72_recovery_admit(&w,61000)); /* next-oldest still live */
 assert(j72_recovery_admit(&w,61001));
 assert(!j72_recovery_admit(&w,61000)); /* clock reversal refuses */
 w=(struct j72_recovery_window){0};
 for(unsigned i=0;i<1000;i++)assert(j72_recovery_admit(&w,60000ULL*i));
 w=(struct j72_recovery_window){0};
 for(unsigned i=0;i<6;i++)assert(j72_recovery_admit(&w,0));
 assert(!j72_recovery_admit(&w,0));
 assert(j72_recovery_admit(&w,60000));
 w=(struct j72_recovery_window){0};
 for(unsigned i=0;i<6;i++)assert(j72_recovery_admit(&w,ULLONG_MAX-5+i));
 assert(!j72_recovery_admit(&w,0)); /* no unsigned-wrap escape */
 w=(struct j72_recovery_window){.count=7};
 assert(!j72_recovery_admit(&w,1));
 w=(struct j72_recovery_window){.next=6};
 assert(!j72_recovery_admit(&w,1));
 puts("PASS: burst cap, exact boundary, rolling expiry, isolated longevity, monotonic and invalid-state guards");
}
