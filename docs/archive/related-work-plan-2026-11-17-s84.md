# §6 Related Work: assessment and cut plan (session 83, 2026-11-17)

The assessment and plan the user approved in session 83 ("I approve all of these changes"), with the user's answers,
the source checks done since, and what went wrong when applying it. The manuscript is unchanged: every edit of
session 83 was discarded. `manuscript/_g_related_work.tex` is as committed in `d9fc35d`, 1,843 words; the target is
30-40% off, about 1,100-1,300 words.

## The user's guidance on the plan

- Contrast our contribution with other work **where necessary** (emphasis on necessary), not at the end of every
  paragraph.
- Repetition of other sections is less forgivable. Assume the reader has read the introduction and §2 carefully, but
  not necessarily the rest of the paper in detail.
- Split *Robust and monotone detectors* into smaller paragraphs.
- Little detail about individual papers, unless they are critical related work that we build on directly, or seminal.
  What matters is each work's novel contribution and how the works relate to each other, not specifics ("they got X%
  accuracy", "they used a foo-bar-biz-bat network").

## (a) The section's argument, and the order

Every line of work near ours needs to know what an attacker's edits do to the features, and gets that knowledge from
somewhere other than the extractor:
- problem-space attacks find it by trial (apply the edit, extract the features again);
- constraint-based feature-space attacks take it as input, written by an expert or learned from samples;
- adversarial training gets it by generating realizable examples, at great cost;
- monotone and verified detectors take each feature's direction from an analyst or from observed attacks;
- certified defenses avoid the question by bounding how *much* the attacker edits, not *what* an edit can do.

We compute it from the extractor. The order (attacks, constraints, defenses, certified defenses, neighbouring fields)
serves the argument: keep it.

Three problems cause the length:
1. **The difference from our work is stated five times**, once at the end of each paragraph. In *Robust and monotone
   detectors* it takes 256 words (the last six sentences). §2's paragraph on the four lines of work ("Across the four
   lines of work, the knowledge comes from trial, ...") already makes the same point with the same citations.
2. **Repetition of other sections.** *Incremental computation and provenance* repeats the credit §3.2 gives
   incremental view maintenance and §3.3 gives abstract interpretation (the rule of signs). Gimenez et al.'s ERDALT and
   PV details, and "On EMBER, the computed directions find lowerable features ...", are §5.3 *What Observed Attacks
   Miss*. (*Problem-space attacks* also overlaps §2, but see below: the user keeps it.)
3. ***Robust and monotone detectors* does three jobs**: adversarial training, monotone detectors, and Chen et al.'s
   verified classifiers.

## (b) Per paragraph

| Paragraph (words) | Job | Verdict |
|---|---|---|
| Problem-space attacks (160) | Attacks find side effects by trial; we compute them | **Keep as is (user, session 83)**: "it wasn't that long to begin with, it read smoothly, and it emphasized the correct ideas at an appropriate level." |
| Constraints over features (424) | Attacks take constraints as input; experts or samples supply them; we derive them | Keep, cut to ~280-300 (with Labaca-Castro et al. added) |
| Robust and monotone detectors (765) | Defenses need directions and get them by hand or from attacks | **Split** into *Adversarial training* (~150-170, with Tsingenopoulos et al. and Wang et al. if it fits) and *Monotone and verified detectors* (~230-250, with Chen et al. 2021) |
| Certified defenses (180) | Size-of-edit bounds vs. kind-of-edit bounds | Keep, ~150-165, with Calzavara et al. moved in from the last paragraph and Gibert et al. 2023 beside DRSM |
| Incremental computation and provenance (294) | Credit to databases and PL; their tools answer for one edit already made | Keep, cut to ~110: the credit is given in §3; only the difference remains |

## (c) The cuts, by place

Because *Problem-space attacks* stays, the other paragraphs must deliver the whole cut: about **-550 to -700 words
net**, to land at 1,150-1,300. Word counts below are per-sentence estimates.

**Constraints over features (target about -120 net, including about +25 for Labaca-Castro et al.)**
- "The restriction is written as constraints ..." and "The attack perturbs a vector as usual ..." (~45 words) merge
  into the opening sentence (~20). Saves ~25.
- Simonetto et al. (46): drop "two" and the four application domains. Saves ~15.
- FENCE becomes a clause of Simonetto et al.'s sentence ("..., as does Chernikova and Oprea's FENCE for
  network-traffic and malicious-domain classifiers"). Saves ~12.
- Kantchelian et al. (42): drop "in feature space", shorten the example. Saves ~10.
- Dyrmishi et al.: drop "who compare hardening against such attacks with hardening against realistic ones" (the next
  paragraph introduces that study). Saves ~10.
- Sheatsley et al.: **factual fix** (below), about the same length.
- Bostani et al. (44): to ~30. Saves ~14.
- Labaca-Castro et al. added beside Bostani et al. (+25).
- The close, "None of these derives ... A hand-written constraint ... We derive what these attacks take as input. For
  a sum-then-readout extractor ..." (~93 words), becomes **one** sentence of ~30-40. Keep pass 1's narrower claim
  ("derives the constraints from the extractor itself"). Saves ~55.

**Robust and monotone detectors, split in two (target about -330)**
- *Adversarial training*: merge "Constraints tell an attacker ..." and "A defender can use the same knowledge ..."
  (34) into one opening (saves ~15); Lucas et al. 2023 keeps its point (practical only on over 140 workers) and drops
  "from months to between one and ten days" (~15); Lucas et al. 2024 becomes a clause (~12); drop "A hardened detector
  resists the kinds of edits it was trained on." (~12); Tsingenopoulos et al. grows by ~20 (decision below).
- *Monotone and verified detectors*: principle plus Incer et al. (97) to ~75 (~22); Gimenez et al., from "They build
  robust detectors in two ways" through "They also compare with a simpler selection ..." (111), becomes one sentence:
  hand-picked features for the certified detector, ERDALT and PV learned from observed attacks (saves ~80; the reader
  loses ERDALT's linear layer, which §5.3 gives); Chen et al. (106) to ~65: Hidost's features become "features simple
  enough that a subtree edit's reach can be read off them" (~40); Chen et al. 2021 (cost-aware trees) added (+20).
- The synthesis, "The detectors of Incer et al., Gimenez et al., and Chen et al. rest on the same input ..." to the
  end (256), becomes ~55: the three limits (by hand; from attacks; a feature set chosen to be easy to analyze, which
  excludes EMBER's) and one sentence that we compute directions for any declared set of edits. "Incer et al. derive
  the directions by hand, Gimenez et al. ..." repeats each work's own sentence; the EMBER finding is §5.3. Saves ~200.

**Certified defenses (target about -5 net)**
- RS-Del/DRSM sentence (52) to ~32, one clause per mechanism; Gibert et al. 2023 shares DRSM's clause (+15).
- Drop "(RS-Del reaches a certified accuracy of 91% at 128 bytes)" (~15).
- "Ours bounds what an edit can do ..." (46) to ~30 (~15).
- Calzavara et al. moved in from the last paragraph (+30).

**Incremental computation and provenance (target about -180)**
- One sentence pointing to §3.2 and §3.3 for what we borrow replaces the first three sentences (~62 words).
- The 71-word sentence on self-adjusting computation and incremental parsing becomes ~40, keeping the one real
  difference: in a binary format a position can locate items anywhere in the file.
- The difference ("one edit already made" against "every edit a threat model allows") stays as one sentence.
- Provenance semirings go (user: yes; `green2007provenance` leaves the paper).

## (d) Additions (user: yes)

- **Chen et al. 2021, *Cost-Aware Robust Tree Ensembles*** (`papers/chen2021cost.pdf`, not in `main.bib`): attacker
  costs "are asymmetric across features and to the directions of changes", from domain knowledge, for tree ensembles.
  One clause beside Incer et al. Quote-check the body before writing.
- **Labaca-Castro et al. 2022** (`papers/labaca2022realizable.pdf`, arXiv 2102.06747v2, not in `main.bib`; check for a
  venue version): on EMBER, "for each feature, we compute the probability of the feature being modified as a result
  of the problem-space UAP attack", used to sample feature-space perturbations for adversarial training; "the
  statistical model assumes independence across features". Beside Bostani et al.
- **Wang et al. 2022, *Robust Learning against Relational Adversaries*** (`papers/wang2022robust.pdf`): only if it
  fits the present structure (user). Read it before deciding where.
- **Gibert et al. 2023** (`papers/gibert2023certified.pdf`, AISec 2023, not in `main.bib`): chunk-based
  (de)randomized smoothing certified against patch and append attacks; beside DRSM in *Certified defenses*; removes
  the `% TODO cite` there. (`papers/gibert2024assessing.pdf` is their packing study, `gibert2025assessing`; the IEEE
  Access 2024 paper is empirical and not needed.)

## (e) Decisions already made

1. Tsingenopoulos et al.: not a paragraph of its own (user). Two sentences at the end of *Adversarial training*, with
   the proposed wording (robustness defined as the probability that the strongest such adversary fails, estimated by
   training a new agent on held-out reports; the transformations and the dependencies among report entries are
   written by hand, which is what we compute). Experimental comparison: not now.
2. Gibert et al.: the right paper is now in `papers/` (above).
3. Šrndić and Laskov, FENCE, Sheatsley et al.: PDFs are in `papers/`.
4. Chen et al. 2021 and Labaca-Castro et al.: add.
5. Provenance semirings: drop.

## Source checks done in session 83 (facts, reusable)

- **FENCE** (`chernikova2022fence`): "identifies the family of features dependent on that feature, and modifies
  consistently all those features"; network traffic (CTU-13) and malicious domains (MADE). §6's wording holds.
- **Sheatsley et al.** (`sheatsley2021robustness`): §6's "learn constraints from data around a few features chosen by
  hand" is **not supported**. They learn constraints as k-CNF clauses (Valiant's PAC learning), and show "sound
  constraint theories reduce to memorization of the training data". Fix the sentence to say this.
- **Šrndić and Laskov** (`srndic2014practical`): they "run [the attack] in the feature space to completion before
  transforming" into a file, and "it is impossible to generate a file which exactly corresponds to the feature vector".
  So "Šrndić and Laskov's evasion of PDFrate worked this way" (apply-and-extract) in *Problem-space attacks* is
  inaccurate. The user keeps the paragraph; the smallest fix (drop the clause, start at "The toolkits now used ...")
  is **the user's decision**, not applied.
- **Dyrmishi et al.**: "analytical form, which typically requires the involvement of a domain expert"; "We identify
  immutability constraints based on the PE format description and structure given by Microsoft. We also extract
  feature dependency constraints from the original PE file examples". Holds.
- **Bostani et al.**: "Our learned realizable space is a subset of the actual realizable space due to the limitation
  of learning from finite data." Holds.
- **Simonetto et al.**: "generic constraint language", a grammar, linear and non-linear. Holds.

## What went wrong in session 83 (so the next session does not repeat it)

- *Problem-space attacks* was cut from 160 to ~85 words by deleting whatever §2 also says. The user: "one of the worst
  things I have ever seen you write." It lost the paper we build on, the reason (Pierazzi et al.'s condition) that
  makes the paragraph an argument, and the class restriction (so it overclaimed). The paragraph was short and read
  well; the plan's -80 there was a mistake.
- After that, *Constraints over features* got timid trims: -11 words net against a planned -140. The user: "-11 words
  is completely and utterly pointless." The plan's cuts were approved; apply them in full, by rewriting the paragraph
  so it reads well at the planned length, not by deleting sentences and not by nibbling.

## Tsingenopoulos et al.: the session-82 reading (moved here from the resume prompt)

- **Tsingenopoulos et al. (arXiv 2402.19027, `papers/tsingenopoulos2024train.pdf`), the closest work.** Read closely in
  session 82. In §6 one sentence (*Robust and monotone detectors*) says they harden a detector of dynamic-analysis
  reports with examples that an RL agent builds from a set of problem-space transformations the authors define, and
  claim a probabilistic guarantee. **Proposed, not applied (ask):** say instead that they define robustness as the
  probability the strongest such adversary fails, estimated by training a new agent on held-out reports. What the
  reading found: (a) Theorem 4.1 (p-robustness) is the definition (the optimal adversary's expected success is 1-p);
  no bound is computed, and the level is estimated by retraining an RL agent on held-out reports ("given sufficient
  horizon to converge"), so it is only as strong as that attack; (b) the capability set C is hand-written (Table 1:
  add and replace allowed, removal not, replacing APIs not) and dependencies among the 13 report categories are
  propagated by a hand-written sweep (Appendix A: rename an entry everywhere), checked by hand on "a handful" of
  traces: the side-effect computation our framework derives from the extractor; (c) the edits are applied to the
  JSON report, not to binaries (7 years against 45 hours; the binary level is a proof of concept on a modified
  `capemon`), so do not describe their examples as binaries; (d) they state our premise, "attackers must generate
  realistic adversarial binaries, defenders... merely have to generate feature spaces that correspond to realistic
  transformations", by hand and for one model; (e) their model reads the whole report: no sum-then-readout extractor;
  (f) results: attack success 73.8% to 0.0% on the binary task at budgets of 1K and 2K entry modifications, 26,200
  samples of three families, against gradient-based adversarial training near 72%. A reviewer may ask why a defender
  cannot write the realistic edits by hand; the answer is what we compute instead of write. Their method (a
  hand-written edit model and an RL attacker, then retraining) is the realistic competitor for the defender's task;
  whether to compare against it is a larger decision for the user, not for this session.
