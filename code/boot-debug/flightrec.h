#ifndef J72_FLIGHTREC_H
#define J72_FLIGHTREC_H

#include <stdint.h>

#define J72_FLIGHTREC_PAGE_SIZE 16384U
#define J72_FLIGHTREC_HEADER_SIZE 256U
#define J72_FLIGHTREC_EVENT_SIZE 64U
#define J72_FLIGHTREC_CAPACITY 252U
#define J72_FLIGHTREC_VERSION 1U

struct j72_flightrec_event {
    uint8_t magic[8];
    uint16_t stage;
    uint16_t event;
    uint32_t sequence;
    uint32_t flags;
    uint32_t error;
    uint64_t counter;
    uint64_t current_el;
    uint64_t mpidr;
    uint64_t arg0;
    uint32_t crc32c;
    uint32_t reserved;
};

_Static_assert(sizeof(struct j72_flightrec_event) == J72_FLIGHTREC_EVENT_SIZE,
               "flight recorder event geometry differs");

enum j72_flightrec_stage {
    J72_STAGE_IOS_LAUNCHER_ENTER = 0x0100,
    J72_STAGE_IOS_HOOK_COMMITTED = 0x0120,
    J72_STAGE_WAKE_BRIDGE_ENTER = 0x0200,
    J72_STAGE_WAKE_CPU0_ACCEPTED = 0x0210,
    J72_STAGE_GATHER_ENTER = 0x0300,
    J72_STAGE_GATHER_VALIDATED = 0x0310,
    J72_STAGE_M1N1_ENTER = 0x0400,
    J72_STAGE_M1N1_ADT_ACCEPTED = 0x0410,
    J72_STAGE_HOOLOCK_ENTER = 0x0500,
    J72_STAGE_ANS_READY = 0x0510,
    J72_STAGE_STORAGE_READY = 0x0520,
    J72_STAGE_PAYLOAD_LOADED = 0x0540,
    J72_STAGE_KBOOT_ENTER = 0x0600,
    J72_STAGE_KBOOT_DT_PREPARED = 0x0610,
    J72_STAGE_KBOOT_PAYLOAD_READY = 0x0618,
    J72_STAGE_KBOOT_BRANCH = 0x0620,
    J72_STAGE_LINUX_ENTRY = 0x0700,
    J72_STAGE_LINUX_MMU_ON = 0x0710,
    J72_STAGE_INITRAMFS_INIT = 0x0800,
    J72_STAGE_ROOT_MOUNTED = 0x0820,
    J72_STAGE_SWITCH_ROOT = 0x0830,
    J72_STAGE_LINUX_USB_READY = 0x0910,
    J72_STAGE_BOOT_COMPLETE = 0x0920,
};

#endif
