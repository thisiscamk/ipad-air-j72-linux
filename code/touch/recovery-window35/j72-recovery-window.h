/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef J72_RECOVERY_WINDOW_H
#define J72_RECOVERY_WINDOW_H
/* Monotonic milliseconds. At most six admitted recoveries in (now-60s, now].
 * This is a burst bound, not a lifetime budget. No allocation or device I/O. */
#define J72_RECOVERY_CAPACITY 6U
#define J72_RECOVERY_WINDOW_MS 60000ULL
struct j72_recovery_window {
 unsigned long long times[J72_RECOVERY_CAPACITY];
 unsigned int count, next;
};
static inline int j72_recovery_admit(struct j72_recovery_window *w,
                                   unsigned long long now)
{
 if(w->count>J72_RECOVERY_CAPACITY || w->next>=J72_RECOVERY_CAPACITY)return 0;
 if(w->count) {
  unsigned int last=(w->next+J72_RECOVERY_CAPACITY-1)%J72_RECOVERY_CAPACITY;
  if(now<w->times[last])return 0;
 }
 if(w->count==J72_RECOVERY_CAPACITY &&
    now-w->times[w->next]<J72_RECOVERY_WINDOW_MS)return 0;
 w->times[w->next]=now;
 w->next=(w->next+1)%J72_RECOVERY_CAPACITY;
 if(w->count<J72_RECOVERY_CAPACITY)w->count++;
 return 1;
}
#endif
