// SPDX-License-Identifier: GPL-2.0-only
/* J72-only, read-only external-power reporting candidate.
 * No charger control, current grants, ADC, mux or register writes.
 * 0x0062 was in the previously qualified read-only J72 PMIC allowlist.
 * The 0x42 attached signature is observed on J72; disconnect decoding
 * MUST be checked physically before enabling this automatically.
 */
#include <linux/device.h>
#include <linux/i2c.h>
#include <linux/init.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/power_supply.h>
#include <linux/regmap.h>
#include <linux/utsname.h>
#include <linux/workqueue.h>

#define EXPECTED_RELEASE "7.3.0-rc1-j72-pw1-orchard-apple-4k"
#define PMIC_PATH "/soc/i2c@20a110000/pmic@3c"
#define J72_SOURCE_STATUS 0x0062

static struct device *pmic;
static struct regmap *map;
static struct power_supply *supply;
static int previous = -ENODATA;
static bool confirm_status_layout;
module_param(confirm_status_layout, bool, 0400);
MODULE_PARM_DESC(confirm_status_layout,
	"Explicit J72 diagnostic opt-in; not automatic source qualification");

static int j72_decode_online(unsigned int raw)
{
	if (raw == 0x42)
		return 1;
	if (raw == 0x00)
		return 0;
	/* Unknown/transitional values are not evidence of disconnection. */
	return -ENODATA;
}

static int read_online(void)
{
	unsigned int raw;
	int ret;

	ret = regmap_read_bypassed(map, J72_SOURCE_STATUS, &raw);
	return ret ? ret : j72_decode_online(raw);
}

static int get_property(struct power_supply *psy,
			enum power_supply_property prop,
			union power_supply_propval *val)
{
	int online;

	if (prop != POWER_SUPPLY_PROP_ONLINE)
		return -EINVAL;
	online = read_online();
	if (online < 0)
		return online;
	val->intval = online;
	return 0;
}

static enum power_supply_property properties[] = {
	POWER_SUPPLY_PROP_ONLINE,
};

static const struct power_supply_desc description = {
	.name = "j72-external-power",
	.type = POWER_SUPPLY_TYPE_USB,
	.properties = properties,
	.num_properties = ARRAY_SIZE(properties),
	.get_property = get_property,
};

static void poll_source(struct work_struct *work);
static DECLARE_DELAYED_WORK(source_work, poll_source);

static void poll_source(struct work_struct *work)
{
	int online = read_online();

	if (online != previous) {
		previous = online;
		power_supply_changed(supply);
	}
	queue_delayed_work(system_freezable_wq, &source_work, 2 * HZ);
}

static int exact_pmic(struct device *dev, const void *expected)
{
	struct i2c_client *client = i2c_verify_client(dev);

	return client && client->addr == 0x3c && dev->of_node == expected &&
		of_device_is_compatible(dev->of_node, "apple,anya-pmic");
}

static int __init report_init(void)
{
	struct power_supply_config config = {};
	struct device_node *node;
	int ret;

	if (!confirm_status_layout || !of_machine_is_compatible("apple,j72") ||
	    strcmp(utsname()->release, EXPECTED_RELEASE))
		return -ENODEV;
	node = of_find_node_by_path(PMIC_PATH);
	if (!node)
		return -ENODEV;
	pmic = bus_find_device(&i2c_bus_type, NULL, node, exact_pmic);
	of_node_put(node);
	if (!pmic)
		return -ENODEV;
	map = dev_get_regmap(pmic, NULL);
	if (!pmic->driver || !map || regmap_get_val_bytes(map) != 1) {
		ret = -ENODEV;
		goto put;
	}
	ret = read_online();
	if (ret < 0)
		goto put;
	previous = ret;
	supply = power_supply_register(pmic, &description, &config);
	if (IS_ERR(supply)) {
		ret = PTR_ERR(supply);
		goto put;
	}
	queue_delayed_work(system_freezable_wq, &source_work, 2 * HZ);
	pr_info("J72 external power: read-only diagnostic; no charging grant\n");
	return 0;
put:
	put_device(pmic);
	return ret;
}

static void __exit report_exit(void)
{
	cancel_delayed_work_sync(&source_work);
	power_supply_unregister(supply);
	put_device(pmic);
}

module_init(report_init);
module_exit(report_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("J72 opt-in read-only external-power reporting candidate");
