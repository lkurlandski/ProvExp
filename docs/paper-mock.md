# Paper mock (2026-11-02)

At most two pages. It decides what the paper contains; everything not listed here stays in `docs/formalization.md`
or out. "Measured" means a pilot-scale number exists; final numbers need the scale-up (user's decision).

## Thesis

For the feature extractors security classifiers use (find pieces of the input, add up what each contributes, apply a
formula per feature), the feature-space consequences of an attacker's edits can be *computed* from the instrumented
extractor: exactly for one edit, soundly for a whole threat model. Pierazzi et al. call this infeasible and observe it
by re-extraction; others write it by hand or learn it from attacks. The computed answer is correct, more correct than
hand analysis, more complete than learned constraints, and useful: it yields detectors no in-model edit can evade.

## Contributions

1. A model of sum-then-readout extractors (items, sums, readouts) and the requirements under which an edit's side
   effects are exact and a threat model's feature directions are sound, with proofs. Format-free; the format enters
   only for edits stated in raw elements.
2. An instrumented EMBER extractor (2,480 of 2,568 features modeled) and a second instance in traffic (CTU-13 botnet
   features), checked against re-extraction.
3. Derived directions and constraints that correct hand analysis on EMBER and replace 360 hand-written constraints on
   CTU-13.
4. Monotone detectors built from the derived directions that no in-model attack moves, at a small accuracy cost,
   where attack-derived feature selection (Gimenez et al.'s PV) falls to an adaptive attacker.

## Outline and word budget (body about 9,500 words, CCS format)

| Section | Content | Words |
|---|---|---|
| 1 Introduction | the gap, the three ways people cross it today, our claim, results | 1,000 |
| 2 Background | Pierazzi et al.'s problem space and side effects; who needs which view of the reachable set (attacks, monotone detectors, verified training) | 800 |
| 3 Framework | below | 2,500 |
| 4 Instances | EMBER (what is recorded, the three repairs, the import-overwrite patch); CTU-13 features; the edit catalogues | 1,000 |
| 5 Evaluation | Tables 1-4 | 3,000 |
| 6 Related work | incremental view maintenance and parsing, abstract interpretation, provenance, constrained attacks, robust detectors | 700 |
| 7 Discussion | what does not fit (global analyses, learned features, time decay), honest tools, cost of instrumenting | 500 |
| Appendix | proofs; lemmas on hashed keys, patterns, single inputs; requirement checks; EMBER caveats | — |

**Framework (2,500 words):** the problem and notation, Pierazzi's symbols (300); items, sums, readouts, the term and
readout tables, a cross-domain table (PE, APK, traffic) (700); edits and item deltas, edit classes (300); the recipe,
the five requirements as one compact list, Theorem 1 (side effects) (600); sign envelopes, the per-readout rules,
Theorem 2 (directions) (500); robustness as a corollary of Gimenez et al. (100). One running PE example (append a
URL), one traffic example where it adds something (the longest gap after an injection). Dropped from the paper:
projection onto the old provenance matrix, tightness, a cost theorem (cost is a table column), coupling (unless the
Severi row below is adopted).

## Tables and figures

**Figure 1.** An edit becomes an item delta, adjusted sums, and new features, against re-extraction (one PE example).

**Table 1: the computation is correct** (Theorem 1 vs re-extraction).
Rows: domain x operation. Columns: edits, exact, flagged by the engine, wrong.
- EMBER, measured: append, DOS overwrite, add section, every catalogue operation (73,063 edits on 2,000 files);
  combined edits 1,105/1,105. Wrong: 0.
- CTU-13, missing: insert connections (per port, TCP/UDP, any packet and byte counts). Expected: exact on all,
  trivially, since every feature is a total, minimum, or maximum.

**Table 2: more correct than hand analysis, more complete than learned constraints** (Theorem 2).
- EMBER, measured: derived direction table vs the former hand rules; every disagreement is the hand rules' error,
  witnessed by a real file and edit. Columns: features compared, agree, hand rule wrong (witnessed), derived wrong (0).
- CTU-13, missing: derived constraints vs Simonetto et al.'s 360 (326 linear, 34 non-linear). Columns: hand
  constraints implied by ours, hand constraints violated by a real insertion (a witness), constraints of ours absent
  from theirs.
- Learned constraints (from attack outputs), measured on EMBER (run 110): too loose to certify, or certify only on
  the attacks they were learned from. One row.

**Table 3: useful: detectors** (Theorem 3; the measured Table A1).
Rows: unconstrained; PV-seen; PV-all; expert set (Gimenez et al.'s 40 features); adversarial training (missing);
monotone on derived directions (over sums; over features as they are). Columns: AUC, TPR at 1% FPR, evasion under
the toolkit, under held-out attacks (second toolkit: missing), under the adaptive search, smallest score change, cost
to derive (bookkeeping: missing). Measured at pilot scale: the monotone rows 88-89% TPR, 0 evasions, smallest score
change exactly 0.0; PV falls to the adaptive search on 21-22/22; expert set AUC 0.844.

**Table 4 (candidate): the same on CTU-13.** A monotone botnet detector on the derived directions against FENCE and
MoEvA2. MoEvA2 evades Simonetto et al.'s constraint-augmented model 80% of the time; hypothesis: 0% on ours for
in-model insertions, at a few points of AUC. Adopt it if Table 1's CTU-13 row passes.

## What is missing, in order

1. **CTU-13 instance.** Rebuild Chernikova and Oprea's 756 features from the CTU-13 captures (Zeek connection logs,
   per host, port, and minute), record them as items and sums, run Tables 1 and 2. *Go/no-go:* the rebuilt features
   match the published vectors on at least 99% of entries, and every hand constraint is either implied by the derived
   ones or violated by a witnessed real insertion. A start, in order: check what the MoEvA2 package ships (raw
   pipeline or only vectors).
2. **A's gaps:** adversarial-training row, a second toolkit (MAB-Malware) for the held-out column, the cost column,
   scale (seeds 0-2, full splits, more malware).
3. **Framework section in `.tex`**, from `docs/formalization.md`, to its 2,500 words; it can be drafted now.

## Open decisions (user)

- **Drebin.** A third instance, as a head-to-head with Pierazzi et al. on side effects of code transplantation.
  Costs an AndroZoo key and an old reimplementation; its directions are near-trivial. Default: Section 2/3 example
  only, an instance if CTU-13 goes quickly.
- **Coupling row** (which of Severi et al.'s hand-excluded features can in fact move separately). Default: out.
