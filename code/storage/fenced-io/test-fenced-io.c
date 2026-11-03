/* SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "j72-fenced-io.h"

/* The only target is this bounded memory fixture. Counters check that a
 * refused/uncertain call cannot reach subsequent I/O or flush operations. */
struct fixture {
 unsigned char media[8 * J72_IO_BLOCK];
 unsigned reads, writes, flushes, identities;
 unsigned fail_identity_at, intr_reads, intr_writes;
 int flush_error;
 int64_t force_count;
 bool force, force_read, corrupt_readback, change_on_flush, short_aligned;
};
static struct fixture f;
static struct j72_fenced_io s;
static _Alignas(J72_IO_BLOCK) unsigned char data[4 * J72_IO_BLOCK];
static _Alignas(J72_IO_BLOCK) unsigned char scratch[2 * J72_IO_BLOCK];
static int identity(void *ctx) {
 struct fixture *x = ctx;
 x->identities++;
 return x->fail_identity_at && x->identities >= x->fail_identity_at;
}
static int64_t rd(void *ctx, void *buf, size_t n, uint64_t off) {
 struct fixture *x = ctx; x->reads++;
 assert(off >= J72_IO_BLOCK && off <= 7*J72_IO_BLOCK && n <= 7*J72_IO_BLOCK-off);
 if (x->intr_reads) {x->intr_reads--; return J72_IO_EINTR;}
 if (x->force || x->force_read) return x->force_count;
 if (x->short_aligned && n > J72_IO_BLOCK) n = J72_IO_BLOCK;
 memcpy(buf, x->media + off, n);
 if (x->corrupt_readback) ((unsigned char *)buf)[0] ^= 1;
 return (int64_t)n;
}
static int64_t wr(void *ctx, const void *buf, size_t n, uint64_t off) {
 struct fixture *x = ctx; x->writes++;
 assert(off >= J72_IO_BLOCK && off <= 7*J72_IO_BLOCK && n <= 7*J72_IO_BLOCK-off);
 if (x->intr_writes) {x->intr_writes--; return J72_IO_EINTR;}
 if (x->force) return x->force_count;
 if (x->short_aligned && n > J72_IO_BLOCK) n = J72_IO_BLOCK;
 memcpy(x->media + off, buf, n);
 return (int64_t)n;
}
static int flush(void *ctx) {
 struct fixture *x = ctx; x->flushes++;
 if (x->change_on_flush) x->fail_identity_at=x->identities+1;
 return x->flush_error;
}
static const struct j72_io_ops ops = {&f, identity, rd, wr, flush};
static void reset(void) {
 memset(&f,0,sizeof(f));memset(f.media,0x55,sizeof(f.media));
 for (size_t i=0;i<sizeof(data);i++) data[i]=(unsigned char)(i%251);
 assert(!j72_io_init(&s,&ops,J72_IO_BLOCK,7*J72_IO_BLOCK,2*J72_IO_BLOCK));
}
static enum j72_io_result run(void) {
 return j72_io_write_verified(&s,2*J72_IO_BLOCK,data,sizeof(data),scratch,sizeof(scratch));
}
static void latched(void) {
 unsigned w=f.writes,r=f.reads,flushes=f.flushes,ids=f.identities;
 assert(run()==J72_IO_LATCHED);
 assert(f.writes==w&&f.reads==r&&f.flushes==flushes&&f.identities==ids);
}
static void fences(void) {
 for(size_t i=0;i<2*J72_IO_BLOCK;i++)assert(f.media[i]==0x55);
 for(size_t i=6*J72_IO_BLOCK;i<sizeof(f.media);i++)assert(f.media[i]==0x55);
}
int main(void) {
 unsigned cases=0;
 reset();assert(!run());assert(f.writes==2&&f.reads==2&&f.flushes==1);
 assert(s.bytes_written==sizeof(data)&&s.bytes_verified==sizeof(data));fences();cases++;
 reset();f.short_aligned=true;assert(!run());assert(f.writes==4&&f.reads==4);fences();cases++;
 reset();f.intr_writes=3;f.intr_reads=3;assert(!run());fences();cases++;
 reset();f.intr_writes=4;assert(run()==J72_IO_INTERRUPTED);assert(!f.flushes&&!f.reads);latched();cases++;
 reset();f.intr_reads=4;assert(run()==J72_IO_INTERRUPTED);assert(f.flushes==1);latched();cases++;
 for(size_t i=0;i<5;i++) {
  int64_t bad[]={0,-5,1,4095,3*J72_IO_BLOCK};
  reset();f.force=true;f.force_count=bad[i];assert(run()==J72_IO_TRANSFER);
  assert(f.writes==1&&!f.reads&&!f.flushes);latched();cases++;
 }
 for(size_t i=0;i<5;i++) {
  int64_t bad[]={0,-5,1,4095,3*J72_IO_BLOCK};
  reset();f.force_read=true;f.force_count=bad[i];assert(run()==J72_IO_TRANSFER);
  assert(f.writes==2&&f.reads==1&&f.flushes==1);latched();cases++;
 }
 reset();f.flush_error=-1;assert(run()==J72_IO_FLUSH);assert(!f.reads&&f.flushes==1);latched();cases++;
 reset();f.flush_error=J72_IO_EINTR;assert(run()==J72_IO_FLUSH);assert(f.flushes==1);latched();cases++;
 reset();f.corrupt_readback=true;assert(run()==J72_IO_READBACK);assert(!s.bytes_verified);latched();cases++;
 reset();f.fail_identity_at=f.identities+1;assert(run()==J72_IO_IDENTITY);assert(!f.writes);latched();cases++;
 reset();f.fail_identity_at=f.identities+4;assert(run()==J72_IO_IDENTITY);
 assert(f.writes==1&&!f.flushes);latched();cases++;
 reset();f.change_on_flush=true;assert(run()==J72_IO_IDENTITY);assert(f.flushes==1&&!f.reads);latched();cases++;
 for(size_t i=0;i<4;i++) {
  uint64_t bad[]={0,6*J72_IO_BLOCK,UINT64_MAX-4095,2*J72_IO_BLOCK+1};
  reset();assert(j72_io_write_verified(&s,bad[i],data,sizeof(data),scratch,sizeof(scratch))==J72_IO_ARGUMENT);
  assert(!f.writes);latched();cases++;
 }
 reset();assert(j72_io_write_verified(&s,2*J72_IO_BLOCK,data,0,scratch,sizeof(scratch))==J72_IO_ARGUMENT);latched();cases++;
 reset();assert(j72_io_write_verified(&s,2*J72_IO_BLOCK,data+1,4096,scratch,sizeof(scratch))==J72_IO_ARGUMENT);latched();cases++;
 reset();assert(j72_io_write_verified(&s,2*J72_IO_BLOCK,data,sizeof(data),data+4096,4096)==J72_IO_ARGUMENT);latched();cases++;
 for(size_t i=0;i<4;i++) {
  size_t bad[]={0,4095,J72_IO_MAX+4096,4097};
  reset();assert(j72_io_init(&s,&ops,4096,7*4096,bad[i])==J72_IO_ARGUMENT);latched();cases++;
 }
 reset();assert(j72_io_init(&s,&ops,4096,UINT64_MAX,4096)==J72_IO_ARGUMENT);latched();cases++;
 reset();struct j72_io_ops missing=ops;missing.identity=0;
 assert(j72_io_init(&s,&missing,4096,7*4096,4096)==J72_IO_ARGUMENT);latched();cases++;
 printf("PASS: %u actual C fenced-I/O scenarios; memory fixture only; no native backend qualified\n",cases);
 return 0;
}
