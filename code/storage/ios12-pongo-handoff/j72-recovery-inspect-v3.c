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
#include "j72-recovery-guard.h"
#include "j72-recovery-mount-guard.h"
static void jsonstr(const char*s){printf("\"");for(;*s;s++){unsigned char c=(unsigned char)*s;if(c=='"'||c=='\\')printf("\\%c",c);else if(c<32||c>126)printf("\\u%04x",c);else printf("%c",c);}printf("\"");}
static u32 le32(const unsigned char*p){return (u32)p[0]|(u32)p[1]<<8|(u32)p[2]<<16|(u32)p[3]<<24;}
static u64 le64(const unsigned char*p){return le32(p)|(u64)le32(p+4)<<32;}
static int geometry(int fd,u32*block,u64*count){return ioctl(fd,0x40046418UL,block)||ioctl(fd,0x40086419UL,count);}
static int readblock(int fd,u64 lba,unsigned char*b){return lseek(fd,(long long)(lba*4096ULL),0)!=(long long)(lba*4096ULL)||read(fd,b,4096)!=4096;}
static void hex(const unsigned char*b,size_t n){const char*h="0123456789abcdef";for(size_t i=0;i<n;i++)printf("%c%c",h[b[i]>>4],h[b[i]&15]);}
int main(int argc,char**argv){
 (void)argc;(void)argv;
 char model[32]={0},version[32]={0},args[2048]={0};size_t n=sizeof(model),v=sizeof(version),a=sizeof(args);
 if(getuid()!=0||sysctlbyname("hw.machine",model,&n,0,0)||!n||n>=sizeof(model)||model[n-1]||!same(model,"iPad4,2"))return 2;
 if(sysctlbyname("kern.osrelease",version,&v,0,0)||v<3||v>sizeof(version)||version[0]!='1'||version[1]!='8'||version[2]!='.')return 3;
 const char*command=getenv("SSH_ORIGINAL_COMMAND");
 if(!command||(!same(command,"inspect")&&!same(command,"diagnose")&&!same(command,"reboot"))){printf("J72 inspect refused: command is not inspect, diagnose or reboot\n");return 7;}
 alarm(20);
 struct mountguard mg={0};int rootram=mountguard_read(&mg);
 int argstatus=sysctlbyname("kern.bootargs",args,&a,0,0);
 int argsok=argstatus==0&&a>0&&a<sizeof(args)&&args[a-1]==0&&safe_args(args);
 printf("J72_GUARD_JSON {\"profile\":\"j72-ram-mount-guard-v3\",\"bootargs_status\":%d,\"bootargs_length\":%lu,\"bootargs_approved\":%s,\"mount_count\":%d,\"apfs_mounts\":%d,\"root_count\":%d,\"root_is_hfs\":%d,\"root_flag\":%d,\"known_root_label\":%d,\"root_stat_status\":%d,\"md_stat_status\":%d,\"device_numbers_match\":%d,\"mount_strings_valid\":%d,\"root_type\":",argstatus,(unsigned long)a,argsok?"true":"false",mg.count,mg.apfs,mg.roots,mg.hfs,mg.rootflag,mg.known_label,mg.root_stat_status,mg.md_stat_status,mg.device_match,mg.valid_strings);
 jsonstr(mg.type);printf(",\"root_from\":");jsonstr(mg.from);printf(",\"root_is_hfs_md0\":%s,\"raw_disk_opened\":false}\n",rootram?"true":"false");fflush(0);
 if(same(command,"diagnose"))return 0;
 if(!argsok||!rootram){printf("J72 inspect refused: requires approved RAM root with no APFS mounts\n");return 5;}
 if(same(command,"reboot")){printf("J72 recovery reboot requested\n");fflush(0);return reboot(0)==0?0:6;}
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
