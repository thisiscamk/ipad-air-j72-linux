#!/bin/bash
set -eu
wlr-randr --output Unknown-1 --scale 2 --transform normal
omarchy-keyboard run > "$XDG_RUNTIME_DIR/keyboard-start.log" 2>&1 &
qs -p /opt/omarchy-ipad/shell/shell.qml > "$XDG_RUNTIME_DIR/quickshell.log" 2>&1 &
foot -d info --title='J72 compressed desktop' /bin/bash --noprofile --norc > "$XDG_RUNTIME_DIR/foot.log" 2>&1 &
printf 'started\n' > "$XDG_RUNTIME_DIR/j72-shell-started"
