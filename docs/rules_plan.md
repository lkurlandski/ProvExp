# 3-C: Rule matches pushed forward into a learned detector's features

Status: on hold (2026-10-12). Runs 34-37 rest on the pullback and Pᵀ, not the pushforward (sniff test); next, a mock of
the paper table with the operator behind each column. Earlier: design proposed, go/no-go passed (runs 34, 35). The task's motivation may still be
refined (user: the original question was crude; look for a question that better shows the pushforward's use before
building).
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

## The stricter reference (run 36, same script; supersedes run 35's output, its numbers unchanged)

A first attempt drew the reference from bytes that any non-aggregate feature reads; that is 99.9% of a median file
(section entropy and string counts read whole sections), so it was no stricter. The reference now matches S in
**concentration**, c_i = sum_j P_ij over the non-aggregate features (a byte of a short imported name holds a large share
of its hash bucket; a byte of a large section a tiny share of its entropy): random runs with S's lengths among bytes
with c_i >= the 25th percentile of c over S (a pool 35-1,240x |S|). Hypothesis: the ratios drop by orders of
magnitude; the generic API rules (registry, file operations) fall to the reference level, anti-debug and network rules
stay above.

| rule | files | above matched ref. | x matched median | signed credit > 0 |
|---|---|---|---|---|
| network_dns | 6 | 0.67 | 55.6 | 0.83 |
| network_tcp_socket | 7 | 0.57 | 3.9 | 0.57 |
| keylogger, win_private_profile, Winsock2, screenshot | 7-12 | 0.25-0.30 | 0.9-4.9 | 0.58-0.92 |
| escalate_priv, win_hook, win_token, anti_dbg, win_files_operation, win_registry | 6-35 | 0.11-0.17 | 0.9-2.4 | 0.33-0.86 |
| Internet_API, DebuggerException, the two PEiD rules | 5-8 | 0 | 0.5-1.2 | 0-1 |

Ratios fell from 60-3,800x to about 1-5x (network_dns 56x). Against content the GBDT reads as directly, most rules'
bytes are credited about like any other: the GBDT does not single out what the rule matches, beyond its general
reliance on imported names. Only the DNS rule (and TCP sockets, marginally) stands out. The hypothesis held for the
generic API rules and failed for anti-debug (anti_dbg: 0.15). **So reliance gaps do appear, under the matched
reference: most represented rules are reliance gaps.** Direction (information): the signed credit is mostly toward
malware (57-92% of files), except DebuggerException (0/8) and win_hook (2/6). Small samples (5-35 files per rule).

Outputs: `artifacts/experiments/yara_reliance/seed-0/`; log `artifacts/logs/yara_reliance-seed0.log`.

## Deletion check (run 37, `scripts/yara_deletion.py`; fixed in advance)

The 16 split rules plus the 7 crypto rules (representation-gap controls), 268 (rule, file) pairs: delete S with PB1's
operator vs. 20 concentration-matched reference sets (run 36's reference); S is above in a file if the GBDT's response
|Δ log-odds| beats the references' 95th percentile; a rule is "relied on" if above in at least half of its files.
Criterion: deletion and attribution agree for more than half of the split rules, and their per-rule shares are
positively rank-correlated. Hypothesis: network_dns and network_tcp_socket relied on, the rest not, crypto not.

**The criterion is met (14/16 agree, Spearman 0.39), but the hypothesis fails where it matters.** The agreement comes
from the gap category (no rule is relied on by deletion; 0-33% of files above). The two rules the attribution calls
relied on are not confirmed: network_dns above in 1/6 files, network_tcp_socket 0/7. Their median response does exceed
the references' median (0.081 vs. 0.000 and 0.061 vs. 0.014 log-odds), but the references are heavy-tailed and the
95th percentile is not beaten. The representation-gap controls hold: deleting crypto matches changes nothing (median
response 0 for 6/7 rules). Checked: zero bytes in the reference pool (a no-op under zero fill) are 1-22% of it, not
the cause. **Reading:** the representation-gap and reliance-gap categories are supported; "relied on" is not
confirmed at pilot scale (6-7 files per rule). The criterion was too weak (it could pass on the majority category); at
scale, judge each category separately.

## Rule set (decided 2026-10-12)

Stay with the generic Yara-Rules sets for the methodology: they already populate all three categories (representation
gap, reliance gap, relied on), and the bottleneck is files per rule, not rules. A curated, realistic set (YARA-Forge,
with files selected where its rules fire) is noted for later, before final numbers, for the realism of the case.

## Post-mortem (2026-10-12)

**Why 3-C is on hold.** In the per-rule table this design produces, the "reliance" column is the pullback's mass on the
matched bytes (per file, sum_j |a_j| (Pᵀ1_S)_j = the pullback of |a| summed over S), the "representation" column is
Pᵀ1_S (P, not the pushforward ψ = PᵀD†b), and the deletion check uses no P. The pushforward proper only described
which feature group a rule lands in. As built, 3-C is 3-A with a YARA rule as the second detector, and it does not show
the pushforward's use, which was its purpose. The use case was also soft: who acts on "the model is redundant with
rule R"? Nobody retires a cheap, explainable rule for it.

**How it happened.** The first proposal already said that per-file reliance is a pullback quantity and that the
pushforward would have to earn its place through profiles aggregated across files. The four checks that followed
(runs 34-37) each tested feasibility one step downstream (coverage, a non-empty split, reliance against a reference,
deletion), never that premise. Each passed or nearly passed, which looked like progress; the flaw surfaced only when
the user asked for a sniff test before scaling. Same pattern as 3-B. Along the way: a "stricter" reference that was not
(99.9% of bytes feed some non-aggregate feature), and a deletion criterion that could pass on the majority category.

**What carries over.** The tooling (YARA scanning with byte offsets, per-rule Pᵀ1_S, concentration-matched references,
deletion against them) and two facts: generic string rules match most files with byte locations, and their content
reaches the GBDT mostly through hashed import features. Option (a), comparing the pushed-forward rule with TreeSHAP in
feature space, is not pursued: per file it reduces to the pullback's mass again, and its aggregate is a description
without a task.

**Rule for next time** (`PLAN.md`, screening criterion 6): mock the paper's paragraph and table first, with the
operator behind each column, and screen that before any data check; re-check it after every run.
