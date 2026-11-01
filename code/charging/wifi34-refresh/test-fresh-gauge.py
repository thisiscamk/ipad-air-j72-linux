#!/usr/bin/env python3
"""Compile the actual fresh-gauge retry and pack guard with synthetic reads."""
from pathlib import Path
import subprocess
import tempfile

WORK=Path(__file__).resolve().parent
source=(WORK/'module/j72_input_limit_hub1050_refresh34.c').read_text()
a=source.index('static int pack_values(')
b=source.index('\nstatic void finish_locked',a)
head=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "j72-limit-core.h"
#define ARRAY_SIZE(a) (sizeof(a)/sizeof((a)[0]))
enum power_supply_property {POWER_SUPPLY_PROP_PRESENT,POWER_SUPPLY_PROP_CAPACITY,
 POWER_SUPPLY_PROP_TEMP,POWER_SUPPLY_PROP_VOLTAGE_NOW,POWER_SUPPLY_PROP_CURRENT_NOW};
union power_supply_propval {int intval;};
static int battery_obj,*battery=&battery_obj;
static int policy_lock,lock_depth,generation,refreshes,fail_index,fail_errno;
static int persistent,bad_fresh,read_calls[2][5];
static unsigned int read_failures,fresh_refreshes,read_recoveries;
static int last_read_errno,last_failed_prop;
static u64 last_read_failure_ms;
static int guard_values[5],guard_failed_values[5];
static unsigned int guard_faults,guard_failed_faults;
static u64 guard_at_ms,guard_failed_at_ms;
static void mutex_lock(int *p) {assert(p==&policy_lock&&!lock_depth);lock_depth++;}
static void mutex_unlock(int *p) {assert(p==&policy_lock&&lock_depth==1);lock_depth--;}
static u64 now_ms(void) {return 12345;}
static int old_values[5]={0,20,210,3500000,-500000};
static int fresh_values[5]={1,70,350,3900000,300000};
static int power_supply_get_property(int *b,enum power_supply_property prop,union power_supply_propval *v) {
 assert(!lock_depth&&b==battery);read_calls[generation][prop]++;
 if(prop==fail_index&&(!generation||persistent))return fail_errno;
 v->intval=generation?fresh_values[prop]:old_values[prop];
 if(generation&&bad_fresh==prop+1){int bad[]={0,96,381,4200001,1500001};v->intval=bad[prop];}
 return 0;
}
static void *power_supply_get_drvdata(int *b) {assert(!lock_depth&&b==battery);return b;}
static void bq27xxx_battery_update(void *b) {assert(!lock_depth&&b==battery&&!refreshes);refreshes++;generation=1;}
static void reset(int index,int err,int persist) {
 policy_lock=lock_depth=generation=refreshes=bad_fresh=0;
 read_failures=fresh_refreshes=read_recoveries=0;
 last_read_errno=last_failed_prop=last_read_failure_ms=0;
 guard_faults=guard_failed_faults=guard_at_ms=guard_failed_at_ms=0;
 memset(read_calls,0,sizeof(read_calls));memset(guard_values,0,sizeof(guard_values));
 fail_index=index;fail_errno=err;persistent=persist;
}
'''
tail=r'''
int main(void) {
 int amps=0,cases=0,errors[]={-ETIMEDOUT,-EIO};
 reset(-1,0,0);old_values[0]=1;
 assert(pack_guard(&amps)==0&&!refreshes&&!read_failures);cases++;
 old_values[0]=0;
 for(int i=0;i<5;i++)for(int e=0;e<2;e++) {
  reset(i,errors[e],0);assert(pack_guard(&amps)==0);
  assert(refreshes==1&&fresh_refreshes==1&&read_recoveries==1&&read_failures==1);
  assert(last_failed_prop==i&&last_read_errno==errors[e]&&last_read_failure_ms==12345);
  assert(!memcmp(guard_values,fresh_values,sizeof(guard_values)));
  for(int p=0;p<5;p++)assert(read_calls[1][p]==1);cases++;
  reset(i,errors[e],1);assert(pack_guard(&amps)==errors[e]);
  assert(refreshes==1&&read_failures==2&&!read_recoveries&&!guard_at_ms);cases++;
 }
 for(int i=0;i<5;i++) {
  reset(i,-ENODEV,0);assert(pack_guard(&amps)==-ENODEV&&!refreshes&&!read_recoveries);cases++;
  reset(1,-ETIMEDOUT,0);bad_fresh=i+1;assert(pack_guard(&amps)==-ERANGE);
  assert(refreshes==1&&read_recoveries==1&&guard_failed_faults);cases++;
 }
 assert(!lock_depth);printf("PASS: %d actual-source fresh-read/restart/persistent-error/range-guard cases; gauge I/O outside policy lock\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='j72-fresh-gauge-') as d:
    p=Path(d);c=p/'test.c';binary=p/'test'
    c.write_text(head+source[a:b]+tail)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Wno-unused-function','-Wno-sign-compare','-Wno-misleading-indentation','-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(WORK/'module'),str(c),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
