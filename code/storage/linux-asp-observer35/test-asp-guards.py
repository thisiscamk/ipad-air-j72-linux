#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Actual candidate ASP submission/SGL/queue functions under host stubs."""
from pathlib import Path
import re,subprocess
ROOT=Path(__file__).resolve().parent
source=(ROOT/'src/drivers/block/asp.c').read_text()
def function(name):
 m=re.search(r'^static (?:blk_status_t|void) '+name+r'\([^;{}]*\)\n\{.*?^\}',source,re.S|re.M)
 assert m,name
 return m.group()+'\n'
pre=r'''
#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <errno.h>
#include "src/drivers/block/j72-asp-bounds.h"
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;typedef uint64_t u64;typedef uint64_t dma_addr_t;typedef int blk_status_t;
#define ASP_NUM_TAGS 16
#define ASP_TAG_SIZE 16320
#define ASP_CMD_HDR_SIZE 48
#define ASP_CMD_MAX_SECTORS 4068
#define ASP_LBA_SHIFT 12
#define ASP_LBA_SIZE 4096
#define ASP_CMD_IDENTIFY 0
#define ASP_CMD_READ_USERAREA 16
#define ASP_CMD_IO_FLAG_NO_ENCRYPTION 8
#define BLK_STS_OK 0
#define BLK_STS_IOERR 1
#define BLK_STS_NOTSUPP 2
#define BLK_STS_TIMEOUT 3
#define ASP_MSG_TYPE 0xf
#define ASP_MSG_TYPE_SUBMIT 3
#define ASP_SUBMIT_TAG 0xf00
#define ASP_SUBMIT_OP 0xf000
#define ASP_SUBMIT_OP_RING 1
#define FIELD_PREP(mask,value) (((u64)(value) << __builtin_ctzll(mask)) & (mask))
#define WARN_ON(value) (value)
#define READ_ONCE(value) (value)
#define WRITE_ONCE(value,newvalue) ((value)=(newvalue))
#define dev_err(...) ((void)0)
struct asp_cmd_hdr {u8 op,tag;u16 flags;u32 slba,length;u8 pad[36];} __attribute__((packed));
struct scatterlist {dma_addr_t address;unsigned len;};
struct asp_iod {struct asp_cmd_hdr cmd;int nr_mapped;struct scatterlist *sg;int nents;};
struct apple_asp {bool failed;u64 capacity;void *rtk,*dev,*iod_mempool;unsigned ep;};
struct asp_queue {int unused;};
struct queue {struct asp_queue *queuedata;};
struct request {struct asp_iod *pdu;};
struct blk_mq_hw_ctx {struct queue *queue;};
struct blk_mq_queue_data {struct request *rq;};
#define for_each_sg(list,sg,n,i) for ((i)=0,(sg)=(list);(i)<(n);(i)++,(sg)++)
#define sg_dma_len(sg) ((sg)->len)
#define sg_dma_address(sg) ((sg)->address)
static unsigned char dma[ASP_NUM_TAGS*ASP_TAG_SIZE];
static unsigned sends,barriers,hdr_ptr_calls,sgl_ptr_calls,started,unmapped,freed,cases;
static int send_result,setup_result;
static struct apple_asp asp;
static struct apple_asp *queue_to_apple_asp(struct asp_queue *q){assert(q);return &asp;}
static void *asp_q_cmd_hdr(struct apple_asp *a,struct asp_cmd_hdr *c){assert(a==&asp&&c->tag<16);hdr_ptr_calls++;return dma+c->tag*ASP_TAG_SIZE;}
static void *asp_q_cmd_data(struct apple_asp *a,struct asp_cmd_hdr *c){assert(a==&asp&&c->tag<16);sgl_ptr_calls++;return dma+c->tag*ASP_TAG_SIZE+48;}
static void dma_wmb(void){barriers++;}
static int apple_rtkit_send_message(void*a,unsigned ep,u64 msg,void*b,bool wait){(void)a;(void)ep;(void)msg;(void)b;(void)wait;sends++;return send_result;}
static struct asp_iod *blk_mq_rq_to_pdu(struct request*r){return r->pdu;}
static blk_status_t asp_setup_cmd(struct asp_queue*q,struct request*r){(void)q;(void)r;return setup_result;}
static int rq_dma_dir(struct request*r){(void)r;return 0;}
static void dma_unmap_sg(void*d,void*sg,int n,int direction){(void)d;(void)sg;(void)n;(void)direction;unmapped++;}
static void mempool_free(void*p,void*pool){(void)p;(void)pool;freed++;}
static void blk_mq_start_request(struct request*r){(void)r;started++;}
static void reset(void){memset(&asp,0,sizeof(asp));asp.capacity=100000;memset(dma,0xaa,sizeof(dma));sends=barriers=hdr_ptr_calls=sgl_ptr_calls=started=unmapped=freed=0;send_result=setup_result=0;}
'''
main=r'''
int main(void){
 struct asp_cmd_hdr cmd;
 for(unsigned op=0;op<256;op++){
  reset();memset(&cmd,0,sizeof(cmd));cmd.op=op;
  if(op==16){cmd.flags=8;cmd.length=1;}
  bool ok=op==0||op==16;
  assert((apple_asp_submit_cmd(&asp,&cmd)==0)==ok);
  assert(sends==(unsigned)ok&&hdr_ptr_calls==(unsigned)ok&&barriers==(unsigned)ok);cases++;
 }
 for(unsigned i=0;i<8;i++){
  reset();memset(&cmd,0,sizeof(cmd));cmd.op=16;cmd.flags=8;cmd.length=1;
  if(i==0)cmd.tag=16;if(i==1)cmd.tag=255;if(i==2)cmd.slba=100000;if(i==3)cmd.length=0;
  if(i==4)cmd.length=4069;if(i==5)cmd.flags=0;if(i==6)asp.capacity=0;if(i==7)asp.failed=true;
  assert(apple_asp_submit_cmd(&asp,&cmd)!=0&&sends==0&&hdr_ptr_calls==0&&barriers==0);cases++;
 }
 struct scatterlist sg[2];struct asp_iod iod;
 for(unsigned i=0;i<9;i++){
  reset();memset(&iod,0,sizeof(iod));iod.cmd.op=16;iod.cmd.length=1;iod.nr_mapped=1;iod.sg=sg;sg[0]=(struct scatterlist){4096,4096};
  if(i==0)sg[0].len=0;if(i==1)sg[0].len=1;if(i==2)sg[0].len=4097;if(i==3)sg[0].address=4097;
  if(i==4)sg[0].address=1ULL<<40;if(i==5)sg[0].len=4069*4096;if(i==6)iod.cmd.tag=16;
  if(i==7)iod.cmd.length=2;if(i==8)iod.cmd.op=0x30;
  assert(asp_setup_hw_sgl(&asp,&iod)!=0&&sgl_ptr_calls==0);for(unsigned j=0;j<sizeof(dma);j++)assert(dma[j]==0xaa);cases++;
 }
 reset();memset(&iod,0,sizeof(iod));iod.cmd.op=16;iod.cmd.tag=15;iod.cmd.length=3;iod.nr_mapped=2;iod.sg=sg;
 sg[0]=(struct scatterlist){4096,8192};sg[1]=(struct scatterlist){16384,4096};
 assert(asp_setup_hw_sgl(&asp,&iod)==0);u32 *pfns=(u32*)(dma+15*ASP_TAG_SIZE+48);assert(pfns[0]==1&&pfns[1]==2&&pfns[2]==4);cases++;
 reset();iod.cmd.tag=0;iod.cmd.length=4068;iod.nr_mapped=1;sg[0]=(struct scatterlist){4096,4068*4096};assert(asp_setup_hw_sgl(&asp,&iod)==0);cases++;
 reset();iod.cmd.length=1;sg[0]=(struct scatterlist){(1ULL<<40)-4096,4096};assert(asp_setup_hw_sgl(&asp,&iod)==0);cases++;
 /* A malformed SGL never starts/submits; a delivery ambiguity retains DMA. */
 struct asp_queue aq={0};struct queue q={&aq};struct blk_mq_hw_ctx hw={&q};struct request request={&iod};struct blk_mq_queue_data bd={&request};
 reset();iod.cmd=(struct asp_cmd_hdr){.op=16,.flags=8,.length=1};iod.sg=sg;iod.nr_mapped=iod.nents=1;sg[0]=(struct scatterlist){4097,4096};
 assert(apple_asp_queue_rq(&hw,&bd)!=0&&started==0&&sends==0&&unmapped==1&&freed==1&&iod.sg==NULL);cases++;
 reset();iod.cmd=(struct asp_cmd_hdr){.op=16,.flags=8,.length=1};iod.sg=sg;iod.nr_mapped=iod.nents=1;sg[0]=(struct scatterlist){4096,4096};send_result=-ETIMEDOUT;
 assert(apple_asp_queue_rq(&hw,&bd)==0&&started==1&&sends==1&&asp.failed&&unmapped==0&&freed==0);cases++;
 assert(apple_asp_queue_rq(&hw,&bd)!=0&&sends==1);cases++;
 assert(j72_asp_request_valid(100,99*8,4096));cases++;
 u64 bad[][3]={{0,0,4096},{0x100000001ULL,0,4096},{100,1,4096},{100,800,4096},{100,792,8192},{100,0,0},{100,0,4097},{100,0,4069*4096},{0x100000000ULL,0x800000000ULL,4096}};
 for(unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);i++){assert(!j72_asp_request_valid(bad[i][0],bad[i][1],bad[i][2]));cases++;}
 printf("PASS: %u actual ASP function/bounds cases under host stubs\n",cases);return 0;
}
'''
p=ROOT/'test-asp-guards.c';p.write_text(pre+function('apple_asp_submit_cmd')+function('asp_setup_hw_sgl')+function('apple_asp_queue_rq')+main)
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','-fsanitize=undefined','-fno-sanitize-recover=all',str(p),'-o',str(ROOT/'test-asp-guards')],check=True,timeout=30)
r=subprocess.run([str(ROOT/'test-asp-guards')],capture_output=True,text=True,timeout=10);assert r.returncode==0,r.stderr
(ROOT/'test-asp-guards-result.txt').write_text(r.stdout);print(r.stdout,end='')
