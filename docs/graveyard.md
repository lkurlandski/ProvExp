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
(`docs/archive/PLAN-explanation-provenance-2026-10-21.md`), and the 2026-10-21 simulated review (`docs/reviews/explanation-provenance/2026-10-21-ccs.md`)
remain as source material.

### A': realizable worst-case evaluation of a detector (dropped 2026-11-02; two pieces folded into A)

**Idea.** Prove a detector's worst case under realistic file edits (appending, added sections) with an exact solver
over the attacker's edit choices (Kantchelian et al.'s GBDT encoding), every feature computed from those choices
through provenance, including how one edit moves many features together (claims C2-C3). Per file, a bracket: a proven
floor on the lowest reachable score beside the best real attack. Budget-only and learned regions (constraints learned
from attack outputs) as the practitioner's alternatives. Working documents: `docs/direction-A-prime-plan.md` (the
adopted plan and every result, Sections 9-13), `docs/direction-A-prime-mock.md` (checks 0-2, 1b, decision 7), and
`docs/literature-Aprime-2026-10-27.md`.

**Why it failed.** Sound throughout, but it certifies only where the edits barely touch the detector or the budget is
tiny. Appending on PV certifies every covered file, but PV was built from padding attacks, so that is close to
circular. Elsewhere the certified budget per file never exceeds 4 KB (run 116: undefended model, append 10/13 at 1 KB,
2/13 at 4 KB, 0 at 16-32 KB; sections and PV similar or worse), below the 5-12 KB our own adaptive search needs to
evade PV, and far below what attackers append. The cause is the relaxation, not the solver: the byte-entropy windows
add a block per KB, and the bound is far too loose above a few KB (LP floor -10.8 at 64 KB against a threshold of
1.10). Many files cannot take an added section at all (no free section-table slot). Writing the solver's evasions as
files (check 2) failed earlier (0 of 6 realized). Structural reason: direction A already builds detectors these edits
cannot move (score change exactly 0), so certifying a fragile detector up to a few KB answers a question a reviewer
would not ask ("why not use the sound detector?"). The adversarially trained rows were never built.

**What survives.** (1) The region's soundness: every real edit lands inside it (run 111, 1,105 of 1,105 edits on 85
pilot files, re-checked on every solver change), direct evidence that the computed region captures how one edit moves
many features together; folded into A. (2) The contrast with learned constraints: learned from all toolkit attacks they
are too loose to certify anything on PV, and learned from PV's own attacks they certify by construction (run 110);
one sentence in A. Code kept in place (`scripts/ap_encoding.py`, `scripts/ap_bracket.py`, `scripts/ap_containment.py`,
the HiGHS path via `highspy`, tests); runs 109-116 and their artifacts under `artifacts/experiments/ap_*`.

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
