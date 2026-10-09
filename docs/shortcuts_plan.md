# 3-B: Making a Feature-Based Detector's Reliance Legible in the Bytes

Started 2026-10-09. An extrinsic application (`PLAN.md`, "Paper structure"). Goal: an application of the pullback that
is impossible or much more expensive without it. Framing decided 2026-10-09.

## Claim

A feature-based detector's explanation lives in opaque features: hashed buckets and file-wide aggregates. Feature-space
SHAP says "bucket `imports:library_hash_254` matters" but not *what* it is; the value is a different library in every
file. **The pullback resolves each relied-upon feature's credit back onto the bytes that produced it, naming the
content in each file.** This is:
- **Impossible from feature-space SHAP**, which only names the bucket.
- **Much cheaper and finer than occlusion** (one instrumented extraction vs. hundreds of ablations per file, PB1), so
  it scales to a whole corpus, where recurring content stands out.

Done across the 2,000-file test set (run 22): the pullback turns the GBDT's reliance into a ranked, human-readable
inventory of the content behind its features.

## Evidence (run 22; `run/22_shortcuts.sh`)

Per file, the pullback of interventional TreeSHAP, the top-256 credited bytes in a direction, spans grouped by
content and top feature, ranked by files x mean credit. Clean (2,000/2,000, 1.6 min per direction on 32 workers);
454 benign-pushing and 473 malware-pushing patterns recur in >= 10 files.

- **The headline case:** `imports:library_hash_254` carries `python312.dll` in some files, `api-ms-win-core-registry-l1-1-0.dll`
  and `msi.dll` in others. SHAP sees one bucket; the pullback names the library per file. Same for section names
  behind hashed section features (`.reloc`, `.rsrc`) and imports behind `library_hash_*`.
- **Benign-pushing content:** `VCRUNTIME140.dll`, `Qt6Core.dll`, `GetCurrentThreadId`, `<Module>`.
- **Malware-pushing content (capabilities, a link to 3-C):** `CreateToolhelp32Snapshot`, `VirtualProtect`,
  `WININET.dll`, `urlmon.dll`, `FromBase64String`, `PowerShell`, `User-Agent`.
- Header/data-directory *values* also surface (entry point 0, ImageBase 0x10000000, the Delphi timestamp, certificate
  sizes), but SHAP already reads those, so they are not where the pullback adds the most.

**Baseline (no P):** feature-space SHAP, shown side by side -- it stops at the bucket id; the pullback supplies the
content. (Occlusion is the cost baseline from PB1, not re-run here.)

## Correctness spot-check: manipulating a named byte moves the model as predicted

A small, non-circular check that the bytes the pullback names are the ones the feature reads: change them through the
real bytes -> parser -> feature path and confirm the score moves. This is a *validity* check, not the headline, and it
applies only to features a few bytes can actually set.

- **Run 23** (`scripts/shortcuts_insert.py`, `run/23_shortcuts_insert.sh`): appending benign-pushing *string* patterns
  to 200 held-out malware did **not** move the GBDT (median drop +0.00 to -0.37, nothing flipped; random moved 0).
  Correct and expected: string features are file-wide aggregates (high ambiguity), so one appended occurrence barely
  changes them, and appended text is not a real import. Appending is the wrong lever for aggregate features.
- **Do next:** the lever that matches the feature -- set a header field (the feature *is* the field value: Delphi
  timestamp, SizeOfStackReserve, a debug-directory size), and add a real import with a PE editor (LIEF). Expect the
  named bytes to move the score; this confirms the pullback's localization. Parse-only verification (user); runtime
  functionality out of scope (no sandbox).

## Out of scope / decided against

- **Evasion / "shortcut" as the headline** (2026-10-09): the point is legibility of reliance, not finding exploits.
  The manipulation check stays a correctness spot-check, not an attack result. (`dont-reframe` applies: this was the
  user's call.)
- **Ambiguity as a filter** on which credit forms spans (user, 2026-10-09: forced).
- **Patching features** and training-set prevalence: possible later, not core.

## Open

- The set-field / import spot-check (above): a handful of patterns on the same 200 files.
- Reference for the explanations (TreeSHAP's background may bury rare content).
- Whether to scale discovery beyond 2,000 files (pullbacks are cheap; ask before a large run).
