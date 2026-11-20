#ifndef FB_ADDR
#error FB_ADDR is required
#endif
#ifndef COLOR
#error COLOR is required
#endif
#ifndef DISPLACED
#error DISPLACED is required
#endif

.section .text,"ax",%progbits
.global marker_start
marker_start:
    movz x9, #(FB_ADDR & 0xffff)
    movk x9, #((FB_ADDR >> 16) & 0xffff), lsl #16
    movk x9, #((FB_ADDR >> 32) & 0xffff), lsl #32
    movz w10, #(COLOR & 0xffff)
    movk w10, #((COLOR >> 16) & 0xffff), lsl #16
    movz x11, #24576              // 1536 pixels x 16 rows
1:
    str w10, [x9], #4
    subs x11, x11, #1
    b.ne 1b
    dsb sy
    .word DISPLACED
    .word 0                       // builder installs continuation B
