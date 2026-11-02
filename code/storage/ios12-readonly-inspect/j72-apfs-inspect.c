/* SPDX-License-Identifier: MIT
 * J72 read-only iOS inspection. No resize, snapshot mutation, fsctl or mount.
 * fs_snapshot_list ABI: Apple xnu bsd/sys/snapshot.h; attrlist: sys/attr.h.
 * Minimal ABI declarations avoid importing private SDK files.
 */
typedef unsigned long size_t;
typedef unsigned int u32;
typedef unsigned short u16;
extern int printf(const char *, ...);
extern int sysctlbyname(const char *, void *, size_t *, void *, size_t);
extern void *dlopen(const char *, int);
extern void *dlsym(void *, const char *);
extern int dlclose(void *);
extern int open(const char *, int, ...);
extern int close(int);
extern void *calloc(size_t, size_t);
extern void free(void *);
extern int *__error(void);
struct attrs {u16 bitmapcount, reserved; u32 common, volume, directory, file, fork;};
_Static_assert(sizeof(struct attrs)==24,"attrlist ABI size");
typedef int (*snapshot_list_fn)(int, struct attrs *, void *, size_t, u32);
static int equal(const char *a,const char *b) {while(*a && *a==*b){a++;b++;}return *a==*b;}
static void snapshots(snapshot_list_fn fn,const char *path)
{
 int count=-1,err=0,fd;
 void *buffer;
 if(!fn){printf("{\"available\":false}");return;}
 fd=open(path,0);
 if(fd<0){printf("{\"available\":true,\"open_errno\":%d}",*__error());return;}
 buffer=calloc(1,65536);
 if(!buffer){close(fd);printf("{\"available\":true,\"allocation_failed\":true}");return;}
 /* ATTR_BULK_REQUIRED = ATTR_CMN_NAME | ATTR_CMN_RETURNED_ATTRS. */
 struct attrs a={5,0,0x80000001U,0,0,0,0};
 count=fn(fd,&a,buffer,65536,0);
 if(count<0)err=*__error();
 /* Report only a bounded first batch. No snapshot names or UUIDs leave RAM. */
 printf("{\"available\":true,\"first_batch_entries\":%d,\"errno\":%d,\"buffer_bytes\":65536}",count,err);
 free(buffer);close(fd);
}
int main(void)
{
 char machine[32]={0},release[32]={0};size_t n=sizeof(machine),r=sizeof(release);
 if(sysctlbyname("hw.machine",machine,&n,0,0)||n==0||n>=sizeof(machine)||machine[n-1]!=0||!equal(machine,"iPad4,2"))return 2;
 if(sysctlbyname("kern.osrelease",release,&r,0,0)||r<3||r>sizeof(release)||release[0]!='1'||release[1]!='8'||release[2]!='.')return 3;
 void *lib=dlopen("/usr/lib/libSystem.B.dylib",1);
 if(!lib)return 4;
 snapshot_list_fn list=(snapshot_list_fn)dlsym(lib,"fs_snapshot_list");
 void *apfs=dlopen("/System/Library/PrivateFrameworks/APFS.framework/APFS",1);
 const char *names[]={"APFSContainerResize","APFSContainerGetMinimalSize","APFSContainerGetSpaceInfo","APFSContainerGetMinimumSize","APFSContainerResizeGetMinimumSize","APFSVolumeGetMinimumSize"};
 printf("{\"profile\":\"j72-ios12-readonly-v3\",\"apfs_framework_loaded\":%s,\"symbols\":{",apfs?"true":"false");
 for(unsigned i=0;i<sizeof(names)/sizeof(names[0]);i++)
  printf("%s\"%s\":%s",i?",":"",names[i],apfs&&dlsym(apfs,names[i])?"true":"false");
 printf("},\"root_snapshots\":");snapshots(list,"/");
 printf(",\"data_snapshots\":");snapshots(list,"/private/var");
 printf(",\"resize_called\":false,\"snapshot_mutations\":false,\"mount_called\":false}\n");
 if(apfs)dlclose(apfs);dlclose(lib);return 0;
}
