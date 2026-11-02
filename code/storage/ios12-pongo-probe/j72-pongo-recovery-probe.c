/* SPDX-License-Identifier: MIT
 * Read-only J72 Pongo observer. No boot, patch, MMIO or storage operations.
 * ABI declarations follow pinned Pongo 2.6.3; no Apple SDK headers needed.
 */
typedef unsigned long size_t;
typedef unsigned long long u64;
typedef unsigned u32;
typedef struct {u32 properties,children;char data[];} dt_node;
struct boot_args12 {unsigned short revision,version;u32 pad0;u64 virt,phys,size,top;
 u64 video[6];u32 machine,pad1;u64 dtptr;u32 dtlen;char args[256];u32 pad2;u64 flags,actual;};
_Static_assert(__builtin_offsetof(struct boot_args12,dtptr)==96,"Pongo boot-args ABI");
_Static_assert(__builtin_offsetof(struct boot_args12,args)==108,"Pongo iOS12 command-line ABI");
extern struct boot_args12 *gBootArgs;
extern dt_node *gDeviceTree;
extern void *gEntryPoint;
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
static void value(const char*key,u64 v){char row[96];unsigned n=0;while(*key&&n<70)row[n++]=*key++;row[n++]=' ';for(unsigned i=0;i<16;i++)row[n++]="0123456789abcdef"[(v>>(60-i*4))&15];row[n++]='\n';row[n]=0;command_puts(row);}
static void fail(const char*reason){command_puts("J72_PROBE_REFUSED ");command_puts(reason);command_puts("\n");}
static u64 maps,reserved;
static int maprow(void*a,dt_node*node,int depth,const char*key,void*val,size_t len){
 (void)a;(void)node;(void)depth;
 if(++maps>128)return -1;
 if(eq(key,"name"))return 0;
 if(len!=16){fail("memory-map-property-size");return -1;}
 if(prefix(key,"MemoryMapReserved-"))reserved++;
 char line[40];unsigned n=0;line[n++]='M';line[n++]='A';line[n++]='P';line[n++]=' ';
 while(key[n-4]&&n<35){unsigned c=(unsigned char)key[n-4];if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='-'))return -1;line[n++]=(char)c;}
 line[n]=0;value(line,j72_u64(val));value("MAP_SIZE",j72_u64((unsigned char*)val+8));return 0;
}
static void probe(const char*command,char*args){
 (void)command;while(*args==' ')args++;if(*args){fail("arguments");return;}
 if(socnum!=0x8960||!gBootArgs||!gDeviceTree){fail("platform");return;}
 struct boot_args12*b=gBootArgs;
 if(b->phys<0x800000000ULL||b->size>0x40000000ULL||b->size<0x10000000ULL||b->dtlen<64||b->dtlen>0x100000||b->dtptr<b->virt||b->dtptr-b->virt>~0ULL-b->phys){fail("boot-args-range");return;}
 u64 dtphys=b->dtptr-b->virt+b->phys;
 if(!j72_span(b->phys,b->size,dtphys,b->dtlen)||(u64)gDeviceTree!=dtphys-0x800000000ULL+0x400000000ULL){fail("devicetree-view");return;}
 if(dt_check(gDeviceTree,b->dtlen,0)){fail("devicetree-format");return;}
 size_t len=0;const char*model=dt_prop(gDeviceTree,"model",&len);
 if(!model||len!=8||!eq(model,"iPad4,2")){fail("model");return;}
 u64 entry=(u64)gEntryPoint;
 if(!j72_span(b->phys,b->size,entry,4)){fail("entry-range");return;}
 command_puts("J72_PONGO_PROBE_BEGIN\n");value("MODEL_OK",1);value("SOC",socnum);
 value("BOOT_REVISION",b->revision);value("BOOT_VERSION",b->version);value("PHYS_BASE",b->phys);value("MEM_SIZE",b->size);value("TOP_KERNEL_DATA",b->top);value("ENTRY_PHYS",entry);
 dt_node*map=dt_find(gDeviceTree,"/chosen/memory-map");if(!map){fail("memory-map-missing");return;}
 maps=reserved=0;if(dt_parse(map,-1,0,0,0,maprow,0)){fail("memory-map-parse");return;}
 value("RESERVED_SLOTS",reserved);
 u64 page=entry&~0xfffULL,found=0;unsigned char uuid[16]={0};
 for(unsigned i=0;i<2048;i++){
  if(!j72_span(b->phys,b->size,page,32))break;
  const unsigned char*ptr=(void*)(page-0x800000000ULL+0x400000000ULL);
  if(j72_macho_uuid(ptr,b->size-(page-b->phys),uuid)){found=page;break;}
  if(page<b->phys+4096)break;page-=4096;
 }
 if(!found){fail("bounded-kernel-header-search");return;}
 value("KERNEL_HEADER_PHYS",found);char row[48]="KERNEL_UUID ";unsigned at=12;
 for(unsigned i=0;i<16;i++){row[at++]="0123456789abcdef"[uuid[i]>>4];row[at++]="0123456789abcdef"[uuid[i]&15];}row[at++]='\n';row[at]=0;command_puts(row);
 command_puts("J72_PONGO_PROBE_END\n");
}
void module_entry(void){command_register("j72rescueprobe","read-only J72 XNU/RAM handoff inventory",probe);}
char *module_name="j72_recovery_probe";
struct pongo_exports {const char*name;void*value;};
struct pongo_exports exported_symbols[]={{0,0}};
