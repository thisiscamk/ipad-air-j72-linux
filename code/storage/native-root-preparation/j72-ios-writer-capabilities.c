/* SPDX-License-Identifier: MIT
 * Exact J72/iOS12.5.7 native storage capability QUERIES ONLY.
 * No write, resize, flush, fsctl, mount, snapshot or repair entry point.
 * Query numbers: Apple XNU4903 bsd/sys/disk.h. APFS minimum ABI was already
 * measured by our read-only normal-iOS and RAM-recovery inspectors.
 */
typedef unsigned long size_t;
typedef unsigned int u32;
typedef unsigned long long u64;
extern int printf(const char *, ...);
extern int sysctlbyname(const char *, void *, size_t *, void *, size_t);
extern unsigned getuid(void);
extern int open(const char *, int, ...);
extern int close(int);
extern int ioctl(int, unsigned long, ...);
extern int *__error(void);
extern unsigned alarm(unsigned);
extern void *dlopen(const char *, int);
extern void *dlsym(void *, const char *);
extern int dlclose(void *);

static int same(const char *a, const char *b)
{while (*a && *a == *b) {a++; b++;} return *a == *b;}

static int value(const char *key, char *out, size_t capacity)
{
 size_t n = capacity;
 return sysctlbyname(key, out, &n, 0, 0) == 0 && n > 0 && n <= capacity && out[n-1] == 0;
}

int main(int argc, char **argv)
{
 (void)argv;
 char model[32]={0}, build[32]={0}, release[32]={0};
 if (argc != 1 || getuid() != 0 ||
     !value("hw.machine", model, sizeof(model)) || !same(model, "iPad4,2") ||
     !value("kern.osversion", build, sizeof(build)) || !same(build, "16H81") ||
     !value("kern.osrelease", release, sizeof(release)) ||
     release[0] != '1' || release[1] != '8' || release[2] != '.') return 2;
 alarm(20);
 /* Darwin O_RDONLY|O_NOFOLLOW; no command-line device or ioctl input. */
 int fd = open("/dev/rdisk0", 0x100);
 if (fd < 0) return 3;
 u32 block=0; u64 blocks=0;
 if (ioctl(fd, 0x40046418UL, &block) || ioctl(fd, 0x40086419UL, &blocks) ||
     block != 4096 || blocks != 31250000ULL) {close(fd); return 4;}
 /* All following requests are _IOR queries. No synchronize/flush request is
  * issued; advertising a capability is not a durability qualification. */
 struct query {const char *name; unsigned long request; int wide;};
 const struct query queries[] = {
  {"media_writable", 0x4004641dUL, 0},
  {"features", 0x4004644cUL, 0},
  {"physical_block_bytes", 0x4004644dUL, 0},
  {"maximum_read_bytes", 0x40086446UL, 1},
  {"maximum_write_bytes", 0x40086447UL, 1},
 };
 printf("{\"profile\":\"j72-ios12-native-writer-queries-v1\",\"read_only\":true,\"logical_block_bytes\":4096,\"total_blocks\":31250000,\"queries\":{");
 for (unsigned i=0; i<sizeof(queries)/sizeof(queries[0]); i++) {
  struct {u64 pre; union {u64 wide; u32 small;} value; u64 post;} out={0x123456789abcdef0ULL,{0},0xfedcba9876543210ULL};
  int status = ioctl(fd, queries[i].request, &out.value);
  int error = status ? *__error() : 0;
  int intact = out.pre==0x123456789abcdef0ULL && out.post==0xfedcba9876543210ULL;
  printf("%s\"%s\":{\"status\":%d,\"errno\":%d,\"value\":%llu,\"canaries_intact\":%s}",
         i?",":"",queries[i].name,status,error,queries[i].wide?out.value.wide:(u64)out.value.small,intact?"true":"false");
  if (!intact) {close(fd); return 5;}
 }
 close(fd);
 void *h = dlopen("/System/Library/PrivateFrameworks/APFS.framework/APFS", 1);
 typedef int (*minimum_fn)(const char *, long *);
 minimum_fn minimum = h ? (minimum_fn)dlsym(h, "APFSContainerGetMinimalSize") : 0;
 printf("},\"minimal_size\":{");
 if (minimum) {
  struct {u64 pre; long bytes; u64 post;} out={0x123456789abcdef0ULL,0,0xfedcba9876543210ULL};
  int status = minimum("disk0s1", &out.bytes);
  int intact = out.pre==0x123456789abcdef0ULL && out.post==0xfedcba9876543210ULL;
  printf("\"available\":true,\"status\":%d,\"bytes\":%ld,\"canaries_intact\":%s",status,out.bytes,intact?"true":"false");
  if (!intact) {if(h)dlclose(h); return 6;}
 } else printf("\"available\":false");
 if (h) dlclose(h);
 printf("},\"resize_called\":false,\"flush_issued\":false,\"storage_writes\":false,\"write_qualification_pass\":false}\n");
 return 0;
}
