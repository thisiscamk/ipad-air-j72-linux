/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef J72_MAINTAIN_CORE_H
#define J72_MAINTAIN_CORE_H
#include "j72-limit-core.h"

/* Existing on-current and battery cutoffs remain unchanged. The controller
 * can wait without a current override, then start a new bounded window only
 * after verified restoration, a fresh gauge vector and source qualification.
 */
#define J72_GAUGE_MAX_AGE_MS 6000u
#define J72_RESUME_DELAY_MS 30000u
#define J72_RESUME_SOC 90
#define J72_RESUME_VOLTAGE_UV 4100000
#define J72_RESUME_TEMP_TENTHC 365

enum j72_maintain_mode {
 J72_OFF, J72_RUNNING, J72_WAIT_FULL, J72_WAIT_COOL,
 J72_WAIT_WINDOW, J72_WAIT_START, J72_FAULT
};
struct j72_maintain {
 bool enabled, fault, sample_valid;
 enum j72_maintain_mode mode;
 int sample[5], sample_error, error;
 u64 sample_at_ms, stopped_at_ms;
 unsigned int cycles, pauses;
};

static int j72_maintain_pause(struct j72_maintain *m,
 struct j72_limit_state *p, const struct j72_limit_io *io,
 u64 now, enum j72_maintain_mode mode, int error, bool fatal)
{
 bool was_active = p->active;
 if (m->fault) {fatal=true;if (!error) error=m->error;}
 int ret = j72_limit_restore(p, io);
 if (was_active) {m->pauses++; m->stopped_at_ms=now;}
 if (ret || p->restore_failed) {fatal=true;error=ret ? ret : -EIO;}
 m->mode=fatal ? J72_FAULT : mode;
 m->fault=fatal; m->error=error;
 if (fatal) m->enabled=false;
 return ret ? ret : error;
}

/* Root explicitly requalifies after a stopped fault. This never enables
 * charging, and a failed/unverified restoration can never be reset here. */
static int j72_maintain_requalify(struct j72_maintain *m,
 struct j72_limit_state *p, const struct j72_limit_io *io,
 u64 now, int source_error, int pmic_error)
{
 unsigned int value;
 int ret;
 if (!m->fault || m->enabled || p->active || p->touched || p->restore_failed ||
     (p->used && !p->restored)) return -EPERM;
 if (source_error || pmic_error) return source_error ? source_error : pmic_error;
 if (!m->sample_valid || m->sample_error || now<m->sample_at_ms ||
     now-m->sample_at_ms>=J72_GAUGE_MAX_AGE_MS) return -ETIMEDOUT;
 if (m->sample[0]!=1 || m->sample[1]<10 || m->sample[1]>100 ||
     m->sample[2]<200 || m->sample[2]>500 || m->sample[3]<3500000 ||
     m->sample[3]>4400000 || m->sample[4]<-1500000 || m->sample[4]>1500000)
  return -ERANGE;
 ret=io->read(io->ctx,&value);
 if (ret || value!=J72_HANDOFF) return ret ? ret : -EPERM;
 m->fault=false;m->error=0;m->mode=J72_OFF;p->error=0;
 return 0;
}

static int j72_maintain_step(struct j72_maintain *m,
 struct j72_limit_state *p, const struct j72_limit_io *io,
 u64 now, int source_error, int pmic_error)
{
 unsigned int faults, value;
 int ret;
 if (!m->enabled || m->fault) return 0;
 if (source_error || pmic_error)
  return j72_maintain_pause(m,p,io,now,J72_FAULT,
                            source_error ? source_error : pmic_error,true);
 if (!m->sample_valid || m->sample_error || now < m->sample_at_ms ||
     now-m->sample_at_ms >= J72_GAUGE_MAX_AGE_MS)
  return j72_maintain_pause(m,p,io,now,J72_FAULT,
                            m->sample_error ? m->sample_error : -ETIMEDOUT,true);
 faults=j72_limit_pack_faults(m->sample[0],m->sample[1],m->sample[2],m->sample[3],m->sample[4]);
 /* High SOC/voltage/temperature are holds, never permission to charge beyond
  * the old cutoffs. Missing/low/invalid data and excessive current latch off. */
 if ((faults & (1u|16u)) || m->sample[1]<10 || m->sample[1]>100 ||
     m->sample[2]<200 || m->sample[2]>500 ||
     m->sample[3]<3500000 || m->sample[3]>4400000)
  return j72_maintain_pause(m,p,io,now,J72_FAULT,-ERANGE,true);
 if (m->sample[2]>380)
  return j72_maintain_pause(m,p,io,now,J72_WAIT_COOL,0,false);
 if (m->sample[1]>95 || m->sample[3]>4200000)
  return j72_maintain_pause(m,p,io,now,J72_WAIT_FULL,0,false);
 if (p->active) {
  ret=j72_limit_check(p,io,now,0);
  if (ret || p->error || p->restore_failed)
   return j72_maintain_pause(m,p,io,now,J72_FAULT,ret ? ret : p->error,true);
  if (!p->active) {
   m->pauses++;m->stopped_at_ms=now;
   return j72_maintain_pause(m,p,io,now,J72_WAIT_WINDOW,0,false);
  }
  m->mode=J72_RUNNING;return 0;
 }
 /* An expired window's successful restore is necessary but not a new start
  * permission. Require cooldown plus the same conservative restart thresholds. */
 if (m->mode==J72_WAIT_WINDOW && !m->stopped_at_ms) m->stopped_at_ms=now;
 ret=io->read(io->ctx,&value);
 if (ret || value!=J72_HANDOFF || p->touched || p->restore_failed ||
     (p->used && !p->restored))
  return j72_maintain_pause(m,p,io,now,J72_FAULT,ret ? ret : -EPERM,true);
 if (m->sample[1]>J72_RESUME_SOC || m->sample[3]>J72_RESUME_VOLTAGE_UV) {
  m->mode=J72_WAIT_FULL;return 0;
 }
 if (m->sample[2]>J72_RESUME_TEMP_TENTHC) {
  m->mode=J72_WAIT_COOL;return 0;
 }
 if (m->cycles && (now<m->stopped_at_ms ||
     now-m->stopped_at_ms<J72_RESUME_DELAY_MS)) return 0;
 /* Only this path clears the one-window state; all restoration checks above
  * precede it. A latched hardware/read/source fault cannot reach this path. */
 *p=(struct j72_limit_state){0};
 ret=j72_limit_start(p,io,now,0);
 if (ret || !p->active)
  return j72_maintain_pause(m,p,io,now,J72_FAULT,ret ? ret : -EIO,true);
 m->cycles++;m->mode=J72_RUNNING;return 0;
}
#endif
