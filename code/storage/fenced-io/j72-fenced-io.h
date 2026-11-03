/* SPDX-License-Identifier: MIT */
#ifndef J72_FENCED_IO_H
#define J72_FENCED_IO_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Portable I/O mechanics only. No device opening, approval, resize or GPT API.
 * A future adapter must bind identity() and I/O to the SAME opened descriptor.
 * identity() must independently reject changed media/geometry/session state.
 * Callbacks return negative errors, with -4 reserved for EINTR; zero or
 * unaligned short progress is uncertain and stops the session permanently.
 */
#define J72_IO_BLOCK 4096u
#define J72_IO_MAX (1024u * 1024u)
#define J72_IO_EINTR (-4)
enum j72_io_result {
 J72_IO_OK, J72_IO_ARGUMENT, J72_IO_IDENTITY, J72_IO_TRANSFER,
 J72_IO_INTERRUPTED, J72_IO_FLUSH, J72_IO_READBACK, J72_IO_LATCHED
};
struct j72_io_ops {
 void *ctx;
 int (*identity)(void *ctx);
 int64_t (*pread)(void *ctx, void *buf, size_t bytes, uint64_t offset);
 int64_t (*pwrite)(void *ctx, const void *buf, size_t bytes, uint64_t offset);
 int (*flush)(void *ctx);
};
struct j72_fenced_io {
 struct j72_io_ops io;
 uint64_t first, end; /* bytes; end exclusive */
 size_t max_io;
 uint64_t bytes_written, bytes_verified, successful_flushes;
 enum j72_io_result failure;
 bool initialized;
};

static inline enum j72_io_result j72_io_fail(struct j72_fenced_io *s,
 enum j72_io_result reason)
{
 if (s->failure == J72_IO_OK) s->failure = reason;
 return reason;
}

/* Fresh context only. The eventual transaction owner must NOT reinitialize a
 * failed session or automatically replay an uncertain write. */
static inline enum j72_io_result j72_io_init(struct j72_fenced_io *s,
 const struct j72_io_ops *io, uint64_t first, uint64_t end, size_t max_io)
{
 if (!s) return J72_IO_ARGUMENT;
 *s = (struct j72_fenced_io){0};
 if (!io || !io->identity || !io->pread || !io->pwrite || !io->flush ||
     first >= end || end > INT64_MAX || first % J72_IO_BLOCK ||
     end % J72_IO_BLOCK || max_io < J72_IO_BLOCK || max_io > J72_IO_MAX ||
     max_io % J72_IO_BLOCK)
  return j72_io_fail(s, J72_IO_ARGUMENT);
 s->io = *io; s->first = first; s->end = end; s->max_io = max_io;
 if (io->identity(io->ctx)) return j72_io_fail(s, J72_IO_IDENTITY);
 s->initialized = true;
 return J72_IO_OK;
}

static inline enum j72_io_result j72_io_check(struct j72_fenced_io *s)
{
 if (!s) return J72_IO_ARGUMENT;
 if (s->failure != J72_IO_OK) return J72_IO_LATCHED;
 if (!s->initialized) return j72_io_fail(s, J72_IO_ARGUMENT);
 if (s->io.identity(s->io.ctx)) return j72_io_fail(s, J72_IO_IDENTITY);
 return J72_IO_OK;
}

static inline bool j72_io_range(const struct j72_fenced_io *s, uint64_t off,
 size_t n, const void *buf)
{
 return buf && !((uintptr_t)buf % J72_IO_BLOCK) && n &&
        !(n % J72_IO_BLOCK) && !(off % J72_IO_BLOCK) &&
        off >= s->first && off < s->end && (uint64_t)n <= s->end - off;
}

static inline enum j72_io_result j72_io_transfer(struct j72_fenced_io *s,
 uint64_t off, void *buf, size_t n, bool write)
{
 enum j72_io_result result = j72_io_check(s);
 size_t done = 0;
 unsigned interruptions = 0;
 if (result) return result;
 if (!j72_io_range(s, off, n, buf)) return j72_io_fail(s, J72_IO_ARGUMENT);
 while (done < n) {
  result = j72_io_check(s);
  if (result) return result;
  size_t amount = n - done;
  if (amount > s->max_io) amount = s->max_io;
  unsigned char *cursor = (unsigned char *)buf + done;
  int64_t count = write ? s->io.pwrite(s->io.ctx, cursor, amount, off + done)
                        : s->io.pread(s->io.ctx, cursor, amount, off + done);
  if (count == J72_IO_EINTR) {
   if (++interruptions > 3) return j72_io_fail(s, J72_IO_INTERRUPTED);
   continue;
  }
  if (count <= 0 || (uint64_t)count > amount || count % J72_IO_BLOCK)
   return j72_io_fail(s, J72_IO_TRANSFER);
  if (write) s->bytes_written += (uint64_t)count;
  done += (size_t)count;
 }
 return j72_io_check(s);
}

static inline enum j72_io_result j72_io_flush(struct j72_fenced_io *s)
{
 enum j72_io_result result = j72_io_check(s);
 if (result) return result;
 /* A failed flush, including EINTR, has uncertain durability. Never retry it
  * automatically, report success or proceed to a later transaction step. */
 if (s->io.flush(s->io.ctx)) return j72_io_fail(s, J72_IO_FLUSH);
 s->successful_flushes++;
 return j72_io_check(s);
}

static inline enum j72_io_result j72_io_write_verified(struct j72_fenced_io *s,
 uint64_t off, const void *data, size_t n, void *scratch, size_t scratch_bytes)
{
 enum j72_io_result result = j72_io_check(s);
 if (result) return result;
 if (!j72_io_range(s, off, n, data) || !scratch ||
     (uintptr_t)scratch % J72_IO_BLOCK || scratch_bytes < J72_IO_BLOCK ||
     scratch_bytes > J72_IO_MAX || scratch_bytes % J72_IO_BLOCK)
  return j72_io_fail(s, J72_IO_ARGUMENT);
 /* Overlapping readback storage would erase or alter expected source bytes.
  * Subtraction avoids address-addition wrap at either end of the intervals. */
 uintptr_t a = (uintptr_t)data, b = (uintptr_t)scratch;
 if ((a <= b && b - a < n) || (b < a && a - b < scratch_bytes))
  return j72_io_fail(s, J72_IO_ARGUMENT);
 result = j72_io_transfer(s, off, (void *)data, n, true);
 if (result) return result;
 result = j72_io_flush(s);
 if (result) return result;
 for (size_t done = 0; done < n;) {
  size_t amount = n - done;
  if (amount > scratch_bytes) amount = scratch_bytes;
  result = j72_io_transfer(s, off + done, scratch, amount, false);
  if (result) return result;
  const unsigned char *want = (const unsigned char *)data + done;
  const unsigned char *actual = scratch;
  for (size_t i = 0; i < amount; i++)
   if (want[i] != actual[i]) return j72_io_fail(s, J72_IO_READBACK);
  s->bytes_verified += amount;
  done += amount;
 }
 return j72_io_check(s);
}
#endif
