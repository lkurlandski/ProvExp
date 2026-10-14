# Revision plan (2026-10-14)

Next steps from the self-review (`docs/review-2026-10-14.md`) after the user's feedback. Grouped by what each needs,
cheapest first. Decisions already made are at the bottom.

## A. Writing only, no experiments — DONE 2026-10-14 (commits ff29a9e, e0d45dd, 363fba1)

1. **Honest cost accounting** (review item 2 / W3). In 4.1, report each explainer's own time next to the extraction
   counts: TreeSHAP ~ms, Integrated Gradients ~ms on a GPU, KernelSHAP ~45 s/file. State the "1/135" ratio as holding
   for the extraction count, and note that KernelSHAP's own cost dominates for that explainer. Numbers exist in
   `docs/experiments/pb1.md`.
2. **Make the novelty case in Section 3** (item 5 / W1). Add, in "Constructing P" and around the pushforward
   definition: what instrumenting a *program* takes (the conventions for counts, hashes, strings, entropies, and why
   each is the right one); what the validation buys (exact for additive features, Section 4.1); and why the pushforward
   is a real step (moving attribution through a non-invertible program into features the model never computes;
   conservation; why the $D^\dagger$ normalization is needed, which 5.1 shows empirically). Keep it short; no theory we
   do not measure.
3. **Fix the "one place / second place" inconsistency** (item 12 / W9). Say once, in the experimental setting, that the
   experiments use format knowledge in three places (the deletion operator, the struct trigger, the audit's loader
   rules) and why; drop the running "second place" phrasing.
4. **CM threat-model wording** (item 13 / W9). Say in 4.3 that deletion measures where both detectors are jointly cheap
   to attack, not a working attack, so the section agrees with the discussion.
5. **Related-work contrast with parser-based saliency mapping** (item 15). One or two sentences: prior practice maps
   MalConv saliency onto PE regions with a hand-built parser (Coull & Gardner; Bose et al.), per format, summing bytes
   into regions; the pushforward splits shared bytes among features automatically for any extractor.
6. **Thin the numbers per sentence** (item 14 / W9). A light editing pass over 4.1, 4.3, and 5.3: one headline number
   per sentence, each with its reference point (random, occlusion, chance).

## B. Pilot experiments, no MalConv re-evaluation (do after A, at pilot scale)

7. **[DONE, run 56]** **PE-field-occlusion oracle baseline** (item 1 / W2, W4). Result: oracle gain 0.91 at 124 extractions/file; byte-level pullback beats it 88/100 (p~1e-15). In the manuscript (Table 1 + 4.1). Add one ranking to `scripts/faithfulness.py`: use a PE
   parser to list header fields and sections, occlude each, rank bytes by the resulting change. This is the natural
   upper bound for a direct, structure-aware explainer and answers "is the byte-level win just knowing the read set?"
   (the oracle knows it too). Replaces the paused adaptive-occlusion idea (HiPe exists but is a vision method; building
   it for PE is out of scope). Pilot scale, GBDT only.

8. *(moved to Deferred, item 12: a second extractor via Android APKs.)*

9. **[BUILT, running as run 57]** **Triage tied to a decision** (item 7 / W6, CM). Shared-reliance-evasion chosen; `cm_triage_evasion.py` smoke-tested; user running the pilot (200 files, GPU 1). Follow-up in `docs/experiments/cm.md`. Show the triage labels track *why* two detectors disagree. Take
   files with a *planted* MalConv header evasion (disagreement caused by an attack on MalConv) and files that are
   *organic* GBDT-only detections (a genuine GBDT blind spot). Prediction: planted evasions concentrate in **oppose**
   on the header (the attacker pushed header bytes to read benign to MalConv — evidence MalConv reads the other way);
   organic blind spots concentrate in **blind** (content the GBDT's features do not cover). If it holds, the label is a
   decision a defender can act on. Reuses the trigger/evasion machinery; no new data. Also scale the triage to 100
   files per cell and validate all four cells.

## C. Deferred: needs MalConv re-evaluation or retraining (mock tables stand in for now)

Mocks with predicted, clearly-fake tables are in `docs/experiments/mocks.md`.

10. **Pushforward faithfulness measured on MalConv** (M1, item 3 / W5). Delete the bytes $P$ assigns to MalConv's
    top pushed-forward features; compare with the surrogate mapped through $P$, IG over windows, and random. Cheap and
    closes the clearest methodological gap, but re-scores MalConv, so it waits until we re-enable that.
11. **The audit's mitigation** (M3, item 10 / W6). Zero the audited fields at test time (no retraining) and with
    retraining; measure clean-detection cost and the drop in evasion. The retrain half is for the cluster round; the
    test-time half needs no retraining.

12. **A second feature extractor: Android APKs** (item 6 / W7, user 2026-10-14). Collect an APK dataset from AndroZoo
    and instrument a Drebin-style extractor (manifest permissions, intents, API calls, strings) for $P$; run the 4.1
    faithfulness test, and ideally a pushforward check, on an Android feature-based model. This is the strongest
    evidence for "any feature extractor, any domain". The EMBER-subsetting idea (PE-structural vs. statistical) is
    scrapped (user). Manuscript write-up can begin now with synthetic (blue) placeholders.

## Dropped / paused

- **Header-attack comparison (old M2):** dropped. It re-evaluates MalConv, adds a query-based search loop, and the
  benefit does not justify the complexity or the explanation burden (user, 2026-10-14).
- **Adaptive / hierarchical occlusion (old item 1):** paused. Real prior art (HiPe, Cooper et al. 2022) but a vision
  method; building it for PE is out of scope. The PE-field oracle (B7) answers the same objection more simply.
- **Sandbox execution:** never, for this paper (user). See memory `no-sandbox-execution`.

## Decisions made 2026-10-14

- **MLP cut from the body** (done, commit `363fba1`); it returns in future work. The "a transfer is only as faithful as
  its source" point is now stated conceptually (the transfers are linear), not via the MLP.
- **Figure 1 cut; Figure 3 caption no longer claims a round trip** (commit `e0d45dd`).
- **Scale-up (runs 50-55):** recommend cancelling and returning to pilot work; the designs above change before a final
  scale-up. [awaiting the user]

## Trajectory: how the current work strengthens the manuscript (2026-10-14)

The self-review's biggest rejection risks were (W2/W4) the "byte resolution is out of reach / win is by construction"
objection, (W5) the pushforward never tested on MalConv, (W6) the two applications' security value, (W1) thin novelty,
and (W7) generality shown on one extractor. The session's trajectory attacks them in order of leverage:

- **W2/W4 — closed (run 56).** The field-occlusion oracle, a parser-based upper bound that knows the read set and
  costs 124 extractions/file, reaches only 0.91 and loses to the byte-level pullback on 88/100 files. The pullback's
  advantage is *resolution within a field*, not knowledge of which bytes a feature reads. This is now a positive result
  in Table 1 and 4.1, not a defended claim.
- **W6 (comparison) — in progress (run 57).** If the triage separates attack-caused from organic disagreements
  (oppose vs. blind), the blind/oppose/agree label becomes a defender's *decision*, which is what the review asked for.
  If it does not, we fall back to reframing the existing split as the decision — still an improvement over the current
  prose. Either way 4.3 gains an operational reading.
- **W5, W6 (audit), W1, W7 — staged with honesty.** The pushforward-on-MalConv test (M1), the mitigation (M3), and the
  Android second extractor are drafted in the manuscript as **synthetic (blue) placeholders** tied to concrete runs,
  so the paper already reads as the finished argument and each blue block names the experiment that replaces it. The
  novelty case (W1) is now made in Section 3 (instrumenting a program; the pushforward as the harder direction) rather
  than conceded. The MLP is cut so the body carries only load-bearing results.

Net: the two intrinsic faithfulness claims (pullback, pushforward) and the pullback's application are moving from
"asserted" to "demonstrated against the strongest baseline a practitioner would build"; the pushforward's application
and generality are staged with clearly-marked predictions until the deferred (MalConv-retraining / new-domain) runs.
The scale-up to 2,000 files / 3 seeds remains the last step before submission, after the designs settle.
