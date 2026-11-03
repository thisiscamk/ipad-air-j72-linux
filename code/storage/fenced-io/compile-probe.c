/* SPDX-License-Identifier: MIT */
/* Compile-only iOS12 ABI probe. No executable, media adapter or device access. */
#include "j72-fenced-io.h"
int j72_fenced_io_compile_probe(struct j72_fenced_io *state,
 const struct j72_io_ops *ops, const void *data, void *scratch)
{
 int result = j72_io_init(state, ops, 4096, 32768, 4096);
 if (result) return result;
 return j72_io_write_verified(state, 4096, data, 4096, scratch, 4096);
}
