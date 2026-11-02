/* SPDX-License-Identifier: MIT
 * Read-only exact-J72/iOS12 APFS minimal-size query. No resize or raw IO.
 * ABI: OrchardLinux/resize-apfs ac165892 Sources/NativeSystem/NativeSystem.c
 * and palera1n/jbinit df653b8 apple-include-private/APFS/APFS.h (CFIndex*).
 */
typedef unsigned long size_t;
extern int printf(const char *, ...);
extern int sysctlbyname(const char *, void *, size_t *, void *, size_t);
extern void *dlopen(const char *, int);
extern void *dlsym(void *, const char *);
extern int dlclose(void *);
static int equal(const char*a,const char*b){while(*a&&*a==*b){a++;b++;}return *a==*b;}
int main(void){
 char model[32]={0},release[32]={0};size_t n=sizeof(model),r=sizeof(release);
 if(sysctlbyname("hw.machine",model,&n,0,0)||!n||n>=sizeof(model)||model[n-1]||!equal(model,"iPad4,2"))return 2;
 if(sysctlbyname("kern.osrelease",release,&r,0,0)||r<3||r>sizeof(release)||release[0]!='1'||release[1]!='8'||release[2]!='.')return 3;
 void *h=dlopen("/System/Library/PrivateFrameworks/APFS.framework/APFS",1);if(!h)return 4;
 typedef int(*minimum_fn)(const char *,long *);
 minimum_fn query=(minimum_fn)dlsym(h,"APFSContainerGetMinimalSize");
 if(!query){dlclose(h);return 5;}
 struct {unsigned long before;long bytes;unsigned long after;} result={0x123456789abcdef0UL,0,0xfedcba9876543210UL};
 int status=query("disk0s1",&result.bytes);
 int intact=result.before==0x123456789abcdef0UL&&result.after==0xfedcba9876543210UL;
 printf("{\"profile\":\"j72-ios12-minimal-size-v1\",\"bsd_name\":\"disk0s1\",\"api_status\":%d,\"minimum_bytes\":%ld,\"output_canaries_intact\":%s,\"resize_called\":false,\"raw_disk_opened\":false}\n",status,result.bytes,intact?"true":"false");
 dlclose(h);return intact?0:6;
}
