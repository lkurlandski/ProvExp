# Parked directions: B and C

Set aside on 2026-10-27, when A' was chosen as the second application. Neither failed: no experiment was run on
either, and both remain candidates if the paper or a later paper needs a second application. Read this only when
considering a new application. Literature for both: `docs/literature-2026-10-22.md` (sections "Direction B" and
"Direction C"). Any revival goes through the usual screening first: the gap only feature provenance makes cheap, a
realistic competitor, a mock of the paper table, and a falsifiable go/no-go check (CLAUDE.md, framework conventions).

## B. Auditing raw-byte detectors for backdoors and shortcuts in feature vocabulary

No trigger-identification defense for raw-byte models was found (RAMP shows the attack; PBP purifies; Jigsaw and
generic defenses). Competitor: Perasso et al.'s region overlay. B only has an edge for triggers in shared or hashed
content. Variant: locating a feature-space trigger's bytes in poisoned training files.
**Why parked:** the edge is narrow, and the work tends to drift toward legibility ("explain in the problem space"),
which the user does not count as an application.

## C. Diagnosing evasion through disagreement between heterogeneous ensemble members

Baseline: Smutz and Stavrou's mutual agreement (score disagreement). C must win where scores are silent (e.g., both
members evaded) or classify the cause. PASA is the nearest attribution-based detector (not malware).
**Why parked:** the score-disagreement baseline is strong.
