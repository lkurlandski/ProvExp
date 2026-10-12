# 3-C: Rule matches pushed forward into a learned detector's features

Status: design proposed (2026-10-12), go/no-go passed (runs 34, 35). Not built. The task's motivation may still be refined
(user: the original question was crude; look for a question that better shows the pushforward's use before building).
Packing is not a motivation or case study (user, 2026-10-12): well-explored.

## Proposed design

A rule set runs alongside a learned detector (PEberus: YARA plus EMBER GBDTs; `docs/related_work.md`, H). A rule's
string matches are a problem-space explanation of why it fired. For each rule: is the GBDT redundant with it (relies on
the same content) or complementary, and if complementary, why?

- **Representation gap:** the matched bytes S reach the feature vector only diluted (a tiny share of whole-file
  aggregates); no retraining helps.
- **Reliance gap:** S determines features ((Pᵀ1_S)_j ≥ 0.5), but the GBDT puts little or opposite credit on them
  across the files where the rule fires.

What only the pushforward gives: per-rule profiles across files (offsets differ, features do not); the match's
location decides the features (the same API name feeds import hashes in the import table, string features
elsewhere); the split itself. Per file, the scalar "credit S carries" equals the pullback's mass on S (checked in run
34), so it is not the pushforward's contribution. Realistic alternatives: verdict co-occurrence; deleting S and
re-scoring the GBDT (no P; a scalar); mapping rules to feature groups by hand from the extractor's code.

## Go/no-go (run 34, `scripts/yara_check.py`; fixed in advance)

Yara-Rules (commit 0f93570) `packers/`, `crypto/`, `antidebug_antivm/`, `capabilities/` on PB1's 100 pilot files;
string matches only. Hypothesis: anti-debug and packer rules pass the split through import, string, and section
features; crypto constants are representation gaps.

| | result | needed |
|---|---|---|
| rules located on ≥ 5 files | 47 (27 without `packers/`) | 10 |
| malware files matched by one | 44/50 (34/50 without `packers/`) | 30 |
| rules with S holding ≥ 0.5 of a non-aggregate feature (median file) | 16/47 (14/27 without `packers/`) | 1/3 |

**GO**, carried by `capabilities/` (11/15 split) and `antidebug_antivm/` (3/5). Crypto: 0/7, every rule lands in the
byte histograms (as hypothesized). Packers: 2/20; PEiD signatures match entry-point code, which lands in the
aggregates (the hypothesis failed there), and many are near-duplicates (five Borland Delphi rules, several MSVC/.NET).
The determined features are mostly hashed imports (`import_hash_*`, `library_hash_*`) plus `strings:regex_debug`: the
content behind opaque features. The pushforward's top feature group differs from the rule's usual one in 25-44% of
files for most capability rules (imports vs. strings), so the location matters.

**A risk for the reliance side:** each rule's bytes carry little of the GBDT's attribution (median 0.8%, max 2.3% of
|a| for the split rules; at most 0.17 log-odds). Without a reference (e.g., same-size random byte sets, or the
features' credit elsewhere), every represented rule may look like a reliance gap. The experiment needs that contrast.

Outputs: `artifacts/experiments/yara_check/seed-0/`; log `artifacts/logs/yara_check-seed0.log`.

## Reliance go/no-go (run 35, `scripts/yara_reliance.py`; fixed in advance)

For the 16 split rules, the pullback of the GBDT's |TreeSHAP| summed over S, against 200 random byte sets with S's run
lengths at uniform offsets; S is above random in a file if it beats their 95th percentile. Pass: more than half of the
rules above random in >= 60% of their files. Hypothesis: matched API names sit in the import table, whose bytes carry
concentrated credit, so S beats random in most files.

**GO: 14/16.** Every capability and anti-debug rule is above random in 83-100% of its files (median 60x to 3,800x the
random median); the two PEiD rules that showed a split (Armadillo, MSVC 6) are not (their matches are large code
regions). The features S determines carry 1.3-4.3x more credit on files where the rule fires than on the other pilot
files. In absolute terms each rule's bytes stay a small part of the verdict (0.1-2.3% of |a|).

**Reading, and what it changes.** The reliance side is not flat; if anything it is uniformly *high*: no represented
rule is a reliance gap at this threshold, so the three-way split collapses to represented-and-relied-on vs. not
represented, and the second half is P alone. Two caveats: uniform random runs mostly land on bytes no non-aggregate
feature reads, so beating them partly says "S lies where the GBDT reads" (a reference matched in provenance, e.g.
other bytes that determine non-aggregate features, would be stricter); and |credit| ignores direction. The likely
refinement (to discuss): **direction**, as in 3-A's triage: a rule firing says "suspicious"; does the GBDT read the same
content toward malware or toward benign, per rule and across files?

Outputs: `artifacts/experiments/yara_reliance/seed-0/`; log `artifacts/logs/yara_reliance-seed0.log`.
