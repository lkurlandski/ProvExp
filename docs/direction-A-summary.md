# Direction A at pilot scale: where it stands (2026-10-26)

A one-page assessment of direction A (monotone detectors whose feature directions come from the extractor) against
the targets in `docs/direction-A-mock.md` and the falsifiable outcomes in `docs/direction-A-A1-design.md`. Numbers are
pilot scale: a 10% subsample of every split, seed 0, the 50 pilot malware, threat model M_full, 1% FPR. Tables:
`docs/direction-A-A1-design.md` ("Result: Table A1", "Result: Table A2"); C1 validation: `docs/direction-A-threat-model.md` S6.

## Bottom line

Every go/no-go check and every falsifiable outcome passed, most by a wide margin. The sound detectors are never moved
by any attack (toolkit, held-out, or adaptive; the largest score change is exactly 0.0), keep 87-89% TPR at 1% FPR,
and still detect 40-41 of the 50 pilot malware after every attack. PV selection, built from four or from all eight
toolkit attacks, holds against those attacks but falls to the C1-guided adaptive search on 21-22 of the 22 files it
detects, and costs ~35 TPR points. Direction A's core claim stands at pilot scale. What is missing is mostly rows the
mock planned (baselines) and breadth (a second toolkit, leave-one-out, scale), not evidence for the claim.

**Update (2026-10-29): the C4 rows now use derived directions and are routed.** Retrained from the directions the
engine derives (runs 99-100), the C4 models keep their accuracy (M_full slightly better: 88.1% / 89.9% TPR at 1% FPR).
As precondition-row detectors (files that pass the check get the C4 model, the rest the unconstrained one), the M_full
rows are evaded by no toolkit attack on the 38/50 pilot malware that pass the check (0/28, 0/30 held-out); on the 12
failing files one header-field evasion, through the unconstrained branch. Every class-1 disagreement between the hand
rules and the extractor now has a witness (runs 98, 101), and the derived directions cover all of them. Details:
`docs/direction-A-A1-design.md`, "Re-run with derived directions".

## Checks and outcomes

| Check / outcome | Criterion | Result | Verdict |
|---|---|---|---|
| 1. C1 holds (Table A0) | exact on >= 95% of pefile-written pairs, mismatches explained | append 89/89 A2-applicable, DOS overwrite 100/100; add-section's declared delta exact, rest A4 | pass |
| 2. PV has a hole the GBDT uses | hole >= 5% of PV-GBDT gain | 37.8% (full PV), 44.4% (PV-seen, s10) | pass |
| 3. Soundness does not cost the detector | C4-on-sums within ~2 AUC of PV | 0.993 vs 0.954 (PV-seen), 0.944 (PV-all): better, not worse | pass |
| Separation | adaptive(PV) >> adaptive(C4) = 0 | 21/22 and 22/22 vs 0 on all four C4 rows | pass |
| Soundness | no C4 row moved by an edit in M | min score change exactly 0.0 (toolkit: 0 evasions once non-PE outputs are excluded) | pass |
| Accuracy | C4-on-sums within a few TPR points of PV | 88.6% vs 56.2% / 53.8% | pass |

## Mock vs. measured

| | Mock | Measured |
|---|---|---|
| PV, seen attacks: AUC / TPR / adaptive evasion | 93.8 / 71 / 38% | 95.4 / 56.2 / 95% |
| C4 on sums: AUC / TPR / features kept | 95.5 / 80 / 1,900 | 99.3 / 88.6 / 2,191 |
| C4 on features: AUC / TPR / features kept | 91.0 / 63 / 380 | 99.2 / 86.7 / 1,508 |
| Unconstrained: AUC / TPR | 97.5 / 88 | 99.6 / 93.5 |
| Adaptive attack on PV: queries / extractions / bytes | 400 / 1 / 4 KB | 24-42 / 3-4.5 / 5-12 KB |

The mock was pessimistic about soundness's cost (the sound detectors are within 5-7 TPR points of unconstrained, not
the predicted 8-25) and about the adaptive attack (it breaks PV almost completely, not 38%). The sums re-encoding gains
~2 TPR points over the features as they are (88.6 vs 86.7 at 1% FPR), smaller than the mock's 17, because the
features-as-is row lost far less than predicted.

## What the results do not yet cover

In rough order of how much a reviewer would miss them:

1. **The expert-set baseline** (Gimenez et al.'s 40 hand-picked features; Incer-style). Without it, a reviewer can
   ask whether automation matters: "a hand-picked monotone set is also sound." The argument is accuracy (the mock
   expects ~86 AUC / ~52 TPR) and transferability; it needs the row. Needs the 40-feature list from Gimenez et al.
   (arXiv 2508.10038; not in `papers/`), mapped onto thrember v3's feature names; then one GBDT on the 10% store.
2. **The adversarial-training baseline** (and/or Labaca-Castro et al.'s hardening): the empirical alternative a
   practitioner would actually try. Needs adversarial examples from the toolkit (a run/ script, user-run).
3. **Held-out attacks from a second toolkit.** "Held-out" is currently a split of secml-malware's eight attacks. The
   mock planned MAB-Malware and Labaca-Castro et al.'s actions. Their in-M actions overlap our edit catalogue; a
   second toolkit makes the held-out column independent of the PV-building toolkit.
4. **Leave-one-out PV** (eight PV models), the formal version of the seen/held-out split (decided 2026-10-24).
5. **Scale:** seeds 0-2, full splits, more malware. PV detects only 22 pilot files, so its rates rest on small counts
   (21/22 is not borderline, but 4/22 held-out is).
6. **The cost column** ("cost to derive"): ours is one pass over the instrumented extractor; PV needs the attack runs
   (run 78). Both are in logs; only the bookkeeping is missing.

Not needed for the claim, parked: the Rich-header (DOS stub) C1 predictor (27% of PV's hole; the separation is
already complete without it); an import-adding predictor for the adaptive search (GAMMA API beats our search on the
unconstrained model, 24/47 vs 14/47 — context, not a claim); the A4 (declared vs. real) gap as its own analysis
(reported per row already: real re-extraction evades PV 19-20/22).

## Harsh notes

- **"PV was never meant to resist unseen attacks."** Gimenez et al. evaluate PV only on the attacks it was derived
  from, and a reviewer may call the adaptive result expected. Our answer is that the hole is *computed* (check 2) and
  *realized cheaply* (3-4.5 extractions per file), and that adding attacks does not close it (PV-all: 0/22 on all eight
  toolkit attacks, 22/22 adaptive). The paper should say plainly that the PV result confirms a known risk and
  quantifies it.
- **The adaptive attacker is white-box** (it aims names at the defense's highest-gain buckets). That is the standard
  strongest setting for a defense evaluation; the random-name ablation (11/22 and 15/22 on PV) shows a weaker
  attacker gets far too.
- **The guarantee route is not ours** (Gimenez et al., Incer et al.). Ours is deriving the perturbation set from the
  extractor, soundly and automatically, and the sums re-encoding. The expert-set row (item 1) is what makes this
  visible in the table.

## Recommendation

Direction A is a go at pilot scale. Before moving to the second application, add the two cheap pieces that change how
a reviewer reads Table A1: the expert-set row (item 1: get the paper's list and map it, then one ~2-min GBDT) and the cost column (item 6, bookkeeping). The
adversarial-training baseline, the second toolkit, leave-one-out, and scale are larger and can come with the
scale-up, on the user's decision.

**Flip side noted (2026-10-26):** the same machinery may give a second application, A' — realizing feature-space
attacks in the problem space (including hashed features, by inverting the hash for the bucket and sign wanted). Table
A2's search is half of it. Recorded in `PLAN.md` (Directions, A'); to be screened next to B and C.
