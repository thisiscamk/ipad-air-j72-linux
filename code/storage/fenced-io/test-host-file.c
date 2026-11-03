/* SPDX-License-Identifier: MIT */
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include "j72-fenced-io.h"
struct host_file {int fd; dev_t dev; ino_t ino;};
static int identity(void *ctx) {
 struct host_file *f = ctx;struct stat st;
 return fstat(f->fd,&st) || !S_ISREG(st.st_mode) || st.st_dev!=f->dev ||
        st.st_ino!=f->ino || st.st_size!=8*J72_IO_BLOCK || st.st_nlink!=0;
}
static int64_t rd(void *ctx,void *buf,size_t n,uint64_t off) {
 struct host_file *f=ctx;ssize_t count=pread(f->fd,buf,n,(off_t)off);
 return count<0?-errno:count;
}
static int64_t wr(void *ctx,const void *buf,size_t n,uint64_t off) {
 struct host_file *f=ctx;ssize_t count=pwrite(f->fd,buf,n,(off_t)off);
 return count<0?-errno:count;
}
static int flush(void *ctx) {
 struct host_file *f=ctx;return fsync(f->fd);
}
static _Alignas(J72_IO_BLOCK) unsigned char data[4*J72_IO_BLOCK];
static _Alignas(J72_IO_BLOCK) unsigned char scratch[J72_IO_BLOCK];
int main(void) {
 /* NEW fixed-template host regular file, immediately unlinked. Never accepts
  * a path/descriptor from a caller and never opens a disk or existing file. */
 char path[]="/tmp/j72-fenced-io-XXXXXX";
 struct host_file f={.fd=mkstemp(path)};assert(f.fd>=0);
 assert(!unlink(path));assert(!fcntl(f.fd,F_SETFD,FD_CLOEXEC));
 assert(!ftruncate(f.fd,8*J72_IO_BLOCK));
 struct stat st;assert(!fstat(f.fd,&st));f.dev=st.st_dev;f.ino=st.st_ino;
 memset(scratch,0x55,sizeof(scratch));
 for(size_t off=0;off<8*J72_IO_BLOCK;off+=J72_IO_BLOCK)
  assert(pwrite(f.fd,scratch,sizeof(scratch),(off_t)off)==sizeof(scratch));
 assert(!fsync(f.fd));
 for(size_t i=0;i<sizeof(data);i++)data[i]=(unsigned char)(i%251);
 const struct j72_io_ops ops={&f,identity,rd,wr,flush};struct j72_fenced_io s;
 assert(!j72_io_init(&s,&ops,2*J72_IO_BLOCK,6*J72_IO_BLOCK,2*J72_IO_BLOCK));
 assert(!j72_io_write_verified(&s,2*J72_IO_BLOCK,data,sizeof(data),scratch,sizeof(scratch)));
 assert(s.bytes_written==sizeof(data)&&s.bytes_verified==sizeof(data)&&s.successful_flushes==1);
 for(size_t off=0;off<8*J72_IO_BLOCK;off+=J72_IO_BLOCK) {
  if(off>=2*J72_IO_BLOCK&&off<6*J72_IO_BLOCK)continue;
  assert(pread(f.fd,scratch,sizeof(scratch),(off_t)off)==sizeof(scratch));
  for(size_t i=0;i<sizeof(scratch);i++)assert(scratch[i]==0x55);
 }
 /* Actual identity mutation must stop later I/O on this same descriptor. */
 assert(!ftruncate(f.fd,9*J72_IO_BLOCK));
 assert(j72_io_write_verified(&s,2*J72_IO_BLOCK,data,sizeof(data),scratch,sizeof(scratch))==J72_IO_IDENTITY);
 assert(s.bytes_written==sizeof(data));assert(!close(f.fd));
 puts("PASS: actual C write/fsync/readback/fences on a new unlinked host regular file; native iOS backend unqualified");
 return 0;
}
