# 3-B: Finding (and Mitigating) Spurious Correlations with the Pullback

Started 2026-10-09. An extrinsic application (`PLAN.md`, "Paper structure"). Goal: an application of the pullback that
is impossible or much more expensive without it.

## Claim

A feature-based detector can learn **spurious correlations** -- reliance on content that tracks the label in the
training data but has nothing to do with maliciousness (compiler/packaging artifacts, trivially forgeable metadata).
Shortcut learning is a recognized ML-for-security problem (Arp et al., "Dos and Don'ts"). Finding them in a detector
over an opaque feature set is hard: feature-space SHAP says `imports:library_hash_254` is influential but not *what*
it is (a different library in every file), so you cannot judge whether the reliance is spurious or act on it.

**The pullback surfaces spurious correlations and makes them actionable:** it resolves each influential feature's
credit back onto the content that produced it, across a corpus, so recurring artifacts stand out; then P tells you
which bytes/features to manipulate to confirm or remove the dependence. This is **not** PB1 (per-file faithfulness of
the transfer) and **not** SHAP (which cannot name content or tell spurious from meaningful in an opaque feature). It
is **much cheaper than occlusion** (one extraction vs. hundreds per file, PB1), so it runs corpus-wide.

Not every relied-upon pattern is spurious, and "spurious" is a judgement about the domain (allowed in experiments,
`CLAUDE.md`); the test is whether the content is semantically irrelevant to maliciousness yet the model depends on it,
and whether an attacker can set it. The strongest cases here are forgeable metadata (a code-signing certificate, a
compiler's timestamp), where "signed -> benign" is the textbook malware shortcut.

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

## Confirming the correlation is causal and exploitable (set the bytes, watch the model move)

A surfaced pattern is a *candidate* spurious correlation. To show the model actually depends on it -- and that an
attacker can exploit it -- set the content, in held-out malware, through the real bytes -> parser -> feature path, and
measure the move toward benign. The lever must match the feature.

- **Run 24** (`scripts/shortcuts_setfield.py`, `run/24_shortcuts_setfield.sh`): forgeable **header-field artifacts**
  set to their benign-associated value in 200 held-out malware, vs. a random value of the same width. 197 scored,
  0.5 min. The **Delphi TimeDateStamp** (a compiler artifact, no bearing on maliciousness) moves the GBDT toward
  benign by +0.416 vs. +0.115 for a random value -- the specific forged value, ~3.6x the control. **DEBUG.Size 0x54**
  +0.691 vs. +0.552 (mostly from the field's presence, not its exact value). These are spurious correlations the
  detector learned, surfaced by the pullback from an opaque feature set and confirmed causal and attacker-settable.
- **Run 23** (`scripts/shortcuts_insert.py`, `run/23_shortcuts_insert.sh`): appending benign-pushing *string* content
  did **not** move the GBDT (+0.00 to -0.37, nothing flipped). Correct and informative: string features are file-wide
  aggregates (high ambiguity), so a few appended bytes cannot set them -- that reliance, even if spurious, is not
  exploitable by byte insertion. The contrast with run 24 is the point: the pullback plus P tells you which spurious
  reliance is byte-settable (forgeable metadata) and which is not (aggregates).

Parse-only verification (user); runtime functionality out of scope (no sandbox). Import-via-LIEF not run (new
dependency; the metadata cases already make the point).

## Mitigation (the "possibly mitigate" half; bridges to 3-C)

Once a spurious correlation is named, P says which features carry it, so it can be removed -- drop/neutralize those
features (via the pushforward's per-feature share, 3-C) or retrain with the artifact randomized -- and the fix checked
by re-running the set-bytes test and clean accuracy. Scoped but not yet built; decide with the user whether it lands
in 3-B or 3-C.

## Out of scope / decided against

- **Legibility-of-reliance as the headline** (rejected 2026-10-09): that is subsumed by PB1 (per-file faithfulness of
  the transfer). 3-B's contribution is finding *spurious* correlations and showing they are causal/exploitable, which
  PB1 does not do.
- **Ambiguity as a filter** on which credit forms spans (user, 2026-10-09: forced).

## Open

- The set-field / import spot-check (above): a handful of patterns on the same 200 files.
- Reference for the explanations (TreeSHAP's background may bury rare content).
- Whether to scale discovery beyond 2,000 files (pullbacks are cheap; ask before a large run).
