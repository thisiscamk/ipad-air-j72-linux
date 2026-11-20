#ifndef WDT_TICKS
#error WDT_TICKS is required
#endif
#ifndef DISPLACED
#error DISPLACED is required
#endif

// J72 /arm-io/wdt chip watchdog. The 24 MHz contract and register sequence
// match PongoOS lowlevel.c. Every later checkpoint restarts the counter.
.section .text,"ax",%progbits
.global marker_start
marker_start:
    movz x9, #0x7000
    movk x9, #0x0e02, lsl #16
    movk x9, #0x2, lsl #32       // 0x20e027000
    str wzr, [x9, #0x0c]         // disable chip watchdog
    movz w10, #(WDT_TICKS & 0xffff)
    movk w10, #((WDT_TICKS >> 16) & 0xffff), lsl #16
    str w10, [x9, #0x04]         // reset deadline
    movz w10, #0x8000, lsl #16
    str w10, [x9, #0x00]
    movz w10, #4
    str w10, [x9, #0x0c]         // enable
    str wzr, [x9, #0x00]         // restart counter
    dsb sy
    .word DISPLACED
    .word 0                       // builder installs continuation B
