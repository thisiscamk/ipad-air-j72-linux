/* SPDX-License-Identifier: MIT */
static unsigned j72_u32(const unsigned char*p){return (unsigned)p[0]|(unsigned)p[1]<<8|(unsigned)p[2]<<16|(unsigned)p[3]<<24;}
static unsigned long long j72_u64(const unsigned char*p){return j72_u32(p)|(unsigned long long)j72_u32(p+4)<<32;}
static int j72_span(unsigned long long base,unsigned long long size,unsigned long long addr,unsigned long long n){
 return size&&n&&base<=~0ULL-size&&addr>=base&&addr-base<size&&n<=size-(addr-base);
}
/* Only identify an ARM64 executable header; never follow Mach-O pointers. */
static int j72_macho_uuid(const unsigned char*b,unsigned long long available,unsigned char uuid[16]){
 if(available<32||j72_u32(b)!=0xfeedfacf||j72_u32(b+4)!=0x100000c||j72_u32(b+12)!=2)return 0;
 unsigned n=j72_u32(b+16),bytes=j72_u32(b+20),at=32,uuids=0,text=0;
 if(n<2||n>128||bytes<n*8||bytes>65536||32ULL+bytes>available)return 0;
 for(unsigned i=0;i<n;i++){
  if(at>32+bytes-8)return 0;
  unsigned cmd=j72_u32(b+at),len=j72_u32(b+at+4);
  if(len<8||len>32+bytes-at||(len&7))return 0;
  if(cmd==0x1b){if(len!=24||++uuids!=1)return 0;for(unsigned j=0;j<16;j++)uuid[j]=b[at+8+j];}
  if(cmd==0x19){
   if(len<72)return 0;
   unsigned sections=j72_u32(b+at+64);if(sections>64||len!=72+80*sections)return 0;
   if(b[at+8]=='_'&&b[at+9]=='_'&&b[at+10]=='T'&&b[at+11]=='E'&&b[at+12]=='X'&&b[at+13]=='T'&&b[at+14]==0){
    if(++text!=1||j72_u64(b+at+40)!=0||j72_u64(b+at+48)<32ULL+bytes||j72_u64(b+at+32)<j72_u64(b+at+48))return 0;
   }
  }
  at+=len;
 }
 unsigned any=0;for(unsigned j=0;j<16;j++)any|=uuid[j];
 return at==32+bytes&&uuids==1&&text==1&&any;
}
