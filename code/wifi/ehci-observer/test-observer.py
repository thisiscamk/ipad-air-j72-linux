#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Actual-source fault tests, flattened synthetic APIs; no USB/device access."""
from pathlib import Path
import re
import subprocess
import tempfile

STUBS = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
typedef uint32_t u32;
#define __iomem
#define __init
#define __exit
#define PAGE_SIZE 4096
#define scnprintf snprintf
#define module_param(...)
#define module_param_cb(...)
#define module_init(...)
#define module_exit(...)
#define MODULE_LICENSE(...)
#define MODULE_DESCRIPTION(...)
#define pr_info(...) ((void)0)
#define IS_ERR(p) ((intptr_t)(p) < 0)
#define PTR_ERR(p) ((intptr_t)(p))
struct kernel_param { int unused; };
struct kernel_param_ops { int (*get)(char *, const struct kernel_param *); };
struct device_node { int id; struct device_node *parent; };
struct device { void *driver; struct device_node *of_node; };
struct platform_device { struct device dev; };
struct resource { uint64_t start, end; };
struct of_phandle_args { int args_count; struct device_node *np; };
struct uts { const char *version; };
enum { OK, MACHINE, VERSION, NODE, RESOURCE, PARENT, BUSY, MAP, ALLOC,
       ATTACH, RESUME, ACTIVE, SUSPEND, DETACH, RESTORE, AUTO, BAD_BASELINE, INIT_WRITE, RESTORE_WRITE, NO_CONFIRM,
 PMU_MISSING, PMU_READ, PMU_RELEASE, PMU_VERIFY, PMU_RESTORE, READY_LOW, READY_MUX, GPIO_BASELINE, GPIO_MISSING, GPIO_BUSY, GPIO_DIRECTION, GPIO_CLAIM_CHANGE, HOST_SET_ERROR, HOST_HIGH_VERIFY, HOST_LOW_ERROR, HOST_RESTORE_FAIL, READY_ON_HOST_HIGH, GDEV_ERROR, LABEL_MISSING, DIRECTION_ERROR, EHCI_CAPS, EHCI_RUNNING, EHCI_UNHALTED, EHCI_MAP, TOTAL };
static int fault, refs, mapped, allocated, linked, enabled, usage, read_words, widget_reads;
static unsigned int gates[2] = {0x200, 0x200};
static struct device_node pmgr_node = {0, NULL};
static struct device_node phy_node = {1, &pmgr_node}, host_node = {2, &pmgr_node}, wrong_node = {3, NULL};

static struct platform_device fake_device;
static struct device_node pmu_node = {4, NULL}, gpio_node = {5, NULL};
static int host_level, gpio_claimed, gdev_refs, lookup_count, low_attempts;
static bool changed_mux;
struct gpio_device { int unused; }; struct gpio_desc { int unused; };
static struct gpio_device fake_gdev; static struct gpio_desc fake_desc;
struct gpiod_lookup { const char *key; unsigned int chip_hwnum; const char *con_id; unsigned int idx, flags; };
struct gpiod_lookup_table { const char *dev_id; struct gpiod_lookup table[2]; };
#define GPIO_ACTIVE_HIGH 0
#define GPIOD_ASIS 0

static u32 phy_control = 4, phy_config = 0x153, written[8], delays[4];
static unsigned int write_count, delay_count, pmu_raw = 9, pmu_refs, pmu_reads, pmu_writes;
struct i2c_client { struct device dev; unsigned int addr; };
static struct i2c_client fake_pmu;
struct regmap { int unused; };
static struct regmap fake_map;
static int i2c_bus_type;

static bool of_machine_is_compatible(const char *s) { return fault != MACHINE; }
static struct uts *utsname(void) {
 static struct uts u;
 u.version = fault == VERSION ? "wrong" : "#33 SMP PREEMPT Sat Oct 31 11:57:21 +08 2026";
 return &u;
}
static struct device_node *of_find_node_by_path(const char *s) {
 struct device_node *n = strstr(s,"pinctrl@20e300000") ? &gpio_node : strstr(s,"pmic@3c") ? &pmu_node : (strstr(s,"@20120") ? &phy_node : &host_node);
 if (fault == NODE && n == &phy_node) return NULL;
 refs++; return n;
}
static void of_node_put(struct device_node *n) { if (n) refs--; }
static bool of_device_is_compatible(struct device_node *n, const char *s) { return true; }
static int of_address_to_resource(struct device_node *n, int index, struct resource *r) {
 assert(n == &pmgr_node);
 r->start = fault == RESOURCE ? 0 : 0x20e000000ULL; r->end = r->start + 0x24000 - 1; return 0;
}
static int of_property_read_u32_array(struct device_node *n, const char *s, u32 *out, int count) {
 assert(count == 2 && !strcmp(s,"reg"));
 out[0] = n == &phy_node ? 0x20120 : 0x20170; out[1] = 4; return 0;
}
static uint64_t resource_size(struct resource *r) { return r->end-r->start+1; }
static struct device_node *of_parse_phandle(struct device_node *n, const char *s, int i) {
 refs++; return fault == PARENT ? &wrong_node : &host_node;
}
static void *ioremap(uint64_t a, size_t n) {
 if ((fault == MAP && a == 0x20c000050ULL) || (fault == EHCI_MAP && a == 0x20c200000ULL)) return NULL;
 mapped++; return (void *)(uintptr_t)a;
}
static void iounmap(void *p) { assert(p); mapped--; }
static u32 readl(const void *p) {
 uint64_t a = (uintptr_t)p;
 if (a == 0x20e020120ULL) return gates[0];
 if (a == 0x20e020170ULL) return gates[1];
 if (a >= 0x20c90001cULL && a <= 0x20c90007cULL) {
  assert((a-0x20c90001cULL) % 0x20 == 0); widget_reads++; return 0x108;
 }

 if (a == 0x20e300000ULL + 163 * 4) return (fault == GPIO_BASELINE ? 0x72603 : (0x72602 | host_level)) ^ (changed_mux ? 0x20 : 0);
 if (a == 0x20e300000ULL + 164 * 4) {
  if (pmu_raw != 0xb || fault == READY_LOW || (fault == READY_ON_HOST_HIGH && !host_level)) return 0x70200;
  return fault == READY_MUX ? 0x70240 : 0x70201;
 }
 if (a >= 0x20c200000ULL && a < 0x20c210000ULL) {
  switch (a - 0x20c200000ULL) {
   case 0: return fault == EHCI_CAPS ? 0 : 0x01000010;
   case 4: return 0x1313;
   case 8: return 0x2a026;
   case 0x10: return fault == EHCI_RUNNING ? 0x80001 : 0x80000;
   case 0x14: return fault == EHCI_UNHALTED ? 0 : 0x1000;
   case 0x18: case 0x24: case 0x28: case 0x50: case 0x5c: return 0;
   default: assert(0);
  }
 }
 assert(a == 0x20c000050ULL || a == 0x20c000058ULL);
 assert(((gates[0] & 255) == 255 || gates[0] == 0x1400024f) && (gates[1] & 255) == 255);
 read_words++; return a == 0x20c000050ULL ? phy_control : phy_config;
}
static void usleep_range(int a, int b) { }
static struct platform_device *platform_device_register_simple(const char *s, int id, void *r, int nr) {
 if (fault == ALLOC) return (void *)(intptr_t)-ENOMEM;
 assert(!allocated); allocated = 1; return &fake_device;
}
static void platform_device_unregister(struct platform_device *p) {
 assert(allocated && !linked && !enabled && !usage); allocated = 0;
}
static int of_genpd_add_device(struct of_phandle_args *s, struct device *d) {
 assert(allocated && !linked && s->np == &phy_node && !s->args_count);
 if (fault == ATTACH) return -ENODEV;
 linked = 1; return 0;
}
static void pm_runtime_enable(struct device *d) { assert(linked && !enabled); enabled = 1; }
static void pm_runtime_disable(struct device *d) { assert(enabled); enabled = 0; }
static int pm_runtime_resume_and_get(struct device *d) {
 assert(linked && enabled && !usage);
 if (fault == RESUME) return -EIO;
 usage = 1; gates[0] = fault == ACTIVE ? 0x20f : (fault == AUTO ? 0x1400024f : 0x2ff); gates[1] = 0x2ff; return 0;
}
static int pm_runtime_put_sync_suspend(struct device *d) {
 assert(linked && enabled && usage == 1); usage = 0;
 if (fault == SUSPEND) return -EBUSY;
 gates[0] = fault == RESTORE ? 0x2ff : 0x200; gates[1] = 0x200; return 0;
}
static int pm_genpd_remove_device(struct device *d) {
 assert(allocated && linked && !enabled && !usage);
 if (fault == DETACH) return -EAGAIN;
 linked = 0; return 0;
}

static void writel(u32 value, void *address) {
 assert((uintptr_t)address == 0x20c000050ULL);
 assert(linked && enabled && usage == 1 && write_count < 4);
 if (value == 4) assert(pmu_raw == 9); /* Reset restored BEFORE PHY off. */
 written[write_count++] = value;
 if ((fault == INIT_WRITE && write_count == 3) ||
     (fault == RESTORE_WRITE && write_count == 4)) return;
 phy_control = value;
}
static void udelay(unsigned int n) { assert(delay_count < 2); delays[delay_count++] = n; }
static struct i2c_client *i2c_verify_client(struct device *d) { return d == &fake_pmu.dev ? &fake_pmu : NULL; }
static struct device *bus_find_device(int *bus, void *start, const void *node,
                                     int (*match)(struct device *, const void *)) {
 assert(bus == &i2c_bus_type && node == &pmu_node);
 if (fault == PMU_MISSING) return NULL;
 fake_pmu.addr = 0x3c; fake_pmu.dev.driver = (void *)1;
 fake_pmu.dev.of_node = &pmu_node;
 assert(match(&fake_pmu.dev, node)); pmu_refs++; return &fake_pmu.dev;
}
static void put_device(struct device *d) { assert(d == &fake_pmu.dev && pmu_refs == 1); pmu_refs--; }
static struct regmap *dev_get_regmap(struct device *d, void *name) { assert(d == &fake_pmu.dev); return &fake_map; }
static int regmap_get_val_bytes(struct regmap *m) { return 1; }
static int regmap_read_bypassed(struct regmap *m, unsigned int reg, unsigned int *out) {
 assert(m == &fake_map && reg == 0x403 && pmu_refs == 1); pmu_reads++;
 if (fault == PMU_READ || (fault == PMU_VERIFY && pmu_reads == 2)) return -EIO;
 *out = pmu_raw; return 0;
}
static int regmap_write(struct regmap *m, unsigned int reg, unsigned int value) {
 assert(m == &fake_map && reg == 0x403 && pmu_refs == 1 && pmu_writes < 2);
 assert(value == (pmu_writes ? 9 : 0xb));
 assert(phy_control == 0 && linked && usage == 1);
 pmu_writes++;
 if (fault == PMU_RESTORE && value == 9) return -EIO;
 pmu_raw = value;
 return fault == PMU_RELEASE && value == 0xb ? -EIO : 0;
}

static void *of_fwnode_handle(struct device_node *n) { return n; }
static struct gpio_device *gpio_device_find_by_fwnode(void *n) {
 assert(n == &gpio_node);
 if (fault == GPIO_MISSING) return NULL;
 if (fault == GDEV_ERROR) return (void *)(intptr_t)-EIO;
 gdev_refs++; return &fake_gdev;
}
static const char *gpio_device_get_label(struct gpio_device *g) {
 assert(g == &fake_gdev && gdev_refs == 1);
 return fault == LABEL_MISSING ? NULL : "test-gpio";
}
static void gpiod_add_lookup_table(struct gpiod_lookup_table *t) {
 assert(!lookup_count && !strcmp(t->dev_id,"j72-wlan-ehci-observer"));
 assert(t->table[0].chip_hwnum == 163 && !strcmp(t->table[0].key,"test-gpio"));
 assert(t->table[0].flags == GPIO_ACTIVE_HIGH); lookup_count++;
}
static void gpiod_remove_lookup_table(struct gpiod_lookup_table *t) { assert(lookup_count == 1); lookup_count--; }
static struct gpio_desc *gpiod_get(struct device *d, const char *con, int flags) {
 assert(d == &fake_device.dev && !strcmp(con,"host-ready") && flags == GPIOD_ASIS);
 assert(lookup_count == 1 && !gpio_claimed);
 if (fault == GPIO_BUSY) return (void *)(intptr_t)-EBUSY;
 gpio_claimed = 1; changed_mux = fault == GPIO_CLAIM_CHANGE; return &fake_desc;
}
static int gpiod_get_direction(struct gpio_desc *d) {
 assert(d == &fake_desc && gpio_claimed);
 if (fault == DIRECTION_ERROR) return -EIO;
 return fault == GPIO_DIRECTION ? 1 : 0;
}
static int gpiod_set_raw_value_cansleep(struct gpio_desc *d, int v) {
 assert(d == &fake_desc && gpio_claimed && pmu_raw == 0xb && phy_control == 0);
 if (!v) {
  low_attempts++;
  if (fault == HOST_RESTORE_FAIL || (fault == HOST_LOW_ERROR && low_attempts == 1)) return -EIO;
 }
 if (!(fault == HOST_HIGH_VERIFY && v)) host_level = v;
 return fault == HOST_SET_ERROR && v ? -EIO : 0;
}
static void gpiod_put(struct gpio_desc *d) { assert(d == &fake_desc && gpio_claimed && !host_level && !changed_mux); gpio_claimed = 0; }
static void gpio_device_put(struct gpio_device *g) { assert(g == &fake_gdev && gdev_refs == 1); gdev_refs--; }
'''

MAIN = r'''
int main(int argc, char **argv) {
 assert(argc == 2); fault = atoi(argv[1]); confirm_native = fault != NO_CONFIRM;
 if (fault == BUSY) gates[0] = 0x2ff;
 if (fault == BAD_BASELINE) phy_control = 7;
 int rc = observer_init();
 assert(!refs && !mapped && !pmu_refs);
 if (fault == MACHINE || fault == VERSION) assert(rc == -ENODEV);
 else if (fault == NO_CONFIRM) assert(rc == -EPERM);
 else assert(rc == 0);
 if (fault == OK || fault == AUTO || fault == READY_LOW || fault == READY_ON_HOST_HIGH) {
  assert(result == 0 && observed && restored && consumer_removed);
  assert(phy_touched && phy_restored && running_control == 0 && original_control == 4);
  assert(reset_touched && reset_restored && pmu_before == 9 && pmu_released == 0xb && pmu_after == 9);

  assert(ready_samples == 50 && ready_high_samples == ((fault == READY_LOW || fault == READY_ON_HOST_HIGH) ? 0 : 50));
  assert(high_window_samples == 50 && high_window_ready == (fault == READY_LOW ? 0 : 50));
  assert(low_window_samples == 50 && low_window_ready == ((fault == READY_LOW || fault == READY_ON_HOST_HIGH) ? 0 : 50));
  assert(host_touched && host_restored && gpio_released && host_high_cfg == 0x72603 && host_after == 0x72602);

 } else if (fault != MACHINE && fault != VERSION && fault != NO_CONFIRM) assert(result < 0);
 if (fault == SUSPEND || fault == DETACH || fault == RESTORE_WRITE || fault == PMU_RESTORE) {
  assert(allocated && linked && !consumer_removed && !enabled);
  assert(usage == ((fault == RESTORE_WRITE || fault == PMU_RESTORE) ? 1 : 0));
 } else assert(!allocated && !linked && !enabled && !usage);
 if (fault == SUSPEND || fault == RESTORE || fault == RESTORE_WRITE || fault == PMU_RESTORE) assert(!restored);
 if (fault == RESTORE_WRITE || fault == PMU_RESTORE) assert(!phy_restored && phy_control == 0);
 else if (write_count) assert(phy_restored && phy_control == 4);
 if (write_count) {
  assert(write_count == (fault == PMU_RESTORE ? 3 : 4));
  assert(written[0] == 7 && written[1] == 1 && written[2] == 0);
  if (write_count == 4) assert(written[3] == 4);
  assert(delay_count == 2 && delays[0] == 20 && delays[1] == 1000);
 }
 if (fault == PMU_RESTORE) assert(pmu_raw == 0xb && !reset_restored);
 else assert(pmu_raw == 9);
 if (pmu_writes) assert(pmu_writes == 2);
 if (fault == BAD_BASELINE || fault == NO_CONFIRM || fault == PMU_MISSING || fault == PMU_READ || fault == GPIO_BASELINE)
  assert(!write_count && !pmu_writes);
 if (fault == PMU_RELEASE || fault == PMU_VERIFY) assert(reset_restored && restored && consumer_removed);

 assert(!lookup_count);
 if (fault == HOST_RESTORE_FAIL || fault == GPIO_CLAIM_CHANGE)
  assert(gpio_claimed && gdev_refs == 1 && !gpio_released && !host_restored);
 else {
  assert(!gpio_claimed && !gdev_refs);
  if (fault != MACHINE && fault != VERSION && fault != NO_CONFIRM) assert(gpio_released);
 }
 if (fault != HOST_RESTORE_FAIL) assert(host_level == 0);
 assert(phy_config == 0x153);

 char buf[PAGE_SIZE]; status_get(buf, NULL); assert(strstr(buf,"host_gpio_after=")); char *label = strstr(buf,"\nhost_after="); assert(label && !strstr(label+1,"\nhost_after=")); assert(strstr(buf,"reset_restored="));
 puts("PASS"); return 0;
}
'''

def main():
    source = Path(__file__).with_name('j72_wlan_ehci_observer.c').read_text()
    source = re.sub(r'^#include <linux/[^\n]+\n', '', source, flags=re.M)
    with tempfile.TemporaryDirectory(prefix='j72-host-ready-') as directory:
        src, binary = Path(directory)/'test.c', Path(directory)/'test'
        src.write_text(STUBS + source + MAIN)
        subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Wno-unused-parameter',
                        '-Wno-unused-function','-fsanitize=undefined','-fno-sanitize-recover=all',
                        str(src),'-o',str(binary)],check=True)
        for fault in range(44):
            result = subprocess.run([str(binary),str(fault)],text=True,capture_output=True)
            assert result.returncode == 0,(fault,result.stdout,result.stderr)
    print('PASS: 44 actual-source rollback/ownership/EHCI refusal paths under UBSan; unknown, running and unhalted host controllers refused. No device access.')

if __name__ == '__main__':
    main()
