#ifndef WDT_TICKS
#error WDT_TICKS is required
#endif
#ifndef DISPLACED
#error DISPLACED is required
#endif

// State-preserving J72 watchdog checkpoint. CPU setup has a valid stack.
.section .text,"ax",%progbits
.global marker_start
marker_start:
    stp x9, x10, [sp, #-16]!
    movz x9, #0x7000
    movk x9, #0x0e02, lsl #16
    movk x9, #0x2, lsl #32
    str wzr, [x9, #0x0c]
    movz w10, #(WDT_TICKS & 0xffff)
    movk w10, #((WDT_TICKS >> 16) & 0xffff), lsl #16
    str w10, [x9, #0x04]
    movz w10, #0x8000, lsl #16
    str w10, [x9, #0x00]
    movz w10, #4
    str w10, [x9, #0x0c]
    str wzr, [x9, #0x00]
    dsb sy
    ldp x9, x10, [sp], #16
    .word DISPLACED
    .word 0
