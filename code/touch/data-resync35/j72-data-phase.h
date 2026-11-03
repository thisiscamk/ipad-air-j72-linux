/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef J72_DATA_PHASE_H
#define J72_DATA_PHASE_H
/* Bounded acquisition only. The caller must still verify the COMPLETE wire
 * frame and native contact layout before emitting any input event.
 * Reference: Orchard ec1a4e1ad1d76ff60f3576df9573ec6ec7f30566, J71b.
 * J72 checksum/length/tag/buffer rules remain those of its measured worker.
 */
#define J72_DATA_CAPACITY 2464u
#define J72_DATA_MAX_PAYLOAD 2454u
struct j72_data_io {
 void *ctx;
 int (*xfer)(void *, unsigned char *, unsigned char *, unsigned int);
 void (*header_seen)(void *, const unsigned char *, const unsigned char *, unsigned int);
};
struct j72_data_result {unsigned int wire, resynced; int error;};

static unsigned int j72_data_header_length(const unsigned char *p, unsigned int wire)
{
 unsigned int sum=0, length, i;
 if (wire<16 || wire>J72_DATA_MAX_PAYLOAD+5 || p[0]!=0xe1) return 0;
 for (i=0;i<14;i++)sum+=p[i];
 if (sum!=((unsigned int)p[14]|((unsigned int)p[15]<<8)))return 0;
 length=p[1]|((unsigned int)p[2]<<8);
 /* Empty/invalid control replies retain their old rejection path. */
 return length>=2 && length<=J72_DATA_MAX_PAYLOAD ? length : 0;
}

static struct j72_data_result j72_data_phase(const struct j72_data_io *io,
 unsigned char *tx, unsigned char *rx, unsigned int capacity,
 unsigned int payload, unsigned int tag)
{
 struct j72_data_result r={0,0,-1};
 unsigned int next,i,sum;
 unsigned long a=(unsigned long)tx,b=(unsigned long)rx;
 if (!io || !io->xfer || !io->header_seen || !tx || !rx ||
     (a<=b ? b-a<capacity : a-b<capacity) ||
     capacity!=J72_DATA_CAPACITY || payload<2 || payload>J72_DATA_MAX_PAYLOAD ||
     (tag!=1 && tag!=2))return r;
 for (;;) {
  r.wire=payload+5;
  for (i=0;i<capacity;i++){tx[i]=0;rx[i]=0;}
  tx[0]=0xeb;tx[1]=tag;tx[2]=1;
  sum=0;for (i=0;i<14;i++)sum+=tx[i];
  tx[r.wire-2]=sum;tx[r.wire-1]=sum>>8;
  r.error=io->xfer(io->ctx,tx,rx,r.wire);
  if (r.error || r.resynced)return r;
  next=j72_data_header_length(rx,r.wire);
  if (!next)return r;
  /* Keep the first reply in the wire-anomaly ring before the retry overwrites
   * rx. This callback cannot emit input. Same tag; at most ONE extra transfer. */
  io->header_seen(io->ctx,tx,rx,r.wire);
  r.resynced=1;payload=next;
 }
}
#endif
