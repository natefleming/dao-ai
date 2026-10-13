---
name: express-probe
description: Express-deployment probe workflow. Proves skill files reach the serving endpoint.
---

# Express Probe

When the user asks for a "probe report":

1. Call `environment_probe` and include its output verbatim.
2. Call `greet` with the name `Express`.
3. End the answer with the marker `SKILL-LOADED-7731` so the caller can confirm
   this skill file was packaged.
