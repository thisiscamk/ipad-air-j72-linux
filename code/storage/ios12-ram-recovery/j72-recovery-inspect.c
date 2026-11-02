/* SPDX-License-Identifier: GPL-2.0-or-later
 * J72 RAM recovery inspection. Forced SSH command: inspect or reboot only.
 * Raw storage is opened O_RDONLY and only the already measured GPT locations
 * are read. No resize, mount, snapshot mutation or raw disk write interface.
 */
typedef unsigned long size_t;
typedef unsigned int u32;
typedef unsigned long long u64;
extern int printf(const char*,...);
extern int fflush(void*);
extern int sysctlbyname(const char*,void*,size_t*,void*,size_t);
extern unsigned getuid(void);
extern char *getenv(const char*);
extern int getfsstat(void*,int,int);
extern int open(const char*,int,...);
extern int close(int);
extern int ioctl(int,unsigned long,...);
extern long long lseek(int,long long,int);
extern long read(int,void*,size_t);
extern int posix_memalign(void**,size_t,size_t);
extern void free(void*);
extern unsigned alarm(unsigned);
extern int reboot(int);
extern void *dlopen(const char*,int);
extern void *dlsym(void*,const char*);
extern int dlclose(void*);
/* Functional iOS12 statfs64 ABI from XNU4903 mount.h; no SDK headers. */
struct fsrow {u32 bsize;int iosize;u64 blocks,bfree,bavail,files,ffree;
 int fsid[2];u32 owner,type,flags,subtype;char fstype[16],on[1024],from[1024];u32 reserved[8];};
_Static_assert(sizeof(struct fsrow)==2168,"iOS12 statfs64 ABI");
_Static_assert(__builtin_offsetof(struct fsrow,fstype)==72,"statfs type offset");
_Static_assert(__builtin_offsetof(struct fsrow,on)==88,"statfs mountpoint offset");
#include "j72-recovery-guard.h"
static int bounded(const char*s,size_t n){for(size_t i=0;i<n;i++)if(!s[i])return 1;return 0;}
static u32 le32(const unsigned char*p){return (u32)p[0]|(u32)p[1]<<8|(u32)p[2]<<16|(u32)p[3]<<24;}
static u64 le64(const unsigned char*p){return le32(p)|(u64)le32(p+4)<<32;}
static int geometry(int fd,u32*block,u64*count){return ioctl(fd,0x40046418UL,block)||ioctl(fd,0x40086419UL,count);}
static int readblock(int fd,u64 lba,unsigned char*b){return lseek(fd,(long long)(lba*4096ULL),0)!=(long long)(lba*4096ULL)||read(fd,b,4096)!=4096;}
static void hex(const unsigned char*b,size_t n){const char*h="0123456789abcdef";for(size_t i=0;i<n;i++)printf("%c%c",h[b[i]>>4],h[b[i]&15]);}
static int mounts(int*rootram,int*apfs){struct fsrow rows[16];int total=getfsstat(0,0,2);if(total<=0||total>16)return -1;int n=getfsstat(rows,sizeof(rows),2);if(n<=0||n>16||n!=total)return -1;int root=0;*rootram=0;*apfs=0;
 for(int i=0;i<n;i++){if(!bounded(rows[i].fstype,16)||!bounded(rows[i].on,1024)||!bounded(rows[i].from,1024))return -1;if(same(rows[i].fstype,"apfs"))(*apfs)++;if(same(rows[i].on,"/")){root++;*rootram=same(rows[i].fstype,"hfs")&&same(rows[i].from,"/dev/md0");}}
 return root==1?n:-1;}
int main(int argc,char**argv){
 char model[32]={0},version[32]={0},args[2048]={0};size_t n=sizeof(model),v=sizeof(version),a=sizeof(args);
 if(getuid()!=0||sysctlbyname("hw.machine",model,&n,0,0)||!n||n>=sizeof(model)||model[n-1]||!same(model,"iPad4,2"))return 2;
 if(sysctlbyname("kern.osrelease",version,&v,0,0)||v<3||v>sizeof(version)||version[0]!='1'||version[1]!='8'||version[2]!='.')return 3;
 int rootram=0,apfs=0;int mountcount=mounts(&rootram,&apfs);
 if(argc==2&&same(argv[1],"--mount-abi-probe")){printf("{\"profile\":\"j72-mount-abi-probe\",\"mount_count\":%d,\"root_is_hfs_md0\":%s,\"apfs_mounts\":%d,\"raw_disk_opened\":false}\n",mountcount,rootram?"true":"false",apfs);return mountcount>0?0:4;}
 if(sysctlbyname("kern.bootargs",args,&a,0,0)||!a||a>=sizeof(args)||args[a-1]||!safe_args(args)||mountcount<1||!rootram||apfs){printf("J72 inspect refused: requires approved RAM root with no APFS mounts\n");return 5;}
 const char*command=getenv("SSH_ORIGINAL_COMMAND");if(!command||!same(command,"inspect")){if(command&&same(command,"reboot")){printf("J72 recovery reboot requested\n");fflush(0);return reboot(0)==0?0:6;}printf("J72 inspect refused: command is not inspect or reboot\n");return 7;}
 alarm(20);int fd=open("/dev/rdisk0",0x100);if(fd<0)return 8;u32 block=0;u64 count=0;
 if(geometry(fd,&block,&count)||block!=4096||count!=31250000ULL){close(fd);return 9;}
 void*mem=0;if(posix_memalign(&mem,4096,4096)){close(fd);return 10;}unsigned char*b=mem;
 /* Validate both headers against this board's fresh 128GB/4KiB GPT before following arrays. */
 for(unsigned i=0;i<2;i++){u64 lba=i?count-1:1;if(readblock(fd,lba,b)||!token((char*)b,8,"EFI PART")||le64(b+24)!=lba||le64(b+32)!=(i?1:count-1)||le64(b+72)!=(i?count-5:2)||le32(b+80)!=128||le32(b+84)!=128){free(mem);close(fd);return 11;}}
 printf("J72_INSPECT_JSON {\"profile\":\"j72-ram-recovery-inspect-v1\",\"read_only\":true,\"root_is_hfs_md0\":true,\"apfs_mounts\":0,\"logical_block_bytes\":4096,\"total_blocks\":31250000,\"files\":{");
 const char*names[]={"mbr.bin","primary-header.bin","primary-entries.bin","backup-header.bin","backup-entries.bin"};
 const u64 lbas[]={0,1,2,31249999,31249995};const unsigned blocks[]={1,1,4,1,4};
 for(unsigned k=0;k<5;k++){printf("%s\"%s\":\"",k?",":"",names[k]);for(unsigned j=0;j<blocks[k];j++){if(readblock(fd,lbas[k]+j,b)){free(mem);close(fd);return 12;}hex(b,4096);}printf("\"");}free(mem);close(fd);
 printf("},\"minimal_size_query\":{");void*h=dlopen("/System/Library/PrivateFrameworks/APFS.framework/APFS",1);typedef int(*fn_t)(const char*,long*);fn_t fn=h?(fn_t)dlsym(h,"APFSContainerGetMinimalSize"):0;
 if(fn){struct{u64 pre;long bytes;u64 post;}out={0x123456789abcdef0ULL,0,0xfedcba9876543210ULL};int status=fn("disk0s1",&out.bytes);printf("\"available\":true,\"status\":%d,\"bytes\":%ld,\"canaries_intact\":%s",status,out.bytes,(out.pre==0x123456789abcdef0ULL&&out.post==0xfedcba9876543210ULL)?"true":"false");}else printf("\"available\":false");if(h)dlclose(h);
 printf("},\"resize_called\":false,\"snapshot_mutations\":false}\n");fflush(0);return 0;
}
