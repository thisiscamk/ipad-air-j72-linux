#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exercise actual firmware-write and shutdown gates under host stubs."""
from pathlib import Path
import re,subprocess
root=Path(__file__).resolve().parent
s=(root/'src/drivers/block/asp.c').read_text()
def function(name,kind):
 m=re.search(r'^static '+kind+' '+name+r'\([^;{}]*\)\n\{.*?^\}',s,re.S|re.M)
 assert m,name
 return m.group()+'\n'
pre=r'''
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <errno.h>
typedef uint64_t u64;
#define SZ_64M (64ULL<<20)
#define BIT_ULL(n) (1ULL<<(n))
#define AKF_V1_REMAP_AP_LO 8
#define AKF_V1_REMAP_AP_HI 12
#define AKF_V1_REMAP_IOP_LO 16
#define AKF_V1_REMAP_IOP_HI 20
#define AKF_V1_REMAP_SZ_LO 24
#define AKF_V1_REMAP_SZ_HI 28
#define AKF_V1_ENDIANNESS 32
#define AKF_V1_CPU_CONTROL 40
#define AKF_V1_LITTLE_ENDIAN 1
#define AKF_V1_CPU_CONTROL_START 16
#define WRITE_ONCE(v,n) ((v)=(n))
#define dev_dbg(...) ((void)0)
#define dev_notice(...) ((void)0)
#define dev_err_probe(dev,code,...) (code)
struct device_node {int unused;};
struct device {struct device_node *of_node;};
struct reserved_mem {u64 base,size;};
struct apple_asp {struct device* dev;void*akf_base;bool failed;};
struct platform_device {struct device dev;struct apple_asp *data;};
static struct device_node node;
static struct reserved_mem reserved;
static u64 base,size;static int missing_index,missing_node,missing_reg,missing_reserved,no_map,writes,node_puts,cases;
static int of_property_match_string(struct device_node*n,const char*a,const char*b){(void)n;(void)a;(void)b;return missing_index?-1:0;}
static struct device_node*of_parse_phandle(struct device_node*n,const char*a,int i){(void)n;(void)a;(void)i;return missing_node?NULL:&node;}
static int of_property_read_reg(struct device_node*n,int i,u64*b,u64*s){(void)n;(void)i;*b=base;*s=size;return missing_reg?-1:0;}
static struct reserved_mem*of_reserved_mem_lookup(struct device_node*n){assert(n==&node);return missing_reserved?NULL:&reserved;}
static bool of_property_read_bool(struct device_node*n,const char*a){(void)n;(void)a;return no_map;}
static void of_node_put(struct device_node*n){assert(n==&node);node_puts++;}
static void writel(unsigned value,void*p){(void)value;(void)p;writes++;}
static struct apple_asp *platform_get_drvdata(struct platform_device*p){return p->data;}
static void reset(void){base=0x830000000ULL;size=0x100000;reserved=(struct reserved_mem){base,size};missing_index=missing_node=missing_reg=missing_reserved=writes=node_puts=0;no_map=1;}
'''
main=r'''
int main(void){
 struct device d={&node};struct apple_asp asp={.dev=&d,.akf_base=(void*)4096};
 for(int i=0;i<13;i++){
  reset();
  switch(i){case 0:missing_index=1;break;case 1:missing_node=1;break;case 2:missing_reg=1;break;case 3:missing_reserved=1;break;case 4:no_map=0;break;case 5:reserved.base+=4096;break;case 6:reserved.size+=4096;break;case 7:base=reserved.base=0;break;case 8:size=reserved.size=0;break;case 9:size=reserved.size=SZ_64M+4096;break;case 10:base=reserved.base=base+1;break;case 11:base=reserved.base=1ULL<<40;break;case 12:base=reserved.base=(1ULL<<40)-4096;break;}
  assert(apple_asp_setup_firmware(&asp)<0&&writes==0);assert(node_puts==(i<2?0:1));cases++;
 }
 reset();assert(apple_asp_setup_firmware(&asp)==0&&writes==8&&node_puts==1);cases++;
 struct platform_device p={0};apple_asp_remove(&p);cases++;
 for(int i=0;i<3;i++){asp.failed=i!=0;p.data=&asp;int before=writes;apple_asp_remove(&p);assert(asp.failed&&writes==before);cases++;}
 printf("PASS: %d actual firmware/shutdown gate cases; invalid handoff performs no MMIO writes\n",cases);return 0;
}
'''
p=root/'test-asp-firmware.c';p.write_text(pre+function('apple_asp_setup_firmware','int')+function('apple_asp_remove','void')+main)
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',str(p),'-o',str(root/'test-asp-firmware')],check=True,timeout=30)
r=subprocess.run([str(root/'test-asp-firmware')],capture_output=True,text=True,timeout=10);assert r.returncode==0,r.stderr
(root/'test-asp-firmware-result.txt').write_text(r.stdout);print(r.stdout,end='')
