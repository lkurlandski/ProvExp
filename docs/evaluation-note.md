# §5 working note: what the section evaluates, and how it is organized (session 108, 2026-11-23)

Planning note for rebuilding §5 *Evaluation* from the ground up, as `docs/archive/instances-note.md` was for §4.
Archive it once §5's new structure is accepted. The current text (`manuscript/_f_evaluation.tex`) and decision 10
(`docs/decisions.md`: three findings, not a validation section, not a defense paper) are the baseline; this note
checks them against the paper's claims and the scale-up's experiments.

## 1. What §5 evaluates

The paper's claim, as §2 sets it up: a defender needs to know which way an attacker's edits can move each feature
(to constrain a detector, to define a feature-space threat model). Today that knowledge comes from **trial** (apply
edits, re-extract, look), from **reading the extractor** (an analyst's hand analysis), or from **observed attacks**
(learn from what attacks did). Each is limited: trial covers the edits it tries, reading is as complete as the reader,
observed attacks cover what those attacks did. Our framework **computes** it from the extractor's code (Theorem 1:
the derived table, sound for the whole threat model).

So §5 evaluates **the derived directions against the directions a practitioner would otherwise have**, on EMBER. The
yardstick is Corollary 1: give each source of knowledge the same use (a detector built on it) and the same attacks,
and see what happens. A source can fail in two ways, and each shows up as a measurable consequence:

| Failure | What it means | What it costs | Measured by |
|---|---|---|---|
| **Unsound** (misses a direction) | trusts a feature some edit can move the other way | the detector can be evaded | the attacks (any attack; the adaptive search aimed at what the detector trusts) |
| **Over-cautious** (constrains what no edit moves) | constrains or drops features the threat model cannot touch | detection lost for nothing | TPR at 1% and 0.1% FPR against the derived detector on the same features |

The derived table is sound (proven; checked in 5.1) and loose only where Theorem 1's per-operation, per-sum bound is
loose. Its detector's cost against the unconstrained detector is therefore **the price of soundness itself** for that
threat model, not one more competitor's failure: that is 5.4.

What §5 does *not* evaluate: Proposition 1 as a task (decided: the paper need not show every point of §2 in §5,
decisions 10 (c) and 12 (iii); at the scale-up the adaptive search scores candidates by extraction). Proposition 1
appears in §5 only as a check (5.1) and in the opener of 5.2 (how many features one edit moves).

## 2. Each source, what it gets wrong, and the experiment

| Source | Instances in §5 | Unsound? | Over-cautious? | Experiment (scale-up step) | Pilot evidence |
|---|---|---|---|---|---|
| Reading the extractor | our hand table | yes: 8 directions wrong (4 in the population) | no (agrees elsewhere; one feature left free) | `1-audit/hand-table`; hand detector attacked | adaptive lowers its score on 10/29, never crosses |
| | Gimenez et al.'s expert set | yes under *full*: 11 of 40 lowerable by rename / DOS stub | yes: 29.1% vs 92.2% TPR under *additions* | expert directions, `expert_adaptive`, MAB expert setting | adaptive 2/8, MAB 4/8 |
| | Severi et al.'s hashed features | no | yes: 1,430 of 1,558 movable under additions | none (count from the derived table) | — |
| Observed attacks | PV | yes: rename hole (124 lowerable features trusted, 38.8% of gain) | yes: 26.3% vs 87.2% (constrains the DLL flag, which nothing moves) | material (10,000 training malware, ~80k outputs), `learned`, all attacks | 4/9 adaptive, 7/9 MAB |
| | ERDALT | yes: constrains seen vectors, not directions (90% of its layer's weight on lowerable features) | (AUC .88) | same, ERDALT rescaled (session 100) | 24/29 by its own GAMMA imports with unseen donors |
| | adversarial training | no constraints: it learns the outputs | no | same | toolkit halved, adaptive unchanged (23/50 vs 25/49) |
| | iterated adversarial training (new) | learns the adaptive search's own outputs, `ent` held out | no | `4-detectors/iterated` (2 rounds) | none at pilot scale |
| | (leave-one-out folds) | PV holds on every held-out attack yet a rename evades it | — | folds in `learned`, held-out attack | PV 0 in all folds; ERDALT 25/29 on GAMMA imports |
| Trial (new in §5) | trial table from our own edits on the 2,000 evaluation files (favours the competitor) | yes: every evasion through a feature trial never saw move | no: less cautious than derived (87.6 vs 83.4% at 1%), resting on movable features | `3-directions/trial`, `train`, all attacks | beam 26/44, MAB 17/44; derived 0/39 |
| **Derived** (ours) | monotone features, monotone sums (full); monotone sums (additions) | no (0 evaded, largest score drop exactly 0; escapes; MAB's undeclared edits) | as tight as Theorem 1 allows | `train`, `price-list`, all attacks with escapes | 0/39, 0/40 |

Reading the table by rows gives the findings; reading the last column gives the evidence the scale-up replaces.

## 3. Proposed organization

**Lead** (done in session 108, to revise with the rest): the three sources; Corollary 1 as the yardstick; one
sentence per finding.

**5.1 Setup.** Detectors (training split, validation thresholds, which are monotone and why the tree check matters);
the evaluation set (1,000 + 1,000 complete test files); attacks (toolkit at GAMMA's budget, the adaptive search scored
by extraction, MAB-Malware; validity rule; the 4 MB output rule; "evaded" = by any attack); checking results (two or
three sentences, details in Appendix D). *Stale today:* 10% subsamples, 100 files, the threshold on the test files,
"computes each candidate's features by Proposition 1", 400 training malware and 3,183 outputs (that is 5.3's), MAB
settings.

**5.2 What reading the extractor misses** (today *What Hand Analysis Misses*). Unchanged in substance: one edit moves
~263 features; our hand table's eight errors and why (parser facts); what the error costs (hand detector); the expert
set (unsound under full); Severi et al. (over-cautious). The expert set's over-caution under additions (29.1% vs
92.2%) moves here from 5.4's *Against hand-picked features*, so both of the expert set's failures are in one place.

**5.3 What observation misses** (today *What Observed Attacks Miss*), two parts:
- *Observed attacks:* the material; what they reveal (lowered vs lowerable); PV (unsound: rename; over-cautious:
  DLL flag); ERDALT; adversarial training and iterated adversarial training; leave-one-out (one sentence, table in
  Appendix E).
- *Trial:* the strongest realistic alternative, run by the defender on the evaluation files themselves; evaded through
  features no tried edit moved; its clean-detection edge rests on those features.

Option: trial as its own subsection (5.4 *What Trial Misses*, cost becomes 5.5). For: §2 names three sources and
the lead follows them; trial is the competitor a reviewer will ask about first. Against: five subsections and a short
one (~300 words); trial and observed attacks share the mechanism (knowledge from edits someone tried), which is
cleaner to say once.

**5.4 What soundness costs** (today *What Robustness Costs*). The price (full threat model, features and sums, 1% and
0.1%); no attack evades; where the guarantee holds (population, escapes); where the cost lies (per operation, entry
write, reading the sums); the width of the threat model (additions; *shifts* if the price list has it); beyond the
guarantee (MAB's undeclared edits). The comparison with hand-picked features moves to 5.2.

## 4. Tables

Today: Table 3 (the hand table's eight errors), Table 4 (defenses learned from attacks), Table 5 (detectors for full
and additions). Under the frame of §1 the natural headline is **one comparison table**: a row per detector, grouped
by the source of its knowledge (none: unconstrained; reading: hand-table detector, expert set; observed attacks: PV,
ERDALT, adversarial training, iterated; trial; derived: features, sums, additions), with AUC, TPR at 1% and 0.1%, and
evaded by any attack. It shows both failure modes at a glance (low TPR = over-cautious; evaded = unsound). It
replaces Tables 4 and 5; Table 3 stays in 5.2. Risk: the threat model differs by row (the expert set and the
additions detector are additions-only); a column or a group label must say so.

## 5. Appendix

Appendix E (*Attacks and Defenses*) mirrors §5 (memory: appendix mirrors body):
- E.1 Setup: the toolkit (byte-level attacks and the MalConv control; GAMMA through our writers), the adaptive search,
  MAB-Malware (hand-over; Zainab et al.'s setting); per-attack table (today's Table 11/`tab:ember:per-attack`).
- E.2 Reading the extractor: the hand table's method if more than 5.2 holds (today nothing; maybe nothing needed).
- E.3 Observation: the material; PV's rule; ERDALT (our change, the rescaling); iterated adversarial training's
  rounds; the trial table's construction; leave-one-out table.
- E.4 Cost: the per-operation price list as a table (today only prose numbers in 5.4).
Appendix D keeps the checks (Table 9, side effects) and the re-encodings over sums; 5.1 and 5.4 cite them precisely
(D.2's Table 9; §4.1 and D.1 for the sums).

## 6. Decisions (Claude, at the user's request, session 108)

The user (session 108): too early to answer these; weigh them and decide. **More adversarial defenses will very likely
be benchmarked later**, in the body or an appendix (undecided), so the section must take new defenses without a
restructure. Each decision below is weighed against that.

1. **What §5 evaluates: kept, generalized from "direction tables" to "what a defense assumes edits can do".** Every
   feature-space defense rests on an assumption about $\mathcal{R}(z)$ (§2 already says so). PV and the hand table
   state it as directions; ERDALT and adversarial training hold it implicitly, in the vectors they learned from. Grouping
   defenses by **where that assumption comes from** (reading, observed attacks, trial, none) is what makes the section
   extensible: a new defense joins a group, or opens one (e.g., *none*: a generic region such as a norm ball, which
   assumes nothing about the extractor). The two failure modes apply to every defense: evaded (unsound assumption) or
   detection lost (over-cautious assumption). *Weighed:* a narrower statement (direction tables only) fits PV and the
   hand table but leaves adversarial training and most published defenses outside the frame.
2. **Trial stays in 5.3** (as the user decided in session 63: "§5's lead and §5.3 gain it"), and 5.3 becomes *What
   Observed Edits Miss*: knowledge from edits someone tried, whether an attacker's (observed attacks) or the
   defender's own (trial). Observed attacks first, trial last: even the defender's own trial of every operation, on
   the very files attacked, misses what it did not try. *Weighed:* a subsection of its own follows §2's three sources
   and the lead, but adds a short fifth subsection, and new learned defenses will land in 5.3 regardless; one
   mechanism, said once, keeps 5.3 the place that grows.
3. **The expert set's detection comparison moves from 5.4 to 5.2**, so both of its failures (lowerable under *full*,
   over-cautious under *additions*) are in one place and 5.4 is only about the derived detectors. 5.4 keeps one clause
   pointing back to it when it states the price. *Weighed:* session 36 placed it in 5.4 as "the result a practitioner
   can act on"; the unified table keeps it visible next to the price, so the move loses little.
4. **One comparison table replaces Tables 4 and 5**, a row per detector, grouped by the source of its assumption
   (none; reading; observed edits: attacks, then trial; derived), columns AUC, TPR at 1% and 0.1% FPR, evaded by any
   attack. This is the decisive choice for extensibility: a new defense is one row in its group. The additions-only
   rows (expert set, monotone sums under additions) carry the threat model in their names; inside/outside-additions
   evasions go to the prose (5.4's width) and Appendix E's per-attack table. Table 3 (the hand table's errors) stays
   in 5.2. Placement: **in 5.3**, where most of its rows are introduced; 5.2 and 5.4 cite it (a float lands near
   where it is first cited, so placing it in 5.1 would show rows before they are explained). Revisit once drafted.
5. **Appendix E mirrors §5** (E.1 Setup: the attacks, the training of every detector, the per-attack table; E.3
   observed edits: PV's rule, ERDALT's change, adversarial and iterated training, the trial table, leave-one-out; E.4
   cost: the per-operation price list as a table; no E.2 unless 5.2 needs one). **Rule for added defenses:** a row in
   the comparison table and per-attack table always; a paragraph in E.3 for how it was built and ported (CLAUDE.md:
   tabulate their setup against ours); body prose only if it shows a mechanism the existing rows do not (a new way an
   assumption fails), else one sentence in its group's paragraph.
6. **Shifts: deferred (user, session 108).** No *shifts* detector exists: the derivation computes the *shifts*
   table (`3-directions/derived`) and the adaptive search accepts `--threat_model M_shift`, but no detector is trained
   or attacked on it, and the running round has none. The user: incorporate it only if implemented and running;
   otherwise decide later whether it goes into the manuscript (agreed it seems useful: a middle point between
   additions and full, and what GAMMA's attacks need). Until then §5 does not mention *shifts* and §4 is unchanged.
7. **Title: *Evaluation* stays.** The lead states what is evaluated, and the subsection titles carry the findings
   (*What Hand Analysis Misses*, *What Observed Edits Miss*, *What Robustness Costs*). A descriptive title would have
   to name the frame before the reader has it.

**Drafting order:** 5.1 *Setup* (to the scale-up protocol), then 5.3 (new structure, trial, iterated training, the
comparison table), then 5.2 (expert set moved in), then 5.4, then Appendix E, then the lead revised against the
whole. Old numbers stay until the rerun is read; new results without a pilot number are written as prose with
`% SYNTHETIC`, and blue values only where a prediction is defensible (trial: the pilot's run 144).

**Session 109 (review):** 5.3's order is now: the material, what the attacks reveal, *PV's hole*, *What PV pays in
detection*, *ERDALT*, *Holding one attack out*, *Adversarial training* (with iterated), *Trial*. Heads name the defense,
so an added defense gets a head of its own. The lead names both failure modes and the derived table's predicting role.
