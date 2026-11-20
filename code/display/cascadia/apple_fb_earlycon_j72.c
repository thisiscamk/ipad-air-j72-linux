// SPDX-License-Identifier: GPL-2.0
/*
 * J72 framebuffer early console, derived from Project Cascadia's
 * devices/a13/kernel/extras/apple_fb_earlycon.c (commit ad28ba40).
 *
 * Draw printk text into the framebuffer left active by m1n1, beginning at
 * parse_early_param().  There is intentionally no UART access: no J72 UART
 * base or pin routing has yet been qualified.
 *
 * Use: earlycon=j72fb keep_bootcon console=tty0 ignore_loglevel loglevel=8
 * Needs CONFIG_FONTS + CONFIG_FONT_8x16.
 */
#include <linux/console.h>
#include <linux/font.h>
#include <linux/init.h>
#include <linux/io.h>
#include <linux/of.h>
#include <linux/platform_device.h>
#include <linux/serial_core.h>
#include <asm/early_ioremap.h>

#define FB_PHYS        0x83d200000UL
#define FB_STRIDE      0x1800
#define FB_WIDTH       1536
#define FB_HEIGHT      2048
#define TOP_ROW        0
#define BOTTOM_ROW     FB_HEIGHT
#define FONT_W         8
#define FONT_H         16
#define LINE_BYTES     (FONT_H * FB_STRIDE)
#define WHITE          0xffffffffU

static const struct font_desc *font;
static void __iomem *line_map;
static int line_mapped = -1;
static void __iomem *full_map;
static bool fb_on;
static int cols, rows, cx, cy;

static void map_line(int line)
{
	if (full_map || line == line_mapped)
		return;
	if (line_map)
		early_iounmap(line_map, LINE_BYTES);
	line_map = early_ioremap(FB_PHYS +
		(size_t)(TOP_ROW + line * FONT_H) * FB_STRIDE, LINE_BYTES);
	line_mapped = line_map ? line : -1;
}

static void __iomem *line_row(int y)
{
	if (full_map)
		return full_map +
			(size_t)(TOP_ROW + cy * FONT_H + y) * FB_STRIDE;
	return line_map ? line_map + (size_t)y * FB_STRIDE : NULL;
}

static void clear_line(void)
{
	int y;

	for (y = 0; y < FONT_H; y++) {
		void __iomem *row = line_row(y);

		if (row)
			memset_io(row, 0, FB_WIDTH * 4);
	}
}

static void newline(void)
{
	cx = 0;
	cy = (cy + 1) % rows;
	map_line(cy);
	clear_line();
}

static void glyph(unsigned char c)
{
	const u8 *g = (const u8 *)font->data + (size_t)c * FONT_H;
	int x, y;

	for (y = 0; y < FONT_H; y++) {
		void __iomem *row = line_row(y);

		if (!row)
			return;
		row += cx * FONT_W * 4;
		for (x = 0; x < FONT_W; x++)
			writel_relaxed((g[y] & (0x80 >> x)) ? WHITE : 0,
				       row + x * 4);
	}
}

static void j72fb_putc(struct uart_port *port, unsigned char c)
{
	if (!fb_on)
		return;
	if (c == '\n') {
		newline();
		return;
	}
	if (c == '\r') {
		cx = 0;
		return;
	}
	if (c < 0x20 || c > 0x7e)
		c = '?';
	if (cx >= cols)
		newline();
	glyph(c);
	cx++;
}

static void j72fb_write(struct console *con, const char *s, unsigned int n)
{
	struct earlycon_device *dev = con->data;

	uart_console_write(&dev->port, s, n, j72fb_putc);
	wmb();
}

static int __init j72fb_setup(struct earlycon_device *dev, const char *opt)
{
	font = &font_vga_8x16;
	cols = FB_WIDTH / FONT_W;
	rows = (BOTTOM_ROW - TOP_ROW) / FONT_H;
	cx = cy = 0;
	fb_on = true;
	map_line(0);
	clear_line();
	dev->con->write = j72fb_write;
	return 0;
}
EARLYCON_DECLARE(j72fb, j72fb_setup);

static void stop_screen(void)
{
	console_lock();
	fb_on = false;
	console_unlock();
}

static int bus_notify(struct notifier_block *nb, unsigned long action,
		      void *data)
{
	struct device *dev = data;

	if (action == BUS_NOTIFY_BIND_DRIVER && fb_on && dev->of_node &&
	    of_device_is_compatible(dev->of_node, "simple-framebuffer"))
		stop_screen();
	return NOTIFY_DONE;
}

static struct notifier_block j72fb_nb = {
	.notifier_call = bus_notify,
};

static int __init map_full(void)
{
	void __iomem *m;

	if (!fb_on)
		return 0;
	bus_register_notifier(&platform_bus_type, &j72fb_nb);
	m = ioremap_wc(FB_PHYS, (size_t)FB_STRIDE * FB_HEIGHT);
	if (!m)
		return 0;
	console_lock();
	full_map = m;
	if (line_map) {
		early_iounmap(line_map, LINE_BYTES);
		line_map = NULL;
		line_mapped = -1;
	}
	console_unlock();
	return 0;
}
core_initcall(map_full);

static int __init screen_handover(void)
{
	if (fb_on)
		stop_screen();
	return 0;
}
device_initcall_sync(screen_handover);
