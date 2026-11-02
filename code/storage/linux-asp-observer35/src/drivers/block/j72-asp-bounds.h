/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef J72_ASP_BOUNDS_H
#define J72_ASP_BOUNDS_H
#ifdef __KERNEL__
#include <linux/types.h>
#else
#include <stdint.h>
#include <stdbool.h>
typedef uint64_t u64;
typedef uint32_t u32;
#endif
#define J72_ASP_PAGE 4096u
#define J72_ASP_SGL_MAX 4068u
static inline bool j72_asp_request_valid(u64 capacity, u64 sector512, u32 bytes)
{
 u64 lba=sector512>>3, blocks=bytes>>12;
 return capacity && capacity<=0x100000000ULL && !(sector512&7) && bytes &&
        !(bytes&4095) && blocks<=J72_ASP_SGL_MAX && lba<=0xffffffffULL &&
        lba<capacity && blocks<=capacity-lba;
}
static inline bool j72_asp_sg_valid(u64 address,u32 bytes,u32 used,u32 expected)
{
 u64 mask=(1ULL<<40)-1;
 u32 pages=bytes>>12;
 return bytes && !(bytes&4095) && !(address&4095) && address<=mask &&
        (u64)bytes-1<=mask-address && used<=J72_ASP_SGL_MAX &&
        pages<=J72_ASP_SGL_MAX-used && used<=expected && pages<=expected-used;
}
#endif
