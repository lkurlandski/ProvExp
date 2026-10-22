# Graveyard: ideas that did not pan out, and why

Abandoned directions and the reason each failed, so we do not rediscover them. The full working documents for the
larger items are in git history (removed from the tree to reduce clutter); the commit that removed each is noted.
Code and run scripts for the dropped experiments live under `scripts/archive/` and `run/archive/` with their
artifacts still in `artifacts/experiments/`.

## Dropped directions

### Explanation provenance for explainable ML (dropped 2026-10-22)

**Idea.** Instrument the feature extractor once into a provenance matrix P and transfer explanations between the
feature space and the bytes (pullback b = Pa, pushforward a = P^T D^+ b); evaluate faithfulness, then one security
application per direction (comparing a GBDT and MalConv file by file; auditing MalConv in EMBER's vocabulary).

**Why it failed.** Built method first, with applications found afterwards (four failed attempts before the two that
survived). The technical core (data-flow bookkeeping, G-DeepSHAP's propagation, a Shapley grounding that equals the
uniform recording on EMBER) was judged too small, the faithfulness results unsurprising (white-box structure beats
black-box window explainers), and the security outcomes weak or already known (header reliance of MalConv; a 12.4%
field attack beside the paper's own 81% stub attack; a predicted drop a defender could simulate). Structural reason:
where flat P is precise (named header fields) it is not needed; where it would be needed (hashed and aggregate
features) it is diffuse. The user judged the draft a strong reject (2026-10-22). Manuscript, plan
(`docs/archive/PLAN-explanation-provenance-2026-10-21.md`), and the 2026-10-21 simulated review (`REVIEW-2026-10-21.md`)
remain as source material.

## Dropped experiments (within the old direction)

### 3-B — Spurious correlations via the pullback (dropped 2026-10-12)

**Idea.** Pull each file's GBDT explanation back to its bytes, group the top spans by content across a corpus, and
surface recurring, forgeable artifacts the detector keys on (shortcut learning; Arp et al., "Dos and Don'ts"). Confirm
them with a causal transplant, then mitigate by neutralizing the named features.

**Why it failed.** The pipeline worked end to end (discovery, confirmation, mitigation; 3.6% of detected malware
evaded at 1% FPR, removed by neutralizing 6 features at no accuracy cost), but it did not demonstrate the pullback's
value. The confirmed shortcuts sat on *named* features (`datadirectories:security_size`, `debug_size`) that
feature-space SHAP plus the feature names surfaces directly; the one finding only the pullback could make (`.rsrc` in a
hashed feature) carried 7% of the evasions. P's distinctive operation — summing credit across features onto shared
bytes — rarely changed anything here (83% of the top-byte credit came through spans dominated by a single feature).
The task simply did not need what is distinctive about P on a feature set with readable names.

**Lessons** (now the screening criteria in `PLAN.md`, "Paper structure", 3): check that an application needs what only
P gives *before* building it, on existing data; name the realistic alternative (here, SHAP + feature names), not a
strawman (a byte 4-gram miner); do not pile work on an untested premise or read confirmed-shortcut intermediate
results as progress on the claim. Full doc: `docs/archive/shortcuts_plan.md` before commit (see history).

### Rule-based 3-C — Rule matches pushed forward into a learned detector (on hold 2026-10-12, dead 2026-10-13)

**Idea.** Run a rule set (YARA, as in PEberus) alongside the GBDT; treat a rule's string matches as a problem-space
explanation and ask, per rule, whether the GBDT is redundant with it or complementary, split by whether the matched
bytes reach the features (representation gap) and whether the GBDT relies on them (reliance gap).

**Why it failed the sniff test.** As built, every column rested on the pullback and on Pᵀ, not on the pushforward
ψ = PᵀD⁺b — the operator whose application it was supposed to demonstrate. The "reliance" column was the pullback's
mass on the matched bytes, the "representation" column was Pᵀ1_S, and the deletion check used no P at all. The
go/no-go's hypothesis also failed where it mattered (agreement came from generic API rules; anti-debug rules, the
interesting case, showed a reliance gap of only 0.15). Superseded by the pushforward audit (see `docs/experiments/audit.md`),
which uses the pushforward essentially. Full doc: `docs/rules_plan.md` before commit (see history).

### The pushforward-as-shortcut-forging framing (no-go 2026-10-13, within the audit)

The audit's first framing pushed MalConv's IG forward to find benign-associated content, then *forged* it into malware
to move MalConv toward benign. No candidate was confirmed. A diagnostic (`run/42`) showed why: MalConv's per-byte
credit is real and specific in the file it explains, but does not **transfer** to another file, because MalConv keeps
only the strongest convolution window per channel and a field's contribution depends on its context and offset within
that window. The forgeable-shortcut premise does not fit MalConv. The fix (approved by the user) was to flip to
*destroying* malware evidence in place — scrambling the bytes P names — which needs no transfer and became the working
audit. Recorded in `docs/experiments/audit.md`.

## Directions the user has generally found unproductive

Not hard bans — raise them if there is a concrete reason — but each has been considered and set aside, so bring a
justification rather than assuming it is welcome. **Updated 2026-10-22:** under the new direction, PE specifics are
allowed where they serve a malware-generic argument, and the pushforward is no longer required (both directions are a
plus, not a rule); the other items still apply.

- **Analyses built on PE-format structure** (headers, sections, overlay, packers, "attacker-controllable regions").
  The framework is domain-agnostic and depends only on P; questions about controlling an *arbitrary* byte set, posed
  in terms of P, are welcome, but format-structure stratifications have repeatedly not led anywhere.
- **Coverage, localizability, and the null element's share as contributions.** They measure one explanation of one
  file by one explainer, not P; a large unattributable share reflects a limitation of the provenance pipeline, not a
  finding. App-L stays as a stated limitation only.
- **Packing as motivation or a case study.** Well-explored in the literature; not a fresh angle.
- **Dropping the pushforward's application / keeping it intrinsic-only.** The pullback alone is close to G-DeepSHAP;
  the symmetry between the two spaces is the paper's novelty, so the pushforward needs its own extrinsic application
  (now the audit).

## Superseded planning documents

- `docs/archive/plan_phase2.md`, `docs/archive/pilot.md`: the old "Phase 2" plan and pilot census, with the retired
  experiment IDs E1–E4 and A1–A3. Superseded by `PLAN.md`'s intrinsic/extrinsic structure. In history.
