# Research workspace orchestration — revision 2

This revision adds `--touch-resync35`, the matching observer and capture before
provider shutdown. These host references expect the existing private workspace,
module/source manifests, exact-boot Wi-Fi control and source/read-only receipts.
They are not a turnkey installer or portable charging utility. No private input
or raw device log is included. The original first-attempt references remain in
`../workspace-reference/`; the original tested driver is also archived here.

The updated session checks its separate `session-preparation-v2.json` source
receipt. Use `--preflight --touch-resync35` before the changed boot's test, then
`--run --touch-resync35 --readcheck ...` with its fresh native receipt. The staged
touch candidate must pass its self-check and owner input verification first.
The original zero-layout/SPI/timeout health rules remain in place.

On failure, normal charging stop and independent baseline precede normal desktop/
input stop and state-0/4 ring export. No worker reset, input restart, forced
unload or kernel export bypass exists. Failed APIs remain failed in the receipt.
The original observation failure remains an abort even if export succeeds.
Raw reports stay private. Synthetic report types in tests are not diagnoses
of the actual three rejected reports.

Only after the driver exits does `ensure-j72-ios-charging.py --run
--voltage-resume35` proceed. Start it after the session driver is alive; it waits
for all its test owners, handles missing USB without assuming Linux, and requires
actual iOS charging/full-on-external-power evidence. Unlock may be needed.

[Host-source receipt](PREPARATION-V2.json). The original power module/limits,
kernel, cold payload, firmware and private inputs are preserved. This combined
input/power trial is device untested and is not an isolated power-policy A/B test.
