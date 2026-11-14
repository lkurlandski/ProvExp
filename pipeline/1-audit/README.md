# 1-audit: the extractor's checks

What the instrumented extractor claims, checked against re-extraction on real files. The scale-up's audit pass (with
the deviations table of Appendix D) comes first: it is the only stage that can change the feature store.

- `item-checks/`: the item layer reads out every feature bit for bit; single-byte flips and locating positions;
  random in-place writes. Paper: Appendix D, Table 9; §5.1's counts.
- `catalogue-checks/`: every operation of the threat model, applied by our own byte-level edits with ordinary and
  adversarial parameters: the features move only in the derived directions (sound), the edited file stays in the
  population (closed), the declared changes are exact. Needs `3-directions/derived`. Paper: §4.4, §5.1, Table 9.
  Output: `1-audit/catalogue/` (`edits.parquet`, `report.json`).
- `population/`: which clause of the population check each file fails. Paper: §4.4, §5.4.
- `deviations/`: which of our deviations from EMBER v3, and which parser heuristics we leave as they are, apply to
  each file, in the population and outside it. Paper: Appendix D's deviations table (proposed, session 65).
- `escapes/`: which single field writes outside the threat model take a file out of the population. Paper: §5.4.
- `hand-table/`: the hand-written side-effect predictors against re-extraction, and the files that show each of their
  errors (overlay, signature, structure). Paper: §5.2, Table 3.

Order at the scale-up (one file list, `FILES`, for every step): `population/`, then `escapes/` and `deviations/`; `3-directions/derived`
(the loose table) before `catalogue-checks/` (which also runs the chained edits); `hand-table/` last (its counts read
the population and the catalogue's edits); `item-checks/` at any point.
