/* SPDX-License-Identifier: MIT
 * Authored portable SHA-256, using the SHA-256 constants and operations in
 * FIPS 180-4. No firmware, SDK or external crypto implementation included.
 */
static unsigned j72_rotr(unsigned x,unsigned n){return (x>>n)|(x<<(32-n));}
static void j72_sha256(const unsigned char *data,unsigned long long n,unsigned char out[32],void(*yield_fn)(void)){
 static const unsigned k[64]={
 0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
 0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
 0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
 0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
 0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
 0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
 0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
 0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
 unsigned h[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
 unsigned long long blocks=n/64+1+((n%64)>=56);
 for(unsigned long long b=0;b<blocks;b++){
  unsigned w[64];
  for(unsigned i=0;i<16;i++){
   w[i]=0;
   for(unsigned j=0;j<4;j++){
    unsigned long long at=b*64+i*4+j;unsigned char v=0;
    if(at<n)v=data[at];else if(at==n)v=0x80;
    if(at>=blocks*64-8)v=(unsigned char)((n*8)>>(8*(blocks*64-1-at)));
    w[i]=(w[i]<<8)|v;
   }
  }
  for(unsigned i=16;i<64;i++){
   unsigned a=w[i-15],z=w[i-2];
   w[i]=w[i-16]+(j72_rotr(a,7)^j72_rotr(a,18)^(a>>3))+w[i-7]+(j72_rotr(z,17)^j72_rotr(z,19)^(z>>10));
  }
  unsigned a=h[0],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],z=h[7],bb=h[1];
  for(unsigned i=0;i<64;i++){
   unsigned t=z+(j72_rotr(e,6)^j72_rotr(e,11)^j72_rotr(e,25))+((e&f)^(~e&g))+k[i]+w[i];
   unsigned u=(j72_rotr(a,2)^j72_rotr(a,13)^j72_rotr(a,22))+((a&bb)^(a&c)^(bb&c));
   z=g;g=f;f=e;e=d+t;d=c;c=bb;bb=a;a=t+u;
  }
  h[0]+=a;h[1]+=bb;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=z;
  if(yield_fn&&!(b&0x3fff))yield_fn();
 }
 for(unsigned i=0;i<32;i++)out[i]=(unsigned char)(h[i/4]>>(24-8*(i%4)));
}
