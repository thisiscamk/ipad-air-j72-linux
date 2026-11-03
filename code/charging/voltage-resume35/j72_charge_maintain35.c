// SPDX-License-Identifier: GPL-2.0-only
/* Opt-in qualified-hub maintenance with bounded 1050mA windows.
 * Only PMIC register 04c0 is writable. No write on load or arm.
 * The high-priority deadline never reads the gauge. Gauge reads occur
 * outside policy_lock, on a separate queue, so HDQ waits cannot block it.
 */
#include <linux/device.h>
#include <linux/i2c.h>
#include <linux/init.h>
#include <linux/input.h>
#include <linux/ktime.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/of.h>
#include <linux/platform_device.h>
#include "core.h"
#include <linux/power/bq27xxx_battery.h>
#include <linux/power_supply.h>
#include <linux/reboot.h>
#include <linux/regmap.h>
#include <linux/slab.h>
#include <linux/suspend.h>
#include <linux/utsname.h>
#include <linux/workqueue.h>
#include "j72-limit-core.h"
#include "j72-maintain-core.h"

#define EXPECTED_BUILD "#35 SMP PREEMPT Mon Nov 2 07:00:00 +08 2026"
#define PMIC_PATH "/soc/i2c@20a110000/pmic@3c"
#define BATTERY_PATH "/soc/serial@20a0b4000/battery"

static DEFINE_MUTEX(policy_lock);
static struct j72_limit_state policy;
static struct j72_maintain maintain;
static int maintain_pmic_error;
static struct device *pmic, *udc;
static u64 source_lease_until;
static struct regmap *map;
static struct power_supply *battery;
static struct workqueue_struct *deadline_queue, *guard_queue;
static bool ready, armed, power_down;
static struct input_handle *home_handle;
static unsigned int samples;
static int baseline_current, current_min, current_max;
/* Stored under policy_lock after gauge I/O; frozen first failed reading. */
static int guard_values[5], guard_failed_values[5];
static unsigned int guard_faults, guard_failed_faults;
static u64 guard_at_ms, guard_failed_at_ms;
static unsigned int read_failures, fresh_refreshes, read_recoveries;
static int last_read_errno, last_failed_prop;
static u64 last_read_failure_ms;

static void deadline_fn(struct work_struct *work);
static void guard_fn(struct work_struct *work);
static void request_fn(struct work_struct *work);
static void abort_fn(struct work_struct *work);
static DECLARE_DELAYED_WORK(deadline_work, deadline_fn);
static DECLARE_DELAYED_WORK(guard_work, guard_fn);
static DECLARE_WORK(request_work, request_fn);
static DECLARE_WORK(abort_work, abort_fn);

static u64 now_ms(void)
{
	return ktime_to_ms(ktime_get_boottime());
}

/* Exact-kernel read-only gadget state, protected against driver removal.
 * A configured gadget is necessary but does not identify a charging source.
 * The host must also renew a lease after verifying the qualified hub port.
 */
static int source_guard(void)
{
 struct dwc2_hsotg *hsotg;
 int ret = -ENOTCONN;
 if (!j72_source_lease_valid(now_ms(), source_lease_until)) return -ETIME;
 if (!udc || !device_trylock(udc)) return -EBUSY;
 if (udc->driver && !strcmp(dev_driver_string(udc), "dwc2")) {
  hsotg = dev_get_drvdata(udc);
  if (hsotg && READ_ONCE(hsotg->gadget.state) == USB_STATE_CONFIGURED &&
      READ_ONCE(hsotg->gadget.speed) == USB_SPEED_HIGH) ret = 0;
 }
 device_unlock(udc);
 return ret;
}

static int lease_set(const char *value, const struct kernel_param *unused)
{
 int ret = 0;
 if (!sysfs_streq(value, "qualified-JCH377-1500mA")) return -EINVAL;
 mutex_lock(&policy_lock);
 if (!ready || policy.restore_failed) ret = -EPERM;
 else source_lease_until = now_ms() + J72_LEASE_MS;
 mutex_unlock(&policy_lock);
 return ret;
}
static const struct kernel_param_ops lease_ops = { .set = lease_set };
module_param_cb(source_lease, &lease_ops, NULL, 0200);

static int read_limit(void *unused, unsigned int *value)
{
	return regmap_read_bypassed(map, 0x04c0, value);
}

static int write_limit(void *unused, unsigned int value)
{
	u64 now, remaining;

	if (value != J72_HANDOFF && value != J72_TRIAL)
		return -EPERM;
	if (value == J72_TRIAL) {
		/* This callback is reached only after the core records ownership. */
		now = now_ms();
		remaining = policy.deadline_ms > now ? policy.deadline_ms - now : 0;
		if (!remaining)
			return -ETIME;
		mod_delayed_work(deadline_queue, &deadline_work,
				 msecs_to_jiffies(min_t(u64, 250, remaining)));
	}
	return regmap_write(map, 0x04c0, value);
}

static const struct j72_limit_io io = {
	.read = read_limit,
	.write = write_limit,
};

static int pmic_guard(void)
{
	static const unsigned int ceiling_regs[] = {0x04c6, 0x04c7, 0x04ce};
	unsigned int value, i;
	int ret;

	ret = regmap_read_bypassed(map, 0x0010, &value);
	if (ret || (value & BIT(2)))
		return ret ? ret : -EPERM;
	for (i = 0; i < ARRAY_SIZE(ceiling_regs); i++) {
		ret = regmap_read_bypassed(map, ceiling_regs[i], &value);
		if (ret || value != 0x3f)
			return ret ? ret : -EPERM;
	}
	return 0;
}

/* A failed flags refresh is cached for five seconds by the core. Retry one
 * complete vector after an explicit fresh core update, never a stale value.
 * The separate source/deadline queue remains active during all gauge I/O.
 */
static int pack_values(int *values)
{
 static const enum power_supply_property props[] = {
  POWER_SUPPLY_PROP_PRESENT, POWER_SUPPLY_PROP_CAPACITY,
  POWER_SUPPLY_PROP_TEMP, POWER_SUPPLY_PROP_VOLTAGE_NOW,
  POWER_SUPPLY_PROP_CURRENT_NOW,
 };
 union power_supply_propval v;
 unsigned int attempt, i;
 int ret = -EIO;
 for (attempt = 0; attempt < 2; attempt++) {
  for (i = 0; i < ARRAY_SIZE(props); i++) {
   ret = power_supply_get_property(battery, props[i], &v);
   if (ret) break;
   values[i] = v.intval;
  }
  if (!ret) {
   if (attempt) {
    mutex_lock(&policy_lock); read_recoveries++; mutex_unlock(&policy_lock);
   }
   return 0;
  }
  mutex_lock(&policy_lock);
  read_failures++; last_read_errno = ret; last_failed_prop = props[i];
  last_read_failure_ms = now_ms();
  mutex_unlock(&policy_lock);
  if (attempt || (ret != -ETIMEDOUT && ret != -EIO)) return ret;
  mutex_lock(&policy_lock); fresh_refreshes++; mutex_unlock(&policy_lock);
  bq27xxx_battery_update(power_supply_get_drvdata(battery));
 }
 return ret;
}

/* Never hold policy_lock around this function: a gauge access can wait. */


static void finish_locked(void)
{
 armed = maintain.enabled;
}

static void deadline_fn(struct work_struct *work)
{
 mutex_lock(&policy_lock);
 if (maintain.enabled) {
  j72_maintain_step(&maintain,&policy,&io,now_ms(),source_guard(),maintain_pmic_error);
  finish_locked();
  if (maintain.enabled)
   mod_delayed_work(deadline_queue,&deadline_work,msecs_to_jiffies(250));
 }
 mutex_unlock(&policy_lock);
}

static void guard_fn(struct work_struct *work)
{
 int values[5], ret, pmic_ret;
 if (!READ_ONCE(ready) || !READ_ONCE(maintain.enabled)) return;
 ret=pack_values(values); /* Never hold policy_lock during HDQ. */
 pmic_ret=pmic_guard();
 mutex_lock(&policy_lock);
 if (maintain.enabled) {
  maintain.sample_error=ret;maintain_pmic_error=pmic_ret;
  if (!ret) {
   memcpy(maintain.sample,values,sizeof(values));
   memcpy(guard_values,values,sizeof(values));
   maintain.sample_at_ms=guard_at_ms=now_ms();maintain.sample_valid=true;
   guard_faults=j72_limit_pack_faults(values[0],values[1],values[2],values[3],values[4]);
   if (policy.active && j72_limit_sample_ready(&policy,now_ms())) {
    if (!samples || values[4]<current_min) current_min=values[4];
    if (!samples || values[4]>current_max) current_max=values[4];
    samples++;
   }
  }
  j72_maintain_step(&maintain,&policy,&io,now_ms(),source_guard(),maintain_pmic_error);
  finish_locked();
  if (maintain.enabled) queue_delayed_work(guard_queue,&guard_work,2*HZ);
 }
 mutex_unlock(&policy_lock);
}

static void request_fn(struct work_struct *work)
{
 int values[5],ret,pmic_ret;
 if (!READ_ONCE(ready) || !READ_ONCE(armed) || READ_ONCE(power_down)) return;
 ret=pack_values(values);pmic_ret=pmic_guard();
 mutex_lock(&policy_lock);
 if (!ready || !armed || power_down || maintain.enabled || maintain.fault) goto done;
 maintain.sample_error=ret;maintain_pmic_error=pmic_ret;
 if (!ret) {
  memcpy(maintain.sample,values,sizeof(values));
  memcpy(guard_values,values,sizeof(values));
  maintain.sample_valid=true;maintain.sample_at_ms=guard_at_ms=now_ms();
  baseline_current=values[4];
 }
 maintain.enabled=true;maintain.mode=J72_WAIT_START;
 j72_maintain_step(&maintain,&policy,&io,now_ms(),source_guard(),maintain_pmic_error);
 finish_locked();
 if (maintain.enabled) {
  mod_delayed_work(deadline_queue,&deadline_work,msecs_to_jiffies(250));
  queue_delayed_work(guard_queue,&guard_work,2*HZ);
 }
done:
 mutex_unlock(&policy_lock);
}

static void abort_fn(struct work_struct *work)
{
 mutex_lock(&policy_lock);
 armed=false;maintain.enabled=false;
 j72_maintain_pause(&maintain,&policy,&io,now_ms(),J72_OFF,0,false);
 mutex_unlock(&policy_lock);
}

static void home_event(struct input_handle *handle, unsigned int type,
                       unsigned int code, int value)
{
 if (type!=EV_KEY || !READ_ONCE(ready) || code!=KEY_POWER) return;
 WRITE_ONCE(power_down,value!=0);
 if (value==1) {
  WRITE_ONCE(armed,false);
  queue_work(deadline_queue,&abort_work);
 }
 /* Home remains available to the desktop and cannot start charging. */
}

static int home_connect(struct input_handler *handler, struct input_dev *dev,
			const struct input_device_id *id)
{
	struct input_handle *handle;
	int ret;

	if (!dev->name || strcmp(dev->name, "gpio-keys") ||
	    !test_bit(KEY_HOMEPAGE, dev->keybit)) return -ENODEV;
	if (home_handle) return -EBUSY;
	handle = kzalloc(sizeof(*handle), GFP_KERNEL);
	if (!handle) return -ENOMEM;
	handle->dev = dev; handle->handler = handler; handle->name = "j72-input-trial";
	ret = input_register_handle(handle);
	if (ret) goto free;
	ret = input_open_device(handle);
	if (ret) { input_unregister_handle(handle); goto free; }
	home_handle = handle;
	return 0;
free:
	kfree(handle);
	return ret;
}

static void home_disconnect(struct input_handle *handle)
{
	WRITE_ONCE(armed, false);
	input_close_device(handle);
	input_unregister_handle(handle);
	home_handle = NULL;
	if (READ_ONCE(ready)) queue_work(deadline_queue, &abort_work);
	kfree(handle);
}

static const struct input_device_id home_ids[] = {
	{ .flags = INPUT_DEVICE_ID_MATCH_EVBIT, .evbit = { BIT_MASK(EV_KEY) } },
	{ },
};
static struct input_handler home_handler = {
	.event = home_event, .connect = home_connect, .disconnect = home_disconnect,
	.name = "j72-charge-maintain34", .id_table = home_ids,
};

static int arm_set(const char *value, const struct kernel_param *unused)
{
 unsigned int limit;
 int ret=0;
 bool on;
 if (sysfs_streq(value,"maintain-qualified-JCH377")) on=true;
 else if (sysfs_streq(value,"stop")) on=false;
 else return -EINVAL;
 mutex_lock(&policy_lock);
 armed=false;
 if (!on) {
  maintain.enabled=false;
  j72_maintain_pause(&maintain,&policy,&io,now_ms(),J72_OFF,0,maintain.fault);
  ret=policy.restore_failed ? -EIO : 0;
 } else if (!ready || maintain.enabled || maintain.fault || policy.restore_failed || power_down) ret=-EPERM;
 else {
  ret=source_guard();
  if (!ret) ret=pmic_guard();
  if (!ret) ret=read_limit(NULL,&limit);
  if (!ret && limit!=J72_HANDOFF) ret=-EPERM;
  if (!ret) armed=true;
 }
 mutex_unlock(&policy_lock);
 return ret;
}
static const struct kernel_param_ops arm_ops = { .set = arm_set };
module_param_cb(arm_hub, &arm_ops, NULL, 0200);

/* Explicit enable after host source qualification. Home never arms/starts it. */
static int begin_set(const char *value, const struct kernel_param *unused)
{
 int ret=0;
 if (!sysfs_streq(value,"begin-qualified-maintenance")) return -EINVAL;
 mutex_lock(&policy_lock);
 if (!ready || !armed || maintain.enabled || maintain.fault || power_down || policy.restore_failed) ret=-EPERM;
 else schedule_work(&request_work);
 mutex_unlock(&policy_lock);
 return ret;
}
static const struct kernel_param_ops begin_ops = { .set = begin_set };
module_param_cb(begin_session, &begin_ops, NULL, 0200);

/* Only an explicit root request after fresh host qualification may clear
 * a stopped fault. Renewing source_lease alone never enables or clears it. */
static int requalify_set(const char *value, const struct kernel_param *unused)
{
 int values[5], ret, pmic_ret;
 if (!sysfs_streq(value,"requalify-verified-restoration")) return -EINVAL;
 if (!READ_ONCE(ready)) return -ENODEV;
 ret=pack_values(values);pmic_ret=pmic_guard();
 mutex_lock(&policy_lock);
 maintain.sample_error=ret;
 if (!ret) {
  memcpy(maintain.sample,values,sizeof(values));
  maintain.sample_valid=true;maintain.sample_at_ms=now_ms();
 }
 if (!ready || power_down) ret=-EPERM;
 else ret=j72_maintain_requalify(&maintain,&policy,&io,now_ms(),source_guard(),pmic_ret);
 mutex_unlock(&policy_lock);
 return ret;
}
static const struct kernel_param_ops requalify_ops = { .set = requalify_set };
module_param_cb(requalify_source, &requalify_ops, NULL, 0200);

static int status_get(char *buf, const struct kernel_param *unused)
{
	u64 remaining, now;
	int n;

	mutex_lock(&policy_lock);
	now = now_ms();
	remaining = policy.active && policy.deadline_ms > now ? policy.deadline_ms - now : 0;
	n = scnprintf(buf, PAGE_SIZE,
		"ready=%u\narmed=%u\nused=%u\nactive=%u\nrestored=%u\nrestore_failed=%u\nerror=%d\nremaining_ms=%llu\nsource_lease_until_ms=%llu\nbaseline_current_uA=%d\ntrial_samples=%u\ntrial_current_min_uA=%d\ntrial_current_max_uA=%d\n",
		ready, armed, policy.used, policy.active, policy.restored,
		policy.restore_failed, policy.error, (unsigned long long)remaining,
		(unsigned long long)source_lease_until, baseline_current, samples, current_min, current_max);
	n += scnprintf(buf + n, PAGE_SIZE - n,
		"guard_at_ms=%llu\nguard_faults=%u\nguard_present=%d\nguard_soc=%d\nguard_temp_tenthC=%d\nguard_voltage_uV=%d\nguard_current_uA=%d\n"
		"failed_guard_at_ms=%llu\nfailed_guard_faults=%u\nfailed_guard_present=%d\nfailed_guard_soc=%d\nfailed_guard_temp_tenthC=%d\nfailed_guard_voltage_uV=%d\nfailed_guard_current_uA=%d\n",
		(unsigned long long)guard_at_ms, guard_faults,
		guard_values[0], guard_values[1], guard_values[2], guard_values[3], guard_values[4],
		(unsigned long long)guard_failed_at_ms, guard_failed_faults,
		guard_failed_values[0], guard_failed_values[1], guard_failed_values[2],
		guard_failed_values[3], guard_failed_values[4]);
 n += scnprintf(buf + n, PAGE_SIZE - n,
  "read_failures=%u\nfresh_refreshes=%u\nread_recoveries=%u\nlast_read_errno=%d\nlast_failed_prop=%d\nlast_read_failure_ms=%llu\n",
  read_failures, fresh_refreshes, read_recoveries, last_read_errno,
  last_failed_prop, (unsigned long long)last_read_failure_ms);
 n += scnprintf(buf+n,PAGE_SIZE-n,
  "enabled=%u\nfault=%u\nmode=%u\ncycles=%u\npauses=%u\ncontroller_error=%d\nsample_at_ms=%llu\n",
  maintain.enabled,maintain.fault,maintain.mode,maintain.cycles,maintain.pauses,
  maintain.error,(unsigned long long)maintain.sample_at_ms);
 n += scnprintf(buf+n,PAGE_SIZE-n,
  "resume_policy=1\nlast_pause=%u\nthermal_latched=%u\nwarm_full_resumes=%u\n",
  maintain.last_pause,maintain.thermal_latched,maintain.warm_full_resumes);
 mutex_unlock(&policy_lock);
 return n;
}
static const struct kernel_param_ops status_ops = { .get = status_get };
module_param_cb(status, &status_ops, NULL, 0400);

static int prepare_stop(void)
{
	int ret;
	WRITE_ONCE(armed, false);
	mutex_lock(&policy_lock);
	maintain.enabled=false;
	j72_maintain_pause(&maintain,&policy,&io,now_ms(),J72_OFF,0,maintain.fault);
	ret=policy.restore_failed ? -EIO : 0;
	mutex_unlock(&policy_lock);
	return ret;
}
static int pm_event(struct notifier_block *nb, unsigned long event, void *unused)
{
	if (event == PM_SUSPEND_PREPARE || event == PM_HIBERNATION_PREPARE ||
	    event == PM_RESTORE_PREPARE) return notifier_from_errno(prepare_stop());
	return NOTIFY_DONE;
}
static int reboot_event(struct notifier_block *nb, unsigned long event, void *unused)
{
	prepare_stop();
	return NOTIFY_DONE;
}
static struct notifier_block pm_nb = { .notifier_call = pm_event };
static struct notifier_block reboot_nb = { .notifier_call = reboot_event };

static int exact_pmic(struct device *dev, const void *node)
{
	struct i2c_client *c = i2c_verify_client(dev);
	return c && c->addr == 0x3c && dev->of_node == node &&
		of_device_is_compatible(dev->of_node, "apple,anya-pmic");
}

static int __init trial_init(void)
{
	struct device_node *node;
	struct bq27xxx_device_info *di;
	unsigned int limit;
	int ret = -ENODEV;

	if (!of_machine_is_compatible("apple,j72") ||
	    strcmp(utsname()->version, EXPECTED_BUILD)) return -ENODEV;
	node = of_find_node_by_path("/soc/bus@20c000000/usbdev@20c100000");
 if (!node) return -ENODEV;
 udc = bus_find_device_by_of_node(&platform_bus_type, node);
 of_node_put(node);
 if (!udc) return -ENODEV;
 node = of_find_node_by_path(PMIC_PATH);
	if (!node) { put_device(udc); return -ENODEV; }
	pmic = bus_find_device(&i2c_bus_type, NULL, node, exact_pmic);
	of_node_put(node);
	if (!pmic) { put_device(udc); return -ENODEV; }
	map = dev_get_regmap(pmic, NULL);
	if (!pmic->driver || !map || regmap_get_val_bytes(map) != 1) goto put_pmic;
	battery = power_supply_get_by_name("j72-bq27545-battery");
	if (!battery) goto put_pmic;
	di = power_supply_get_drvdata(battery);
	node = of_find_node_by_path(BATTERY_PATH);
	if (!di || !node || di->dev->of_node != node || di->chip != BQ27545 ||
	    strcmp(dev_driver_string(di->dev), "bq27xxx-hdq-uart")) {
		of_node_put(node); goto put_battery;
	}
	of_node_put(node);
	ret = pmic_guard();
	if (!ret) ret = read_limit(NULL, &limit);
	if (!ret && limit != J72_HANDOFF) ret = -EPERM;
	if (ret) goto put_battery;
	deadline_queue = alloc_workqueue("j72-limit-deadline", WQ_UNBOUND | WQ_HIGHPRI | WQ_MEM_RECLAIM, 1);
	guard_queue = alloc_workqueue("j72-limit-gauge", WQ_UNBOUND | WQ_MEM_RECLAIM, 1);
	if (!deadline_queue || !guard_queue) { ret = -ENOMEM; goto destroy; }
	ret = register_pm_notifier(&pm_nb);
	if (ret) goto destroy;
	ret = register_reboot_notifier(&reboot_nb);
	if (ret) goto unreg_pm;
	ret = input_register_handler(&home_handler);
	if (ret) goto unreg_reboot;
	if (!home_handle) { ret = -ENODEV; goto unreg_input; }
	WRITE_ONCE(ready, true);
	pr_info("j72 input trial: ready, disabled; qualified-hub maintenance only; NO write at load\n");
	return 0;
unreg_input:
	input_unregister_handler(&home_handler);
unreg_reboot:
	unregister_reboot_notifier(&reboot_nb);
unreg_pm:
	unregister_pm_notifier(&pm_nb);
destroy:
	if (deadline_queue) destroy_workqueue(deadline_queue);
	if (guard_queue) destroy_workqueue(guard_queue);
put_battery:
	power_supply_put(battery);
put_pmic:
	put_device(pmic);
	put_device(udc);
	return ret;
}

static void __exit trial_exit(void)
{
	WRITE_ONCE(ready, false);
	prepare_stop();
	input_unregister_handler(&home_handler);
	unregister_reboot_notifier(&reboot_nb);
	unregister_pm_notifier(&pm_nb);
	cancel_work_sync(&request_work);
	cancel_work_sync(&abort_work);
	cancel_delayed_work_sync(&guard_work);
	cancel_delayed_work_sync(&deadline_work);
	destroy_workqueue(guard_queue);
	destroy_workqueue(deadline_queue);
	power_supply_put(battery);
	put_device(pmic);
	put_device(udc);
}
module_init(trial_init);
module_exit(trial_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Exact J72/#35 opt-in hub maintenance; unchanged limits, source lease and per-window rollback");
