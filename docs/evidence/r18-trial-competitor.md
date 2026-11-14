# R18: the trial competitor

Session 60 (2026-11-13, R18 track; `docs/resume-prompt-R18.md`). The review's point (C-W3, D-W6, B-W4 (e)): §5 never
builds the competitor a practitioner who knows the twelve operations would use, a systematic trial over them. This
note records what was built, what it showed, and what waits on the user. The run is `run/144_trial_competitor.sh`
(its header holds the numbers too); artifacts in `artifacts/experiments/r18_trial/`.

## Step 0: the mock

One row in Table 5 (detectors), *Trial*, with the same columns as the derived rows (AUC, TPR at 1% and 0.1% FPR,
evaded by any attack). Operator: the trial table (a feature is dropped if some edit lowered it, monotone increasing
if edits only raised it, free if no edit moved it), trained as the derived detector is. What moves: §5's lead
("Trial is exact but answers only for the edits it tries") and §5.3's closing claim (only the derived table shows,
before any attack, which trusted features an edit can lower). If trial is evaded through a feature it never moved, the
lead's contrast with trial gets measured evidence; if not, the contrast is reframed around the guarantee.

Hypothesis (session 58's, adopted): the trial table matches the derived one except ~50 string-pattern and Rich
features, never conflicts with it, and its detector is not evaded. **It failed** at the smoke (below).

## Step 1: the trial table

Strongest fair trial with our own writers (memory `own-edits-over-lief`): catalogue_checks' 2000-exact and
pilot-loose-lief edits (one draw each of random, printable or zero content per file; one slack region, the first
section's name) plus `scripts/trial_probe.py`: every section renamed, all slack, DOS and header bytes rewritten
(zeros, printable), and 20 donor import libraries per file from 200 benign training files (not the attack's pilot
donors). Population files only. Second variant `-toolkit`: plus the toolkit outputs (run 133 on training malware, run
78 on the pilot).

Modeled features (warnings apart), trial vs derived (`report-final.json`):

| derived → trial | features | what |
|---|---:|---|
| lowerable → lowered | 916 | |
| lowerable → never lowered | 66 | 62 string-pattern counts; iat_size, iat_virtual_address, import_virtual_address; authenticode:parse_error |
| raise-only → never moved | 86 | 84 import hash buckets (720 before donor imports), num_zero_size, SizeOfUninitializedData |
| fixed or raise-only → lowered | 0 | no soundness conflict |

- **Each wider trial witnesses more.** The stronger probe lowered six string counts the catalogue never did
  (`regex_debug` by renaming a section; `regex_certificate`, `internet`, `service` in slack; `window` in the DOS
  region) and four DOS-header fields. A count drops only on the rare file with a matching string in writable bytes, so
  trial's coverage grows with files and content and never says when it is complete.
- **The opposite question** (can any edit lower what trial never lowered?): for the string counts, yes on some files
  (above). `iat_size` and `iat_virtual_address`: the `imp` declaration lets an import adder move the IAT entry
  (`catalogue.py:409-411`); our writer keeps it, LIEF moved it (the toolkit outputs lower both). Parser warnings: the
  largest, "Suspicious flags set for section" (13.9% of the trial detector's gain), likely no operation removes (it
  needs an existing section's flags rewritten), so there the derived table over-approximates by its warnings rule
  (R12). Freeing the warnings as trial does costs the derived detector nothing measurable (83.0/66.2 vs 83.4/65.1).
- **The toolkit leaves the threat model.** With the toolkit outputs, 179 features are lowered that no operation lowers
  (GAMMA through LIEF relays out the file, assumption A4; some outputs stop being PE files: `general:is_pe` lowered).
  Trial cannot tell these from the operations' effects.

Detectors (pilot store, seed 0; TPR at 1% / 0.1% FPR): unconstrained 93.5 / 84.4; derived (`-loose`) 83.4 / 65.1;
**trial 87.6 / 71.3**; trial-toolkit 53.1 / 36.5. The trial detector puts 30.8% of its split gain on features the
derived table marks lowerable: 14.4% modeled (iat_size 4.6, regex_https:// 2.1, iat_virtual_address 1.8, ...), 16.4%
warnings.

## Step 2: the attack (smoke; the full run is run 144)

Real-scored beam, 100 candidates, 12 pilot malware: **trial evaded on 5 of the 11 it detects**, every time by one
`ent` edit, signature cloning (a signed donor's certificate appended, the security entry pointed at it). Audit
(`clone_audit`, scratch): the drop is carried by `strings:regex_https://` (−1.1 to −2.3 logit): the certificate's URLs
raise the count; trial never moved it (random content holds no URL) and left it free, and the model reads more https
URLs as benign. The derived detector drops the feature (content-writing edits move it both ways): 0 of 2, score
+0.01 to +0.05. Trial-toolkit: 0 of 3, but its score fell (min Δlogit −0.93), so it is not monotone under the edits
either. Fairness note: trial with benign-donor *append* content would have raised this count (the toolkit variant
does, and closes this hole); the run tests whether it opens others.

Reading for the user (not decided): the reviewers' competitor, given its strongest form with our own writers, matches
the derived table on 92% of the modeled lowerable features, detects about four points more, and falls to one edit
through a feature whose effect depends on content trial did not try. That is §5's lead measured: trial answers only
for the edits (and contents) it tries. The toolkit variant shows the other side: trial through published tools cannot
separate the operations from the tools' side effects and costs 30 points of detection.

## Step 3: iterated adversarial training (recommendation, not run)

Literature (`papers/`): Lucas et al. 2023 adversarially train raw-byte detectors against code transformations for one
epoch; training on some attacks raised robustness to others ("training with some types of attacks can increase
robustness to other types of attacks"). Tsingenopoulos et al. 2024 retrain for 15 iterations and reach 0% attack
success "under these adversarial capabilities", tested on held-out files, not held-out capabilities; they transform
the dynamic-analysis reports directly (feature space respecting problem-space constraints), since problem-space
retraining would take years.

Cost from stored runs: run 125 (generation 2.3 h for 1,200 toolkit tasks, retrain ~10 min), run 143's real scoring
(~0.6 s per candidate, ~20 min per file not evaded at 2,000 candidates). Two rounds of the real-scored beam on 400
training malware: ~5-7 h per round at 16 workers, plus retraining and the held-out evaluation: **~13-15 h at pilot
scale, one seed**; a few days at the scale-up (seeds 0-2).

Blocker: `a1_adaptive.py` (R7-owned) stores the operations and scores of a search, not the adversarial file or its
feature row, so it cannot feed retraining yet. Needed: an option to save the best candidate's feature row per (defense,
file), in the store's layout, as `a_advtrain.py`'s X.npy does. Not edited here.

Recommendation (Claude): in, at the scale-up, as one row of Table 4 (two rounds, the adaptive beam over all twelve
operations in the loop, training malware only), tested with MAB-Malware and with one operation held out of the loop.
Hold out `ent` (signature cloning): it is the operation that broke trial, the defender learns it only after an attacker
uses it, and it is the strongest benign signal. Expected: the retrained detector resists the beam it trained on and
falls to the held-out operation, which supports §5.3 with the defense the four reviewers expect. A pilot first (~15 h)
if the user wants the reading before committing the scale-up's compute.

## While run 144 ran (session 62)

**The six non-string disagreements, traced.** Per-operation signs of the precondition row (`-pre`, the variant the
detector uses; recomputed with a_directions' own functions on 24 pilot files, since `directions.csv` stores only the
strict variant per operation):

| feature | derived (-pre) | trial | reading |
|---|---|---|---|
| authenticode:parse_error | lowerable (rsg; ent and content writes) | never moved | derived right: set on 42 of 54,266 test files, none probed |
| num_zero_size, SizeOfUninitializedData | raise-only (sec, imp) | never moved | derived right: an added section without raw data; our writers never add one |
| iat_size (and import_size) | lowerable (imp only) | never moved | plausible: a recomputed inflated size, or the IAT entry pointed at the new thunks only |
| iat_virtual_address, import_virtual_address | lowerable (imp only) | never moved / raised | over-broad: the new table lies in a section added after the others, so both addresses only rise |

`catalogue.py:408-411` declares the four import/IAT entries `BOTH`. Run 145 measured what the two addresses' breadth
costs: the derived `-loose` detector retrained with them monotone increasing instead of dropped, 83.2 / 66.3 vs 83.4 /
65.1 (TPR at 1% / 0.1% FPR): nothing measurable (hypothesis: under one point; held). So trial's four-point edge rests
on features that are lowerable, not on an over-broad declaration. Narrowing the declaration to `UP` for the two
addresses is correct but changes no number; it is `catalogue.py` (R7-owned), so a proposal, not made.

**The `a1_adaptive.py` change adversarial training needs**, written and tested on a copy, not applied (R7-owned):
`docs/evidence/r18-a1_adaptive-save_rows.patch` (+28 lines). `--save_rows` (needs `--score real`) writes
`{outdir}/rows/{defense}/X.npy` (the best file's re-extracted row per detected file, the store's layout, 3,655
columns) and `files.parquet` (name, label 1, p_clean, p_adv, ops, evaded), the layout `train_classic.py --augment`
reads. Smoke (1 pilot file, 100 candidates, trial detector): the saved row scores 0.7614, the search's own result
(one `ent` edit). Training malware instead of the pilot needs no code: `--pilot_files` with a training-split file list
(columns name, label, `log_odds:gbdt`) and `--db .../tr`, which also makes the donors training goodware.

**The audit, ready**: `scripts/trial_audit.py` replays each evasion (the search is deterministic), takes the best file
and lists the features carrying the drop by `pred_contrib`, with trial's marking. On the smoke file it reproduces the
stored row exactly and names `strings:regex_https://` (0 -> 16, -1.53 logit, free in trial).

## Run 144: the attacks (session 63)

Detected / evaded, all pilot malware each detector detects (in brackets: files in the population):

| detector | beam, 2,000 candidates | MAB-Malware |
|---|---|---|
| trial | 44 / 26 (33 / 19) | 44 / 17 (32 / 12) |
| trial-toolkit | 20 / 13 (14 / 7) | 20 / 3 (13 / 1) |
| derived (`-loose`) | 39 / 0 (28 / 0) | 39 / 0 (27 / 0) |

Hypothesis against it: derived 0 with its score never falling (min Δlogit +0.00): **held**. Trial evaded on 40-60%,
nearly all by `ent`: **held** (59%; every evasion uses `ent`). Trial-toolkit evaded on a few: **failed** (13 of 20;
only 2 use `ent`). MAB-Malware few or none: **failed** for trial (17 of 44, each by one overlay append of a benign
section's content); held for trial-toolkit (3, two outside the population) and derived.

Audit (`scripts/trial_audit.py`, `--mab` for MAB-Malware; outputs in `artifacts/experiments/r18_trial/attacks/audit/`):
all 39 beam evasions replayed and every one reproduces the run (the four longest, 10-24 min each, replayed after the
user's go-ahead). All 20 MAB-Malware evasions reproduce from
the minimal files it kept. In every evasion the feature carrying the largest drop is one the trial table left
**free**, i.e. no edit trial tried ever moved it:

- trial, beam: `strings:regex_https://` leads 21 of 26 (0 -> 2 to 48: a cloned certificate's URLs), the rest import
  buckets (`import_hash_271`, `library_hash_109`), `regex_onlick`, and two parser warnings on files outside the
  population;
- trial, MAB-Malware: `regex_https://` leads 16 of 17 (0 -> 2), with `regex_download` and `regex_powershell`: the
  appended benign content holds URLs and those words, trial's random, printable and zero contents none;
- trial-toolkit, beam: import library buckets lead 11 of 13 (`library_hash_163`, `167`, `162`, `199`, `110`): the attack's
  donor libraries hash into buckets the 200 trial donors and the toolkit outputs never touched; parser warnings on
  the files outside the population (where trial-toolkit is not even monotone: "Invalid resources directory", marked
  raise-only, falls 1 -> 0).

The derived detector drops the string counts and the warnings and holds the import buckets monotone increasing, so
none of these moves can lower its score. Reading: each wider trial closes the holes it tried (the toolkit's benign
appends close `regex_https://`), and the attack finds the next one it did not try (import buckets). Trial answers
only for the edits and the contents it tries; the derived table answers for the threat model.

## Log

- 2026-11-13 (session 60): steps 0-3 above; run 144 scripted; scripts `trial_probe.py`, `trial_table.py` (176dbb8).
- 2026-11-14 (session 62): while run 144 ran: the six disagreements traced, run 145 (the import addresses' breadth
  costs nothing), the `--save_rows` patch (proposal), `scripts/trial_audit.py`.
- 2026-11-14 (session 63): run 144 read and audited (above); `trial_audit.py --mab`. Decisions (user): the reading
  (§5's lead and §5.3, text after the scale-up; trial's clean-detection edge stated with §5.4's cost); a trial row
  (own writers + derived) in Table 5 at the scale-up, trial-toolkit at pilot scale; iterated adversarial training in
  the scale-up as in step 3 (`ent` held out). `--save_rows` applied to `a1_adaptive.py` (39b9b49).
