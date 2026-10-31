# Tested desktop source changes

`wvkbd-v0.20-j72.patch` applies to the public v0.20 source and provides the
keyboard integration used by the local build. `omarchy-keyboard` is the
measured Bash session controller; it expects that keyboard installed at
`/home/tablet/.local/bin/j72-wvkbd-auto`, a tablet runtime directory, and
Labwc input-method integration. It is not a system-wide installer.

`foot-1.28-touch-ime.patch` is the experimental short-tap IME activation
change used in the tested Foot build. It is based on the local Foot 1.28
source. Its separate contribution was not isolated from keyboard focus and
touch-worker fixes; do not attribute the whole keyboard result to it.

The owner confirmed repeated hide/tap/reopen/type in the combined desktop.
These changes belong in an eventual omarchy-a contribution, separate from
Orchard's hardware PR. See the included source licenses and `../NOTICE.md`.
