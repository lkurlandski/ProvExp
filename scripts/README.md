# Scripts

Every experiment is run through a numbered script in `run/`, which names the script, its arguments, its log, and its
runtime; start there to reproduce a number. Grouped by what the current paper uses. Old names: C1 = exact side
effects (Proposition 1), C4 = sound directions (Theorem 1), Tables A0/A1/A2 = Tables 5/7 and the toolkit split.

## Data and models (shared)

featurize, check_features, refeaturize_nonpe, build_metadata, select_explanation_set (the pilot and explanation
sets), train_classic (GBDTs, monotone constraints from a direction table), train_erdalt (Gimenez et al.'s ERDALT),
make_fixtures (test files).

## The paper: the EMBER instance and evaluation (direction A)

- **Directions:** a_directions (the direction table per threat model; derived from the item tables by default,
  `--hand` for the hand rules; `--extractor sums` for the re-encoding over sums; `--loose` for R7's widening: the
  certificate and debug entries writable (`ent`) and their data allowed past the end), a_expert_directions (the same for
  Gimenez et al.'s 40 features).
- **Checks of the instrumentation and the catalogue:** item_checks (G1/G2 bit-exact readouts, G5, G6: single-byte
  flips and locating positions), catalogue_checks (G7: every operation applied by our own byte-level edits, checked
  against re-extraction and the derived directions; Tables 5 and 6, closure; `--loose`: the widened population with
  `ent` and escaped copies, runs 141-142), population_clauses (which clause of the
  population check each file fails: incomplete or unusual layout; §4.4, run 136), escape_audit (which single field
  writes outside the threat model take a file out of the population; R7, run 137), a_c1_table0 (the hand side-effect
  predictors, the engine's oracle).
- **Witnesses of the hand table's errors (Table 6):** a_overlay_witness, a_signature_witness, a_structure_witness
  (entry section, Rich header, exports and relocations past the end).
- **Attacks and baselines (Table 7):** a_pv_attacks (secml-malware attacks, PV selection), a_pv_hole, a_erdalt_hole,
  a_advtrain (attacked training malware: adversarial training and ERDALT's vectors; `--seed_per_file` for varied runs),
  a_coverage (§5.3: which lowerable features the toolkit's outputs and our own edits lowered, by source; run 132), a1_evaluate (toolkit columns; one held-out attack per fold for leave-one-out, run 131), a1_toolkit_split, a1_adaptive (the adaptive search: greedy and beam,
  scoring candidates by predicted side effects, or with `--score real` by extracting every candidate, nothing
  declined; `--escape` applies an escape write first, run 138), mab_attack (MAB-Malware, the authors' code in
  `third_party/mab_malware` run single-threaded with a direct hand-over to our detectors; run 139), a_expert_adaptive, a_price_list (per-operation cost of soundness).
- **The trial competitor (R18, run 144):** trial_probe (a stronger trial of the in-place operations and donor imports,
  our own writers), trial_table (the direction table learned by trial against the derived one, and the files to
  train a monotone detector on it).
- **From A' (dropped, two pieces used by the paper):** ap_check1_learned (learned constraints, run 110: Table 6's
  learned row), ap_containment (combined edits, run 111: Table 5's last row), with ap_check0_solver (Kantchelian's
  exact GBDT encoding) and ap_encoding underneath. The rest of `ap_*` is source material only.

Library code: the item layer `src/provexp/items.py`, the engines `src/provexp/reach.py`, the catalogue
`src/provexp/featuresets/ember2024/catalogue.py`, the re-encoding over sums `.../sums.py`, the expert set
`.../expert.py`.

## The old direction (explanation provenance, dropped 2026-10-22; kept as source material)

Explanations and census (explain, provenance_census, pullback_agreement, pilot_tables, theory_coverage,
provenance_cost, exact_pullback_check); CP (cp_tables, cp_coarsening, cp_blackbox); PB1 (discover_protected_fields,
header_typical_values, faithfulness, pb1_tables); the trigger (trigger_*); PF1 (pf1, pf1_resolution, pf_inverse,
pf_malconv); 3-A (cm_*); 3-C audit (audit_*); the old manuscript's figures (paper_figures); shared transplant machinery
(shortcuts, shortcuts_transplant). They stay in place because tests and old `run/` scripts load them by path.
Experiments dropped earlier are in `scripts/archive/`.
