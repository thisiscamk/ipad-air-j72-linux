#!/usr/bin/env python3
"""Exercise the actual HSIC observer init/cleanup with host API fault injection."""
from pathlib import Path
import importlib.util
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).with_name('j72_hsic_phy_observer_v2.c')
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
struct device { int unused; };
struct platform_device { struct device dev; };
struct resource { uint64_t start, end; };
struct of_phandle_args { int args_count; struct device_node *np; };
struct uts { const char *version; };
enum { OK, MACHINE, VERSION, NODE, RESOURCE, PARENT, BUSY, MAP, ALLOC,
       ATTACH, RESUME, ACTIVE, SUSPEND, DETACH, RESTORE, AUTO, TOTAL };
static int fault, refs, mapped, allocated, linked, enabled, usage, read_words, widget_reads;
static unsigned int gates[2] = {0x200, 0x200};
static struct device_node pmgr_node = {0, NULL};
static struct device_node phy_node = {1, &pmgr_node}, host_node = {2, &pmgr_node}, wrong_node = {3, NULL};
static struct platform_device fake_device;
static bool of_machine_is_compatible(const char *s) { return fault != MACHINE; }
static struct uts *utsname(void) {
 static struct uts u;
 u.version = fault == VERSION ? "wrong" : "#33 SMP PREEMPT Sat Oct 31 11:57:21 +08 2026";
 return &u;
}
static struct device_node *of_find_node_by_path(const char *s) {
 struct device_node *n = strstr(s,"@20120") ? &phy_node : &host_node;
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
 if (fault == MAP && a == 0x20c000050ULL) return NULL;
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
 assert(a == 0x20c000050ULL || a == 0x20c000058ULL);
 assert(((gates[0] & 255) == 255 || gates[0] == 0x1400024f) && (gates[1] & 255) == 255);
 read_words++; return a == 0x20c000050ULL ? 7 : 0;
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
'''
MAIN = r'''
int main(int argc, char **argv) {
 assert(argc == 2); fault = atoi(argv[1]);
 if (fault == BUSY) gates[0] = 0x2ff;
 int rc = observer_init();
 assert(!refs && !mapped);
 if (fault == MACHINE || fault == VERSION) { assert(rc == -ENODEV); }
 else { assert(rc == 0); }
 if (fault == OK || fault == AUTO) {
  assert(result == 0 && observed && restored && consumer_removed);
  assert(read_words == 2 && widget_reads == 12 && control == 7 && config == 0);
 } else if (fault != MACHINE && fault != VERSION) { assert(result < 0); }
 if (fault == SUSPEND || fault == DETACH) {
  assert(allocated && linked && !consumer_removed && !enabled && !usage);
 } else { assert(!allocated && !linked && !enabled && !usage); }
 if (fault == SUSPEND || fault == RESTORE) { assert(!restored); }
 if (fault != OK && fault != AUTO && fault != SUSPEND && fault != DETACH && fault != RESTORE)
  assert(!observed && !read_words);
 assert(domain_ready(0x2ff) && domain_ready(0x1400024f));
 assert(!domain_ready(0x24f) && !domain_ready(0x1400020f) && !domain_ready(0x14000240));
 char buf[PAGE_SIZE]; status_get(buf, NULL); assert(strstr(buf,"result="));
 puts("PASS"); return 0;
}
'''


def main():
    source = re.sub(r'^#include <linux/[^\n]+\n', '', SOURCE.read_text(), flags=re.M)
    with tempfile.TemporaryDirectory(prefix='j72-hsic-cleanup-') as directory:
        src = Path(directory) / 'test.c'
        binary = Path(directory) / 'test'
        src.write_text(STUBS + source + MAIN)
        subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra',
                        '-Wno-unused-parameter', '-Wno-unused-function',
                        '-fsanitize=undefined', '-fno-sanitize-recover=all',
                        str(src), '-o', str(binary)], check=True)
        for fault in range(16):
            result = subprocess.run([str(binary), str(fault)], capture_output=True, text=True)
            assert result.returncode == 0, (fault, result.stdout, result.stderr)
    spec = importlib.util.spec_from_file_location('observer_runner', Path(__file__).with_name('run-j72-hsic-phy-observer-v2.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    good = dict(ready='1', used='1', active='0', armed='0', restored='1', restore_failed='0')
    encode = lambda values: ''.join(key+'='+value+'\n' for key, value in values.items()).encode()
    module.stopped_trial(encode(good))
    for key, value in good.items():
        bad = dict(good, **{key: '0' if value == '1' else '1'})
        try:
            module.stopped_trial(encode(bad))
        except AssertionError:
            continue
        raise AssertionError('Accepted unsafe charge state: ' + key)
    print('PASS: 16 actual-source init/cleanup fault paths under UBSan; six unsafe charging-state refusals. Host simulation only.')


if __name__ == '__main__':
    main()
