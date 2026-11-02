/* SPDX-License-Identifier: GPL-2.0-or-later
 * Authored iOS12 ARM64 ABI declarations and read-only root identity check.
 * XNU4903 stat.h/mount.h describe these field sizes, not an SDK dependency.
 */
struct fsrow {u32 bsize;int iosize;u64 blocks,bfree,bavail,files,ffree;
 int fsid[2];u32 owner,type,flags,subtype;char fstype[16],on[1024],from[1024];u32 reserved[8];};
struct statrow {int dev;unsigned short mode,links;u64 ino;u32 uid,gid;int rdev;
 long times[8];long long size,blocks;int blksize;u32 flags,gen;int spare;long long extra[2];};
_Static_assert(sizeof(struct fsrow)==2168,"iOS12 statfs64 ABI");
_Static_assert(__builtin_offsetof(struct fsrow,fstype)==72,"statfs type offset");
_Static_assert(__builtin_offsetof(struct fsrow,on)==88,"statfs mountpoint offset");
_Static_assert(sizeof(struct statrow)==144,"iOS12 ARM64 stat64 ABI");
_Static_assert(__builtin_offsetof(struct statrow,mode)==4,"stat64 mode offset");
_Static_assert(__builtin_offsetof(struct statrow,rdev)==24,"stat64 rdev offset");
_Static_assert(__builtin_offsetof(struct statrow,times)==32,"stat64 times offset");
extern int stat64(const char*,struct statrow*);
struct mountguard {int count,apfs,roots,hfs,rootflag,known_label,device_match;
 int root_stat_status,md_stat_status,valid_strings;char type[16],from[1024];};
static int mg_bounded(const char*s,size_t n){for(size_t i=0;i<n;i++)if(!s[i])return 1;return 0;}
static void mg_copy(char*d,const char*s,size_t n){size_t i=0;for(;i+1<n&&s[i];i++)d[i]=s[i];d[i]=0;}
static int mountguard_read(struct mountguard*g){
 struct fsrow rows[16];g->root_stat_status=g->md_stat_status=-2;
 int total=getfsstat(0,0,2);g->count=total;
 if(total<=0||total>16)return 0;
 int n=getfsstat(rows,sizeof(rows),2);g->count=n;
 if(n!=total||n<=0||n>16)return 0;
 for(int i=0;i<n;i++){
  if(!mg_bounded(rows[i].fstype,16)||!mg_bounded(rows[i].on,1024)||!mg_bounded(rows[i].from,1024))return 0;
  if(same(rows[i].fstype,"apfs"))g->apfs++;
  if(same(rows[i].on,"/")){
   g->roots++;g->hfs=same(rows[i].fstype,"hfs");g->rootflag=(rows[i].flags&0x4000U)!=0;
   g->known_label=same(rows[i].from,"/dev/md0")||same(rows[i].from,"md0")||same(rows[i].from,"root_device");
   mg_copy(g->type,rows[i].fstype,sizeof(g->type));mg_copy(g->from,rows[i].from,sizeof(g->from));
  }
 }
 g->valid_strings=1;
 struct statrow root={0},md={0};
 g->root_stat_status=stat64("/",&root);g->md_stat_status=stat64("/dev/md0",&md);
 g->device_match=g->root_stat_status==0&&g->md_stat_status==0&&
  (root.mode&0170000)==0040000&&(md.mode&0170000)==0060000&&root.dev!=0&&root.dev==md.rdev;
 return g->roots==1&&g->hfs&&g->rootflag&&g->known_label&&g->device_match&&g->apfs==0;
}
