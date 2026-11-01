// SPDX-License-Identifier: GPL-2.0-only
/* Exact J72/#33 HSIC1 PHY observation. Linux genpd owns all gate changes.
 * No PHY, reset, GPIO or PMIC write; no host registration, DMA or firmware.
 * The existing provider is found by node, so it need not have a phandle.
 */
#include <linux/delay.h>
#include <linux/io.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/of_address.h>
#include <linux/platform_device.h>
#include <linux/pm_domain.h>
#include <linux/pm_runtime.h>
#include <linux/utsname.h>

#define DOMAIN "/soc/power-management@20e000000/power-controller@20120"
#define HOST "/soc/power-management@20e000000/power-controller@20170"
#define PHY_BASE 0x20c000050ULL
#define PHY_STATE 0x20e020120ULL
#define HOST_STATE 0x20e020170ULL
static u32 before[2], active[2], after[2], control, config;
static u32 widgets_before[4], widgets_active[4], widgets_after[4];
static int result = -EAGAIN, suspend_result, detach_result;
static bool observed, restored, consumer_removed;

static void states(void __iomem *phy, void __iomem *host, u32 *values)
{
	values[0] = readl(phy);
	values[1] = readl(host);
}

static bool domain_ready(u32 state)
{
 u32 actual = (state >> 4) & 15;
 /* Match the owning driver's auto-PM semantics, restricted to clock-gated
  * or fully active states. Never accept power-gated or target-off states.
  */
 return (state & 15) == 15 &&
        (actual == 15 || ((state & (1U << 28)) && actual == 4));
}

static bool same_states(const u32 *a, const u32 *b)
{
	/* Only request/actual state nibbles, not PMGR sticky diagnostic flags. */
	return !((a[0] ^ b[0]) & 0xff) && !((a[1] ^ b[1]) & 0xff);
}

static void widgets(void __iomem *base, u32 *values)
{
	int i;
	/* Four exact USB-complex configuration offsets in the owner-local tree
	 * and native arbitrator. No guessed offset or register write.
	 */
	for (i = 0; i < 4; i++)
		values[i] = readl(base + 0x1c + i * 0x20);
}

static int status_get(char *buf, const struct kernel_param *unused)
{
	return scnprintf(buf, PAGE_SIZE,
		"result=%d\nobserved=%u\nrestored=%u\nconsumer_removed=%u\n"
		"suspend_result=%d\ndetach_result=%d\n"
		"phy_before=%08x\nphy_active=%08x\nphy_after=%08x\n"
		"host_before=%08x\nhost_active=%08x\nhost_after=%08x\n"
		"control=%08x\nconfig=%08x\n"
		"widget_1c=%08x,%08x,%08x\nwidget_3c=%08x,%08x,%08x\n"
		"widget_5c=%08x,%08x,%08x\nwidget_7c=%08x,%08x,%08x\n",
		result, observed, restored, consumer_removed, suspend_result,
		detach_result, before[0], active[0], after[0], before[1],
		active[1], after[1], control, config,
		widgets_before[0], widgets_active[0], widgets_after[0],
		widgets_before[1], widgets_active[1], widgets_after[1],
		widgets_before[2], widgets_active[2], widgets_after[2],
		widgets_before[3], widgets_active[3], widgets_after[3]);
}
static const struct kernel_param_ops ops = { .get = status_get };
module_param_cb(status, &ops, NULL, 0400);

static int __init observer_init(void)
{
	struct device_node *np = NULL, *parent = NULL, *host_np = NULL;
	struct of_phandle_args spec = { .args_count = 0 };
	struct platform_device *pdev = NULL;
	struct resource resource;
	u32 provider_reg[2], host_reg[2];
	void __iomem *phy = NULL, *host = NULL, *base = NULL, *complex = NULL;
	bool attached = false, pm_enabled = false, resumed = false;
	int ret, i;

	if (!of_machine_is_compatible("apple,j72") ||
	    strcmp(utsname()->version,
		"#33 SMP PREEMPT Sat Oct 31 11:57:21 +08 2026"))
		return -ENODEV;
	np = of_find_node_by_path(DOMAIN);
	host_np = of_find_node_by_path(HOST);
	if (!np || !host_np || !of_device_is_compatible(np, "apple,pmgr-pwrstate") ||
	    np->parent != host_np->parent ||
	    of_property_read_u32_array(np, "reg", provider_reg, 2) ||
	    of_property_read_u32_array(host_np, "reg", host_reg, 2) ||
	    provider_reg[0] != 0x20120 || provider_reg[1] != 4 ||
	    host_reg[0] != 0x20170 || host_reg[1] != 4 ||
	    of_address_to_resource(np->parent, 0, &resource) ||
	    resource.start != 0x20e000000ULL || resource_size(&resource) < 0x20174) {
		result = -ENODEV;
		goto out;
	}
	parent = of_parse_phandle(np, "power-domains", 0);
	if (parent != host_np) {
		result = -ENODEV;
		goto out;
	}
	phy = ioremap(PHY_STATE, 4);
	host = ioremap(HOST_STATE, 4);
	base = ioremap(PHY_BASE, 0x10);
	complex = ioremap(0x20c900000ULL, 0x80);
	if (!phy || !host || !base || !complex) {
		result = -ENOMEM;
		goto out;
	}
	widgets(complex, widgets_before);
	states(phy, host, before);
	if ((before[0] & 0xff) || (before[1] & 0xff)) {
		result = -EBUSY;
		goto out;
	}
	pdev = platform_device_register_simple("j72-hsic-phy-observer-v2", -1, NULL, 0);
	if (IS_ERR(pdev)) {
		result = PTR_ERR(pdev);
		pdev = NULL;
		goto out;
	}
	spec.np = np;
	ret = of_genpd_add_device(&spec, &pdev->dev);
	if (ret) {
		result = ret;
		goto cleanup;
	}
	attached = true;
	pm_runtime_enable(&pdev->dev);
	pm_enabled = true;
	ret = pm_runtime_resume_and_get(&pdev->dev);
	if (ret < 0) {
		result = ret;
		goto cleanup;
	}
	resumed = true;
	states(phy, host, active);
	widgets(complex, widgets_active);
	if (!domain_ready(active[0]) || !domain_ready(active[1])) {
		result = -EIO;
		goto cleanup;
	}
	/* Only the control/config offsets used by the exact native port driver.
	 * Do not sweep the unknown +4/+12 words or any operational EHCI state.
	 */
	control = readl(base);
	config = readl(base + 8);
	observed = true;
	result = 0;
cleanup:
	if (resumed) {
		suspend_result = pm_runtime_put_sync_suspend(&pdev->dev);
		if (suspend_result < 0) {
			if (!result)
				result = suspend_result;
			/* Keep the failed consumer attached, with no async retries.
			 * Do not discard a still-active domain owner on error.
			 */
			pm_runtime_disable(&pdev->dev);
			goto verify;
		}
	}
	if (pm_enabled)
		pm_runtime_disable(&pdev->dev);
	if (attached) {
		detach_result = pm_genpd_remove_device(&pdev->dev);
		if (detach_result) {
			/* Preserve a still-attached device if detaching fails. */
			if (!result)
				result = detach_result;
			goto verify;
		}
	}
	platform_device_unregister(pdev);
	pdev = NULL;
	consumer_removed = true;
verify:
	for (i = 0; i < 200; i++) {
		states(phy, host, after);
		if (same_states(before, after))
			break;
		usleep_range(500, 1000);
	}
	restored = same_states(before, after);
	widgets(complex, widgets_after);
	if (!restored && !result)
		result = -EIO;
out:
	pr_info("j72_hsic_phy_observer_v2: result=%d observed=%u restored=%u removed=%u\n",
		result, observed, restored, consumer_removed);
	if (base)
		iounmap(base);
	if (complex)
		iounmap(complex);
	if (host)
		iounmap(host);
	if (phy)
		iounmap(phy);
	of_node_put(parent);
	of_node_put(host_np);
	of_node_put(np);
	/* Keep diagnostic status available on hardware failure. No retry API. */
	return 0;
}
static void __exit observer_exit(void) { }
module_init(observer_init);
module_exit(observer_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("J72 HSIC1 read-only registers through existing genpd owner");
