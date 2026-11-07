// SPDX-License-Identifier: GPL-2.0-only
#include <linux/module.h>
#include <linux/of.h>
#include <linux/utsname.h>
#include "audio-blob.h"
static bool confirm_transport_only;
module_param(confirm_transport_only,bool,0400);
static int overlay_id;
static int __init start(void) {
 struct device_node *n;
 if(!confirm_transport_only||!of_machine_is_compatible("apple,j72")||strcmp(utsname()->release,"7.3.0-rc1-j72-pw1-orchard-apple-4k"))return -EPERM;
 n=of_find_node_by_path("/soc/sio@20ae00000");
 if(n){of_node_put(n);return -EBUSY;}
 return of_overlay_fdt_apply(j72_sio_fdt,sizeof(j72_sio_fdt),&overlay_id,NULL);
}
static void __exit stop(void) {int ret=of_overlay_remove(&overlay_id);if(ret)pr_err("J72 SIO overlay remove:%d\n",ret);}
module_init(start);module_exit(stop);MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("J72 transient experimental audio card for muted enumeration only");
