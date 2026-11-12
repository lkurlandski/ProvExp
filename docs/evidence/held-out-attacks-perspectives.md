# How to test defenses learned from attacks: perspectives discussed in session 33 (2026-11-11)

A record for restarting the analysis of §5.3 (*What Observed Attacks Miss*) from scratch. The user judged the session's
answers to be of low quality and asked for the perspectives discussed to be written down objectively, with their
strengths and weaknesses, rather than continued. Nothing below is decided. The section's text and the mock are the
authority on what §5.3 currently says (`manuscript/_f_evaluation.tex`, `docs/paper-mock.md` §5).

## The question §5.3 has to answer

Some published defenses decide what to trust from attacks they observe. **PV** (built in our code after the
perturbation-vector idea) keeps only the features no observed attack lowered, and constrains the GBDT's score to be
monotone in them, so that raising them never lowers the score; it drops every other feature. **ERDALT** (our port of
Gimenez et al.'s) trains a neural network on attacked samples with a monotone output layer. §5.3's claim, in the mock:
defenses learned from observed attacks inherit the gaps of those attacks; edits the threat model allows can lower
features the attacks never lowered, and the derived direction table names those features in advance.

The experimental question is how to measure that gap from a defender's point of view, with a methodology that is
not chosen in our favor. The user's standing objection (session 31): the original fixed split had no objective
grounding and "smells like bad science".

## Facts established so far

- **The attacks.** Eight toolkit attacks (secml-malware, Demetrio et al. and GAMMA): gamma_sections, gamma_api,
  gamma_shift, content_shift, dos_extend, header_fields, padding, format_exploit. Their stored outputs against the
  undefended GBDT: `artifacts/experiments/a_pv/deltas.parquet` (run 78; 36 population files each).
- **Run 131, PV leave-one-out (finished).** Held-out evasion of each fold's model by the attack it did not see:
  gamma_api 5/21; the other seven folds 0 (22-25 files each). Mean over folds about 3%. The fixed split's 18% came
  almost entirely from gamma_api being in its held-out group.
- **Run 131, ERDALT leave-one-out (partial, still running 2026-11-11 09:20; rerun by the user after a model-path bug
  was fixed this session).** gamma_api 21/24, gamma_shift 5/25, content_shift 1/28, gamma_sections 0/24,
  dos_extend 0/25; header_fields, padding, format_exploit and the beam search against ERDALT-8 still to come
  (`artifacts/logs/a1_eval-erdalt-loo-*.log`, then `artifacts/experiments/a_loo/summary.json` and
  `a_loo/erdalt-all8-adaptive/adaptive.json`). Every ERDALT model met its stopping criterion except the gamma_api
  fold (no epoch under 5 violations; kept epoch 181).
- **Run 131, finished 2026-11-11 (session 34).** ERDALT folds: gamma_api 21/24, header_fields 10/25, gamma_shift
  5/25, content_shift 1/28, format_exploit 1/23, gamma_sections, dos_extend, padding 0. ERDALT-8 adaptive 17/24.
  Session 34 found that all these vectors were made with the RNG reset to seed 0 before every attack run, so GAMMA's
  section names are the same on every file; see `docs/evidence/section-5.3-design.md`, which supersedes this record as the
  working plan.
- **Step 0 of run 131:** valid attacked training outputs gamma_api 399/400 (one LOST task), dos_extend 400,
  header_fields 400, format_exploit 387.
- **The adaptive search against PV built from all eight attacks:** 14 of 22 (runs 127/129).
- **Check C2 (this session):** the derived table (M_full under the precondition, quirk-fixed;
  `artifacts/experiments/a_directions_derived_v2/M_full-pre-quirkfixed.*`) lets edits lower 1,070 features (10 down
  only, 1,060 both ways; 1,295 up only, 203 fixed). Some toolkit output lowered 745 of them (70%), on the 36 files in
  the population. By group: byte histogram 256/256, byte entropy 256/256, strings 102/177, section-name buckets about
  80/200 (size 14/50, entropy 15/50, vsize 23/50, characteristics 27/50), Rich header 29/33, parser warnings 4/88,
  data directories 0/8, section entry 1/10, header 6/25, Authenticode 6/8. Outside the byte statistics: 233 of 558
  (42%). Each attack except header_fields lowers 600-680 lowerable features, mostly the same ones; header_fields 295.
  The mock's expectation ("a small minority") **failed**; Claude's stated expectation (60-70%) held.
- **Hypotheses tested:** the user's (PV's held-out evasion well above 0 because each attack lowers features the others
  don't) failed on PV; Claude's (the attacks lower nearly the same features, so PV mostly 0 outside gamma_api) held.

## The perspectives, with strengths and weaknesses

### 1. Fixed split: four attacks seen, four held out (runs 81/100/128)

- *Strengths:* cheap; one number per defense.
- *Weaknesses:* the split was chosen by us, and it held out the strongest attack (gamma_api), so the held-out number
  reflects that choice. No objective grounding. Rejected by the user in session 31.

### 2. Leave-one-out, reported as the mean over folds (run 131 as designed)

- *Strengths:* every attack is held out once; no split is chosen; standard in ML.
- *Weaknesses (user, this session):* the mean mostly measures how similar the attacks are to each other, a property of
  the toolkit rather than of the defense. A fold whose held-out attack resembles a seen one is easy by construction;
  six of the eight attacks change largely the same byte statistics, so most folds are trivially 0. The number does
  not represent a defender facing an unexpected attack.

### 3. Leave-one-out, reported as the worst fold

- *Strengths (user's proposal):* answers a defender's question ("what can a novel attack do?"); still no chosen split.
  Per-fold values can be reported alongside.
- *Weaknesses:* bounded by the most novel attack the toolkit happens to contain, so with a redundant toolkit it still
  understates what an attacker can do; a maximum over eight small cells (about 22 files each) is noisy; it can make
  the result hinge on one attack (gamma_api for both PV and, so far, ERDALT), which reads much like the fixed split
  it replaced.

### 4. Keep one, leave the rest out (learn from one attack, test on the other seven; an 8x8 matrix)

- *Strengths (user's alternative):* shows how far one attack's lessons carry; the full matrix shows the structure of
  the toolkit's overlap.
- *Weaknesses (Claude's view, not tested):* a defender with a single attack is unrealistic and may read as a straw
  man; like the mean, it largely measures attack similarity; eight models plus 56 attack runs.

### 5. MAB-Malware held out alone, against defenses learned from all eight toolkit attacks (Claude's proposal)

- *Strengths:* an independent published attack; its actions (from the literature notes, **not yet verified in
  `papers/song2022mab.pdf`**: section rename, certificate removal, debug removal, checksum break, slack append, overlay
  append, section add) plausibly lower structural features the toolkit leaves uncovered (C2: data directories 0/8,
  section-name buckets about 80/200). Zainab et al. (preprint) report MAB-Malware and GAMMA together account for nearly
  all evasions of the other attacks.
- *Weaknesses (user):* holding out one deliberately chosen attack is again a chosen split, the same flaw as
  perspective 1. Also: its code may not run against our models (unverified); a reimplementation over our catalogue
  would invite fidelity questions.

### 6. MAB-Malware as a ninth member of the pool, not held out specially

- *Strengths (user):* useful only if it manipulates different features; if it does, it strengthens whatever design is
  chosen without being singled out. A go/no-go check is possible before any run: from its action list and our
  catalogue, which features can it lower that no toolkit attack lowered?
- *Weaknesses:* integration cost (running their code, or porting); still needs a design from perspectives 2-4 or 7.

### 7. All subsets of the pool: evasion by unseen attacks as a function of how many attacks the defender has seen

For every subset of the attacks (510 with nine), the defense learns from the subset and every attack outside it is
run against it; results are grouped by the subset's size k, with the mean and the worst subset per k. Set against
two quantities that do not depend on the subset: the coverage gap (features edits can lower that the seen attacks
never lowered, from the derived table and the stored outputs) and adaptive evasion against the defense learned
from everything.

- *Strengths:* no chosen split at all; directly answers "if I collect more attacks, does my defense stop being
  evaded?"; the expected picture (unseen-attack evasion falls toward 0 while the coverage gap and the adaptive
  evasion stay high) would show the finding as a curve.
- *Weaknesses:* expensive. Measured evasion needs a model and an attack run per (subset, unseen attack) pair:
  thousands in full; a seeded sample of 8 subsets per k is about 64 PV models (about 2 h) and about 290 attack runs
  (on the order of 15-20 h at 16 workers); ERDALT (about 26 GPU minutes per model) cannot follow. A cheap stand-in
  (an unseen attack can lower PV's score on a file only if it lowers a feature PV keeps) is a necessary condition only,
  and uses outputs aimed at the undefended model, not at each subset's PV. More machinery than the paper's other
  experiments (memories `constrain-experiment-complexity`, `consistency-and-simplicity`). The design was proposed at
  the end of the session and not examined critically.

### 8. Split-free measurements that do not need held-out attacks

- **Coverage (C2):** the share of what edits can lower that the observed attacks lowered (70% overall, 42% outside
  the byte statistics). *Strengths:* objective, cheap, directly about the gap. *Weaknesses:* measures the attacks, not
  a defense; the 70% headline is not small, so the claim must rest on which features are uncovered, not on how many.
- **Adaptive evasion against the defense learned from all attacks** (PV-8: 14/22; ERDALT-8: pending). *Strengths:*
  the defender used everything available; no split. *Weaknesses:* it is our own attack, guided by the derived table,
  so it shows the gap is exploitable but not that an independent attacker would find it.

### 9. Option A, as phrased in this session

Make the near-zero held-out number part of the claim: observed attacks overlap, so testing a learned defense on
held-out observed attacks gives false confidence, while the adaptive search evades (PV-8: 14/22) through features C2
shows no attack lowered. The user agreed with the direction but asked for the experiment to be redesigned so it rests
on a defensible methodology; option B (an independent held-out source on its own) was rejected as perspective 5.

## What went wrong in the session (for the next one to avoid)

- Proposals were made faster than they were examined: the MAB-Malware hold-out repeated the flaw the user had just
  named, and the all-subsets design came with cost estimates but no critical look at whether it is needed.
- One answer contained an unfinished thought in the text ("I'd still report the old split's 18%? No: ...").
- The analysis started from the experiment rather than from §5.3 as a whole: what the section must show, what it shows
  now, and which measurement serves that best.

## Update, 2026-11-11 (session 34): leave-one-out redone the fair way

Run 131's folds learned from seed-0 vectors that included the pilot (test) malware's (`docs/evidence/section-5.3-design.md`,
§3, §10). Run 133 rebuilt the all-eight defenses from varied runs on training malware only; run 135 redoes the folds
from the same outputs (the user kept leave-one-out: "still a very powerful and interesting experiment"). Option A's
claim now has its fair test: the rebuilt PV is evaded by the search through rename, an operation none of the eight
attacks has (4/9); run 135 shows what holding one of the eight out reveals.
