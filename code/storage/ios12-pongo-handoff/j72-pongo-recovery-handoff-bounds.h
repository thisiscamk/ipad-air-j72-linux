/* SPDX-License-Identifier: MIT */
#include "j72-pongo-recovery-bounds.h"
#include "j72_sha256.h"
static int j72_bytes_equal(const unsigned char*a,const unsigned char*b,unsigned n){unsigned v=0;for(unsigned i=0;i<n;i++)v|=a[i]^b[i];return !v;}
static int j72_tc(const unsigned char*b,u64 size,unsigned*entries){
 if(size<32||j72_u32(b)!=1||j72_u32(b+4)!=8||j72_u32(b+8)!=1)return 0;
 unsigned n=j72_u32(b+28);if(!n||n>10000||32ULL+22ULL*n!=size)return 0;
 for(unsigned i=0;i<n;i++){
  const unsigned char*e=b+32+22*i;if(e[20]<1||e[20]>4)return 0;
  if(i){const unsigned char*prev=e-22;unsigned j=0;while(j<20&&prev[j]==e[j])j++;if(j==20){if(prev[20]!=e[20]||prev[21]!=e[21])return 0;}else if(prev[j]>e[j])return 0;}
 }
 *entries=n;return 1;
}
static int j72_bundle(const unsigned char*b,u64 n,u64 expected_size,u64 tc_off,u64 tc_size,u64 hfs_off,u64 hfs_size,const unsigned char sha[32],void(*yield_fn)(void)){
 const unsigned char magic[8]={'J','7','2','R','A','M','0','1'};
 if(n!=expected_size||n<512||n>0x8000000||!j72_bytes_equal(b,magic,8)||j72_u32(b+8)!=1||j72_u32(b+12)!=512)return 0;
 if(j72_u64(b+16)!=tc_off||j72_u64(b+24)!=tc_size||j72_u64(b+32)!=hfs_off||j72_u64(b+40)!=hfs_size)return 0;
 if(tc_off<512||tc_off>=n||hfs_off>=n||(tc_off&15)||tc_size>n-tc_off||hfs_off<tc_off+tc_size||(hfs_off&0x3fff)||hfs_size>n-hfs_off||hfs_size<2048)return 0;
 for(unsigned i=48;i<512;i++)if(b[i])return 0;
 unsigned entries=0;if(!j72_tc(b+tc_off,tc_size,&entries))return 0;
 if(b[hfs_off+1024]!='H'||(b[hfs_off+1025]!='+'&&b[hfs_off+1025]!='X'))return 0;
 unsigned char digest[32];j72_sha256(b,n,digest,yield_fn);return j72_bytes_equal(digest,sha,32);
}
