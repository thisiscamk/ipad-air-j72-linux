# Native N1 firmware converter candidate

This source-only follow-up applies after the experimental native J72 CLI work
in [../orchard-j72-cli](../orchard-j72-cli). It adds the versioned
`z2fw-from-z2-packet@2` recipe step. The default J72 recipe still has
`outputs = []`; it does not automatically supply an unqualified touch driver.

The existing Z2FW container carries mode/timing configuration, the observed zero
proximity initialization, a dynamic calibration reference and the unchanged
model firmware packet. Existing native N1 code owns controller startup and
register calibration. Per-unit calibration is supplied at boot, not embedded.

37 targeted tests and private byte comparisons pass. A replay of the four new
methods in the integrated CLI checkout also passes. **The new native touch
combination has not been tested on the iPad.**

No Apple firmware, unit calibration, captured device tree or private log is
included. Generate firmware locally from the documented official input and
keep it private. Read the patch's bring-up document for exact format and gates.
