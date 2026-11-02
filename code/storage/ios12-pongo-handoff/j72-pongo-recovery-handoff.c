/* SPDX-License-Identifier: MIT
 * Exact-J72 RAM recovery staging. No disk/MMIO/kernel patch/boot interface.
 * The host chooses a separate boot only after staging and postconditions pass.
 */
typedef unsigned long size_t;
typedef unsigned long long u64;
typedef unsigned u32;
typedef struct {u32 properties,children;char data[];} dt_node;
struct boot_args12 {unsigned short revision,version;u32 pad0;u64 virt,phys,size,top;
 u64 video[6];u32 machine,pad1;u64 dtptr;u32 dtlen;char args[256];u32 pad2;u64 flags,actual;};
struct memmap {u64 addr,size;};
_Static_assert(__builtin_offsetof(struct boot_args12,args)==108,"iOS12 ABI");
extern struct boot_args12 *gBootArgs;
extern dt_node *gDeviceTree;
extern void *gEntryPoint;
extern u64 gTopOfKernelData;
extern u32 socnum,loader_xfer_recv_count,ramdisk_size;
extern unsigned char *loader_xfer_recv_data;
extern void *ramdisk_buf;
extern int dt_check(void*,size_t,size_t*) __asm__("_dt_check$64");
extern int dt_parse(dt_node*,int,size_t*,int(*)(void*,dt_node*,int),void*,int(*)(void*,dt_node*,int,const char*,void*,size_t),void*) __asm__("_dt_parse$64");
extern void *dt_prop(dt_node*,const char*,size_t*) __asm__("_dt_prop$64");
extern dt_node *dt_find(dt_node*,const char*);
extern struct memmap *dt_alloc_memmap(dt_node*,const char*);
extern void *alloc_static(u32);
extern void *memcpy(void*,const void*,size_t);
extern int memcmp(const void*,const void*,size_t);
extern void task_yield(void);
extern void command_register(const char*,const char*,void(*)(const char*,char*));
extern void command_puts(const char*);
#include "j72-pongo-recovery-handoff-bounds.h"
#include "j72-pongo-recovery-handoff-private.h"
static int eq(const char*a,const char*b){while(*a&&*a==*b){a++;b++;}return *a==*b;}
static int prefix(const char*a,const char*b){while(*b)if(*a++!=*b++)return 0;return 1;}
static void value(const char*key,u64 v){char row[80];unsigned n=0;while(*key&&n<60)row[n++]=*key++;row[n++]=' ';for(unsigned i=0;i<16;i++)row[n++]="0123456789abcdef"[(v>>(60-i*4))&15];row[n]=0;command_puts(row);}
static unsigned phase,attempted,staged;
static void refuse(void){command_puts("J72_HANDOFF_REFUSED");value("PHASE",phase);command_puts("J72_HANDOFF_END");}
struct slots {unsigned properties,reserved,empty;};
static int inspect(void*context,dt_node*n,int depth,const char*key,void*val,size_t len){
 (void)n;(void)depth;struct slots*s=context;if(++s->properties>128)return -1;
 if(prefix(key,"MemoryMapReserved-")){
  if(len!=16)return -1;
  s->reserved++;if(!j72_u64(val)&&!j72_u64((unsigned char*)val+8))s->empty++;
 }
 return 0;
}
static dt_node*guard(struct memmap**tc){
 phase=1;if(socnum!=0x8960||!gBootArgs||!gDeviceTree)return 0;
 struct boot_args12*b=gBootArgs;
 if(b->phys<0x800000000ULL||b->size<0x10000000||b->size>0x40000000||b->dtlen<64||b->dtlen>0x100000||b->dtptr<b->virt||b->dtptr-b->virt>~0ULL-b->phys)return 0;
 u64 physical=b->dtptr-b->virt+b->phys;
 phase=2;if(!j72_span(b->phys,b->size,physical,b->dtlen)||(u64)gDeviceTree!=physical-0x800000000ULL+0x400000000ULL||dt_check(gDeviceTree,b->dtlen,0))return 0;
 size_t len=0;const char*model=dt_prop(gDeviceTree,"model",&len);
 phase=3;if(!model||len!=8||!eq(model,"iPad4,2")||!j72_span(b->phys,b->size,(u64)gEntryPoint,4)||!j72_span(b->phys,b->size,gTopOfKernelData,1))return 0;
 dt_node*map=dt_find(gDeviceTree,"/chosen/memory-map");if(!map)return 0;
 struct memmap*text=dt_prop(map,"Kernel-__TEXT",&len);
 phase=4;if(!text||len!=16||!j72_span(b->phys,b->size,text->addr,text->size))return 0;
 unsigned char uuid[16];if(!j72_macho_uuid((void*)(text->addr-0x800000000ULL+0x400000000ULL),text->size,uuid)||!j72_bytes_equal(uuid,expected_uuid,16))return 0;
 *tc=dt_prop(map,"TrustCache",&len);
 phase=5;if(!*tc||len!=16||!j72_span(b->phys,b->size,(*tc)->addr,(*tc)->size))return 0;
 return map;
}
static int original(dt_node*map,struct memmap*tc){
 struct boot_args12*b=gBootArgs;struct slots s={0};phase=6;
 if(dt_parse(map,-1,0,0,0,inspect,&s)||!s.reserved||s.reserved!=s.empty||ramdisk_buf||ramdisk_size)return 0;
 size_t len=0;if(dt_prop(map,"RAMDisk",&len))return 0;
 if(tc->size<ORIGINAL_TC_USED||tc->size>65536)return 0;
 unsigned char digest[32];j72_sha256((void*)(tc->addr-0x800000000ULL+0x400000000ULL),ORIGINAL_TC_USED,digest,0);
 phase=7;if(!j72_bytes_equal(digest,expected_original_tc_sha,32))return 0;
 unsigned arglen=0;while(arglen<256&&b->args[arglen])arglen++;if(arglen==256)return 0;
 u64 top=(gTopOfKernelData+0x3fff)&~0x3fffULL;
 u64 need=((TC_SIZE+0x3fff)&~0x3fffULL)+((HFS_SIZE+0x3fff)&~0x3fffULL);
 phase=8;if(!j72_span(b->phys,b->size,top,need+0x10000000))return 0;
 return 1;
}
static void check(const char*command,char*args){
 (void)command;if(*args){refuse();return;}
 struct memmap*tc=0;dt_node*map=guard(&tc);
 if(!map||attempted||!original(map,tc)){refuse();return;}
 command_puts("J72_HANDOFF_CHECK_OK");value("ORIGINAL_TC_MATCH",1);value("DISK_IO",0);command_puts("J72_HANDOFF_END");
}
static unsigned char *new_tc,*new_hfs;
static int postconditions(void){
 struct memmap*tc=0;dt_node*map=guard(&tc);if(!map||!staged)return 0;
 size_t len=0;struct memmap*rd=dt_prop(map,"RAMDisk",&len);
 if(!rd||len!=16||tc->addr!=(u64)new_tc-0x400000000ULL+0x800000000ULL||tc->size!=TC_SIZE||rd->addr!=(u64)new_hfs-0x400000000ULL+0x800000000ULL||rd->size!=((HFS_SIZE+0xfff)&~0xfffULL)||ramdisk_size||ramdisk_buf)return 0;
 const char*line=RAM_BOOTARGS;
 for(unsigned i=0;i<256;i++){
  char expected=*line;if(expected)line++;
  if(gBootArgs->args[i]!=expected)return 0;
 }
 return !gBootArgs->video[1];
}
static void status(const char*command,char*args){
 (void)command;phase=20;
 if(*args||!postconditions()){refuse();return;}
 command_puts("J72_HANDOFF_STAGE_OK");value("RAMDISK_BYTES",HFS_SIZE);value("TRUSTCACHE_BYTES",TC_SIZE);value("DISK_IO",0);command_puts("J72_HANDOFF_END");
}
static void stage(const char*command,char*args){
 (void)command;if(*args||attempted){refuse();return;}
 struct memmap*tc=0;dt_node*map=guard(&tc);if(!map||!original(map,tc)){refuse();return;}
 struct boot_args12*b=gBootArgs;
 phase=9;if(!loader_xfer_recv_data||loader_xfer_recv_count!=BUNDLE_SIZE||(u64)loader_xfer_recv_data<0x400000000ULL||(u64)loader_xfer_recv_data>=0x500000000ULL)return refuse();
 u64 upload=(u64)loader_xfer_recv_data-0x400000000ULL+0x800000000ULL;
 if(!j72_span(b->phys,b->size,upload,BUNDLE_SIZE))return refuse();
 phase=10;if(!j72_bundle(loader_xfer_recv_data,BUNDLE_SIZE,BUNDLE_SIZE,TC_OFFSET,TC_SIZE,HFS_OFFSET,HFS_SIZE,expected_bundle_sha,task_yield))return refuse();
 u64 start=(gTopOfKernelData+0x3fff)&~0x3fffULL;
 u64 tc_alloc=(TC_SIZE+0x3fff)&~0x3fffULL,hfs_alloc=(HFS_SIZE+0x3fff)&~0x3fffULL,end=start+tc_alloc+hfs_alloc;
 phase=11;if(!(end<=upload||upload+BUNDLE_SIZE<=start))return refuse();
 /* From here, failure requires a fresh boot. No retry of partial allocations. */
 attempted=1;new_tc=alloc_static((u32)tc_alloc);new_hfs=alloc_static((u32)hfs_alloc);
 phase=12;if((u64)new_tc!=start-0x800000000ULL+0x400000000ULL||(u64)new_hfs!=(start+tc_alloc)-0x800000000ULL+0x400000000ULL||gTopOfKernelData!=end)return refuse();
 for(u64 i=0;i<tc_alloc;i++)new_tc[i]=0;
 for(u64 i=HFS_SIZE;i<hfs_alloc;i++)new_hfs[i]=0;
 memcpy(new_tc,loader_xfer_recv_data+TC_OFFSET,TC_SIZE);memcpy(new_hfs,loader_xfer_recv_data+HFS_OFFSET,HFS_SIZE);
 phase=13;if(memcmp(new_tc,loader_xfer_recv_data+TC_OFFSET,TC_SIZE)||memcmp(new_hfs,loader_xfer_recv_data+HFS_OFFSET,HFS_SIZE))return refuse();
 /* Commit only RAM handoff metadata after both copies have been verified. */
 struct memmap*rd=dt_alloc_memmap(map,"RAMDisk");phase=14;if(!rd)return refuse();
 rd->addr=(u64)new_hfs-0x400000000ULL+0x800000000ULL;rd->size=(HFS_SIZE+0xfff)&~0xfffULL;
 tc->addr=(u64)new_tc-0x400000000ULL+0x800000000ULL;tc->size=TC_SIZE;
 const char*line=RAM_BOOTARGS;
 for(unsigned i=0;i<256;i++){b->args[i]=*line;if(*line)line++;}
 b->video[1]=0;staged=1;status(command,args);
}
void module_entry(void){
 command_register("j72rescuecheck","guarded RAM recovery preflight",check);
 command_register("j72rescuestage","stage exact recovery image in RAM only",stage);
 command_register("j72rescuestatus","verify RAM recovery handoff",status);
}
char *module_name="j72_recovery_handoff";
struct pongo_exports {const char*name;void*value;};
struct pongo_exports exported_symbols[]={{0,0}};
