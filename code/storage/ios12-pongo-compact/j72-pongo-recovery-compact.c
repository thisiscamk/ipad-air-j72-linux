/* SPDX-License-Identifier: MIT
 * Compact read-only J72 handoff inventory. Never boots or edits guest state.
 * Boot-args and DT ABI follow the pinned Pongo source. No Apple SDK headers.
 */
typedef unsigned long size_t;
typedef unsigned long long u64;
typedef unsigned u32;
typedef struct {u32 properties,children;char data[];} dt_node;
struct boot_args12 {unsigned short revision,version;u32 pad0;u64 virt,phys,size,top;
 u64 video[6];u32 machine,pad1;u64 dtptr;u32 dtlen;char args[256];u32 pad2;u64 flags,actual;};
_Static_assert(__builtin_offsetof(struct boot_args12,dtptr)==96,"boot-args DT ABI");
_Static_assert(__builtin_offsetof(struct boot_args12,args)==108,"iOS12 command-line ABI");
extern struct boot_args12 *gBootArgs;
extern dt_node *gDeviceTree;
extern void *gEntryPoint;
extern u64 gTopOfKernelData;
extern u32 socnum;
extern int dt_check(void*,size_t,size_t*) __asm__("_dt_check$64");
extern int dt_parse(dt_node*,int,size_t*,int(*)(void*,dt_node*,int),void*,int(*)(void*,dt_node*,int,const char*,void*,size_t),void*) __asm__("_dt_parse$64");
extern void *dt_prop(dt_node*,const char*,size_t*) __asm__("_dt_prop$64");
extern dt_node *dt_find(dt_node*,const char*);
extern void command_register(const char*,const char*,void(*)(const char*,char*));
extern void command_puts(const char*);
#include "j72-pongo-recovery-bounds.h"
static int eq(const char*a,const char*b){while(*a&&*a==*b){a++;b++;}return *a==*b;}
static int prefix(const char*a,const char*b){while(*b)if(*a++!=*b++)return 0;return 1;}
static void value(const char*key,u64 v){char row[80];unsigned n=0;while(*key&&n<60)row[n++]=*key++;row[n++]=' ';for(unsigned i=0;i<16;i++)row[n++]="0123456789abcdef"[(v>>(60-i*4))&15];row[n]=0;command_puts(row);}
static void fail(void){command_puts("J72_COMPACT_REFUSED");}
struct inventory {u64 properties,maps,metadata,reserved,empty,tc,tc_size,text,text_size;unsigned tc_seen,text_seen;};
static int inspect(void*context,dt_node*node,int depth,const char*key,void*val,size_t len){
 (void)node;(void)depth;struct inventory*i=context;
 if(++i->properties>128)return -1;
 if(eq(key,"name"))return 0;
 if(prefix(key,"MemoryMapReserved-")){
  if(len!=16)return -1;
  i->reserved++;
  if(!j72_u64(val)&&!j72_u64((unsigned char*)val+8))i->empty++;
 }
 if(len!=16){i->metadata++;return 0;}
 i->maps++;
 if(eq(key,"TrustCache")){
  if(i->tc_seen++)return -1;
  i->tc=j72_u64(val);i->tc_size=j72_u64((unsigned char*)val+8);
 }
 if(eq(key,"Kernel-__TEXT")){
  if(i->text_seen++)return -1;
  i->text=j72_u64(val);i->text_size=j72_u64((unsigned char*)val+8);
 }
 return 0;
}
static void probe(const char*command,char*args){
 (void)command;while(*args==' ')args++;
 if(*args||socnum!=0x8960||!gBootArgs||!gDeviceTree){fail();return;}
 struct boot_args12*b=gBootArgs;
 if(b->phys<0x800000000ULL||b->size>0x40000000ULL||b->size<0x10000000ULL||b->dtlen<64||b->dtlen>0x100000||b->dtptr<b->virt||b->dtptr-b->virt>~0ULL-b->phys){fail();return;}
 u64 dtphys=b->dtptr-b->virt+b->phys;
 if(!j72_span(b->phys,b->size,dtphys,b->dtlen)||(u64)gDeviceTree!=dtphys-0x800000000ULL+0x400000000ULL||dt_check(gDeviceTree,b->dtlen,0)){fail();return;}
 size_t len=0;const char*model=dt_prop(gDeviceTree,"model",&len);
 if(!model||len!=8||!eq(model,"iPad4,2")||!j72_span(b->phys,b->size,(u64)gEntryPoint,4)||!j72_span(b->phys,b->size,gTopOfKernelData,1)){fail();return;}
 unsigned arglen=0;while(arglen<sizeof(b->args)&&b->args[arglen])arglen++;
 if(arglen==sizeof(b->args)){fail();return;}
 dt_node*map=dt_find(gDeviceTree,"/chosen/memory-map");struct inventory i={0};
 if(!map||dt_parse(map,-1,0,0,0,inspect,&i)||i.tc_seen!=1||i.text_seen!=1||!i.reserved||i.empty!=i.reserved||!j72_span(b->phys,b->size,i.tc,i.tc_size)||!j72_span(b->phys,b->size,i.text,i.text_size)||i.text_size<32){fail();return;}
 unsigned char uuid[16];
 if(!j72_macho_uuid((void*)(i.text-0x800000000ULL+0x400000000ULL),i.text_size,uuid)){fail();return;}
 /* No output is produced during DT traversal or header validation. */
 command_puts("J72_COMPACT_BEGIN");value("MODEL_OK",1);value("SOC",socnum);
 value("PHYS_BASE",b->phys);value("MEM_SIZE",b->size);value("ENTRY_PHYS",(u64)gEntryPoint);
 value("ALLOCATOR_TOP",gTopOfKernelData);value("BOOT_COMMAND_LINE_LENGTH",arglen);
 value("PROPERTIES",i.properties);value("MAPS",i.maps);value("METADATA",i.metadata);
 value("RESERVED_SLOTS",i.reserved);value("EMPTY_SLOTS",i.empty);
 value("TRUSTCACHE_PHYS",i.tc);value("TRUSTCACHE_SIZE",i.tc_size);
 value("KERNEL_HEADER_PHYS",i.text);value("KERNEL_TEXT_SIZE",i.text_size);
 char row[48]="KERNEL_UUID ";unsigned at=12;
 for(unsigned n=0;n<16;n++){row[at++]="0123456789abcdef"[uuid[n]>>4];row[at++]="0123456789abcdef"[uuid[n]&15];}row[at]=0;command_puts(row);
 command_puts("J72_COMPACT_END");
}
void module_entry(void){command_register("j72rescuecompact","compact read-only J72 XNU inventory",probe);}
char *module_name="j72_recovery_compact";
struct pongo_exports {const char*name;void*value;};
struct pongo_exports exported_symbols[]={{0,0}};
