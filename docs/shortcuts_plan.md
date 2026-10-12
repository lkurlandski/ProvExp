# 3-B: Finding (and Mitigating) Spurious Correlations with the Pullback

Started 2026-10-09. An extrinsic application (`PLAN.md`, "Paper structure"). Goal: an application of the pullback that
is impossible or much more expensive without it.

## Why it failed (2026-10-12)

**Outcome:** the pipeline works (discovery, causal confirmation, mitigation; 3.6% of detected malware evades at 1%
FPR, removed by neutralizing 6 features at no accuracy cost), but it does not show the pullback's value. The relied-upon
shortcuts sit on *named* features (`datadirectories:security_size`, `debug_size`) that feature-space SHAP surfaces
directly; the one finding only the pullback could make (`.rsrc` in a hashed feature) barely matters (7% of the evasions
alone). Of credit within the top bytes, 83% comes through spans dominated by one feature; summing credit across
features (P's distinctive operation) rarely changes anything here.

**Pitfalls, to avoid next time** (the criteria now in `PLAN.md`, section 3):
- *The necessity of P was assumed, not checked.* The claim was "SHAP cannot name content in an opaque feature", but
  nobody checked, before building, whether this model's reliance lies in opaque features. The check took minutes on
  existing data (run 22's spans) and came last instead of first.
- *A strawman baseline.* The byte 4-gram miner is not what a practitioner would use; the realistic alternative (SHAP
  plus feature names plus the extractor's code) was never put up against the idea.
- *Work piled onto a weak premise:* transplant, reliance, mining, mitigation, and forging were built before the premise
  was tested, and positive intermediate results (confirmed shortcuts) were read as progress on the claim.
- *The task was chosen for the method's story, not for need:* shortcut discovery is real, but on a feature set with
  readable names it does not need what is distinctive about P (opaque-feature content, credit summed across features).
- *Proposals to move on* from a partial result instead of reassessing it.

## Claim

A feature-based detector can learn **spurious correlations** -- reliance on content that tracks the label in the
training data but has nothing to do with maliciousness (compiler/packaging artifacts, trivially forgeable metadata).
Shortcut learning is a recognized ML-for-security problem (Arp et al., "Dos and Don'ts"). Finding them in a detector
over an opaque feature set is hard: feature-space SHAP says `imports:library_hash_254` is influential but not *what*
it is (a different library in every file), so you cannot judge whether the reliance is spurious or act on it.

**The pullback surfaces spurious correlations and makes them actionable:** it resolves each influential feature's
credit back onto the content that produced it, across a corpus, so recurring artifacts stand out; then P tells you
which bytes/features to manipulate to confirm or remove the dependence. This is **not** PB1 (per-file faithfulness of
the transfer) and **not** SHAP (which cannot name content or tell spurious from meaningful in an opaque feature). It
is **much cheaper than occlusion** (one extraction vs. hundreds per file, PB1), so it runs corpus-wide.

Not every relied-upon pattern is spurious, and "spurious" is a judgement about the domain (allowed in experiments,
`CLAUDE.md`); the test is whether the content is semantically irrelevant to maliciousness yet the model depends on it,
and whether an attacker can set it. The strongest cases here are forgeable metadata (a code-signing certificate, a
compiler's timestamp), where "signed -> benign" is the textbook malware shortcut.

**Framing (agreed 2026-10-12, after the SHAP check below).** The contribution is *systematic* discovery and
realization: corpus-wide, over every feature, with no hand-built mapping from features to bytes. No head-to-head
baseline; the comparison is published practice. Severi et al. (USENIX Sec 2021, Sec. 6 and Table 4) realize
SHAP-selected EMBER features with a hand-built watermarking utility and discard "all hash-based features" ("given the
preimage resistance of the hash function"), leaving 35, then "any features whose value is impacted by more than one
other feature", leaving **17** (version fields, linker version, MZ_count, section counts, paths/URLs/registry counts,
size, timestamp). Their task (a backdoor) is orthogonal to ours (auditing a detector); the overlap is the problem they
had to work around. None of our confirmed artifacts is among their 17 (data-directory sizes; a section name in a hashed
feature). The pullback does not invert hashes: it supplies, from the corpus, content that occupies the bucket, and
Pᵀ1_S lists every feature a forged byte set also changes (their dependency problem).

**Exploitability, not an attack.** The adversarial-malware literature (e.g., Demetrio et al., Anderson et al.,
Pierazzi et al.) reaches higher evasion with general manipulations; we do not compete with it. The check is scoped:
the adversary writes only the flagged content at the bytes P names, the file parses with its original section layout,
and functionality is argued from the format (the loader ignores the certificate-table and debug-directory sizes and
section names), not tested in a sandbox. The question is whether the shortcuts are a liability at the operating
threshold and whether the P-named mitigation removes it.
Run 29 (`scripts/shortcuts_forge.py`): the confirmed artifacts, one per top feature, forged together into 2,000
held-out malware; evasion at the 1%-validation-FPR threshold, vs. random bytes in the same runs, on the original and
the neutralized GBDT. Hypothesis: the effects roughly add (about +2.5 log-odds), so a noticeable share of detected
malware near the threshold evades, but not the confident files; the neutralized model shows no evasion.

**Run 29 results** (threshold 0.676 log-odds at 1% validation FPR; 1,934 of 2,000 detected; 1,922 forgeable; ~3 min
per model): **3.6% of detected malware evades** (70 files) vs. 0.1% with random bytes in the same runs; median drop
2.20 vs. 0.36 log-odds. Neutralized GBDT: 0.1% vs. 0.16% (no effect). Hypothesis held, the share is modest.
Leave-one-out on the 70 evading files (scratch analysis, not a run): the certificate size alone evades in 30%, DEBUG.Size
alone in 33%, both in 91%; `.rsrc` applies to 14 of them and adds little (7% alone). **The evasion rests on two named
data-directory sizes, not one, but both are named features that SHAP would surface; the hashed finding barely matters.**

## Design (settled 2026-10-12)

1. **Discovery** (run 22, `scripts/shortcuts.py`): per file, the pullback of interventional TreeSHAP over the 2,000
   explanation-set files; the top-256 benign-credited bytes, split into spans by top feature, grouped across files
   by (top feature, content), ranked by files x mean credit.
2. **Candidates by a fixed rule, not by hand:** the top 20 benign-pushing patterns that recur in >= 10 files. Each is
   labeled by the assistant from its content alone (domain judgement, `scripts/shortcuts_tables.py`, `LABELS`):
   *artifact* (toolchain/metadata, no bearing on behavior: the spurious kind) or *structural* (reflects what the file
   contains). Run 24's Delphi timestamp ranks 22nd, outside the rule.
3. **Transplant test** (run 27, `scripts/shortcuts_transplant.py`): in 200 held-out malware (run 24's files), the
   target's own P names the bytes to write: a run of P's column j (the top feature) of the content's length, else a
   run of a feature in j's hashed family (`section:size_hash_*`). Overwrite with the content; random bytes in the same
   run are the control; both must parse with the original section layout. **Confirmed** (fixed before the run) if
   >= 20 files apply, the median drop toward benign and the median paired effect over the control are both >= 0.1
   log-odds, and a one-sided Wilcoxon test gives p < 0.05/20. Beating the control alone is not enough: a random value
   is often anomalous in itself (a random entry point moves the score 2.6 toward malware).
4. **Reliance and carried features** (run 26, `scripts/shortcuts_reliance.py`): credit at the feature's bytes over the
   explanation set; for each candidate's bytes S, the share (Pᵀ1_S)_k of every feature's provenance they carry.
5. **Baseline without P** (runs 25-27): label-skewed byte 4-grams (Kolter & Maloof) mined from 5,000 training files
   (50 random shards x 50 per label; `scripts/shortcuts_train_sample.py`), ranked by chi-squared; their reliance
   (best occurrence anywhere, a generous measure) and an append test (the only placement without P). Same sample gives
   each candidate's training prevalence by label. Occlusion is the cost baseline, cited from PB1 (not re-run).
6. **Mitigation** (run 28): neutralize (zero in every split) the features carried (share >= 0.5 in >= half of the
   occurrences) by the confirmed *artifact* candidates; retrain the GBDT; re-run the transplant test and clean metrics.

Hypothesis (stated with the design): forgeable metadata moves the model clearly above the control; hashed-name
content moves it less.

## Results (seed 0)

Transplant over 197 scored malware (3 below zero log-odds skipped); drop = median move toward benign, content vs.
random in the same bytes. carry = median share of j's provenance in the candidate's bytes (1 = the bytes set the
feature). test b/m = discovery files by label.

| # | content | top feature | judgement | test b/m | credit | carry | n | drop (content / random) | confirmed |
|---|---|---|---|---|---|---|---|---|---|
| 0 | `0x00000000` | `optional_header_AddressOfEntryPoint` | structural: no entry point | 229/66 | 1.02 | 1.00 | 193 | -0.18 / -2.60 | no |
| 1 | `0x20000060` | `section:num_rx` | structural: code-section flags | 678/558 | 0.09 | 1.00 | 98 | +0.11 / +0.51 | no |
| 2 | `0x54000000` | `datadirectories:debug_size` | artifact: debug-dir size | 185/62 | 0.46 | 1.00 | 185 | +0.72 / +0.59 | **yes** |
| 3 | `0x00000000` | `optional_header_SizeOfCode` | artifact: SizeOfCode 0 | 199/0 | 0.35 | 1.00 | 196 | -0.05 / +0.84 | no |
| 4 | `0x70000000` | `datadirectories:debug_size` | artifact: debug-dir size | 136/28 | 0.35 | 1.00 | 185 | +0.62 / +0.58 | no |
| 5 | `.reloc` | `section:size_hash_5` | artifact: section name | 405/332 | 0.01 | 0.67 | 113 | -0.26 / -0.08 | no |
| 6 | `0x00000000` | `datadirectories:import_virtual_address` | structural: no imports | 227/31 | 0.20 | 1.00 | 191 | +0.29 / +0.29 | no |
| 7 | `.rsrc` | `section:size_hash_43` | artifact: section name | 316/353 | 0.02 | 0.67 | 51 | +0.48 / +0.00 | **yes** |
| 8 | `0x00000010` | `optional_header_ImageBase` | artifact: DLL default base | 426/62 | 0.09 | 1.00 | 158 | +0.14 / +0.21 | no |
| 9 | `0x00200000` | `datadirectories:resource_virtual_address` | artifact: linker layout | 172/0 | 0.18 | 1.00 | 196 | -0.82 / -1.10 | no |
| 10 | `!This program cannot…` | `strings:regex_dos_msg` | artifact: DOS stub | 165/269 | 0.05 | 1.00 | 1 | (166 already present) | no |
| 11 | `.text` | `section:size_hash_41` | artifact: section name | 185/155 | 0.01 | 0.67 | 41 | -0.03 / -0.08 | no |
| 12 | `0x1c000000` | `datadirectories:debug_size` | artifact: debug-dir size | 190/61 | 0.04 | 1.00 | 160 | +0.34 / +0.52 | no |
| 13 | `0x38280000` | `datadirectories:security_size` | artifact: certificate-table size | 29/0 | 0.86 | 1.00 | 196 | +1.34 / -0.27 | **yes** |
| 14 | `0x00000000` | `datadirectories:iat_size` | structural: no IAT | 218/11 | -0.01 | 1.00 | 119 | -0.17 / +0.46 | no |
| 15 | `0x20280000` | `datadirectories:security_size` | artifact: certificate-table size | 27/1 | 0.85 | 1.00 | 196 | +1.34 / -0.27 | **yes** |
| 16 | `0x38000000` | `datadirectories:debug_size` | artifact: debug-dir size | 205/36 | 0.08 | 1.00 | 182 | +0.28 / +0.56 | no |
| 17 | `VCRUNTIME140.dll` | `imports:library_hash_4` | artifact: runtime library | 147/29 | 0.08 | 1.00 | 0 | (no 16-byte library-name run) | no |
| 18 | `0x00000400` | `optional_header_SizeOfStackReserve` | artifact: linker default | 55/30 | 0.20 | 1.00 | 167 | +0.20 / +0.41 | no |
| 19 | `0x00000000` | `datadirectories:resource_virtual_address` | structural: no resources | 48/160 | 0.08 | 1.00 | 137 | +0.17 / -1.15 | **yes** |

- **Confirmed spurious correlations (artifact, causal, attacker-settable): the certificate-table size** (setting
  only the data-directory size, no certificate: +1.34 vs. -0.27; the "signed -> benign" shortcut), **the debug
  directory size 0x54** (+0.72 vs. +0.59), and **the section name `.rsrc`** in a hashed section bucket (+0.48 vs.
  0.00; mostly by renaming another section, the family placement). Resource RVA 0 is confirmed but structural.
- The model also relies on **the presence of a debug directory** whatever its size (candidates 4, 12, 16: any value,
  random included, moves it +0.3 to +0.6), but not on the specific values, so they are not confirmed.
- Not byte-settable or not testable by overwrite: the DOS stub (already in 166/197 targets) and `VCRUNTIME140.dll` (no
  library name of 16 bytes to overwrite). Run 23 (appending strings) remains the boundary for aggregate features.
- Effects are moves, not evasions: almost nothing flips (<= 1%); held-out malware sits far above zero log-odds.
- **Hypothesis:** partly held. Forgeable metadata (certificate size, debug size) moves the model most; one hashed
  name (`.rsrc`) moves it too; several metadata values (SizeOfCode 0, ImageBase, linker layout) do not beat a random
  value.

**Training prevalence** (run 25, 2,500 + 2,500 files, at the feature's bytes): the confirmed artifacts are
benign-skewed in training too (DEBUG.Size 0x54: 22.0% vs. 6.4%; certificate sizes 0.4%/0.1% and 2.3%/0.0%; `.rsrc`
92.8% vs. 82.2%), i.e., learned correlations, not explanation-set noise.

**Baseline without P** (runs 25-27; `python scripts/shortcuts_tables.py --seed 0`, Table 2). The top benign-skewed
4-grams by chi-squared are almost all X.509/DER bytes of embedded certificates (`/crl`, OID prefixes, ASN.1 times):
the miner finds the same "signed -> benign" signal. But for the top 20 the model's credit is ~0 at any occurrence
(mean 0.001; vs. 0.29 for the pullback's), and appending them moves nothing (+0.00 vs. +0.00): the model does not read
the certificate's content, it reads the data-directory size, which the miner cannot point to. None of the 4-grams of
any pullback candidate ranks in the miner's top 1,000. Content without a location is also ambiguous: the five
`0x00000000` candidates share the same best-anywhere credit (0.29), while their credit at the feature's bytes ranges
from -0.01 (IAT size) to 1.02 (entry point); the certificate size gets 0.14 anywhere vs. 0.86 at its field. Occlusion
(the cost baseline, PB1) is not re-run.

**Mitigation** (run 28): 6 features neutralized (`debug_size`, `security_size`, and the four hashed section features
that the `.rsrc` name carries: `size_hash_43`, `vsize_hash_43`, `characteristics_hash_2`, `characteristics_hash_13`).
Test ROC-AUC 0.99759 -> 0.99756, accuracy 0.9755 -> 0.9753. Transplant after: certificate and debug sizes +0.00
(trivially: their only feature is gone), `.rsrc` +0.06 vs. +0.02 (no longer confirmed: P named the full set of
features its bytes carry). The non-trivial parts are that P names that carrier set, and that removal costs nothing
measurable in accuracy.

**Does the pullback find what SHAP + feature names would miss?** (check on run 22's spans, 2026-10-12): the
pullback adds something only where one content's credit is spread over several features. Within the top 256 bytes per
file (median 60% of a file's benign credit), 83% of span credit is in spans where one feature carries >= 80%, and only
3.5% in spans where no feature carries half. The spread cases are mostly several named flags of one header field
(`header:characteristics_*`) or one section name's hashed features (`size_hash_43`, `vsize_hash_43`, ...), both easy
to group by hand. Not checked: the other 40% of credit, on bytes with low per-byte credit. **Reading:** on this GBDT,
SHAP plus feature names (and re-hashing names for hashed features) finds nearly all of what the pullback finds; P
automates the tracing and the placement but is not necessary for discovery.

## Out of scope / decided against

- **Legibility-of-reliance as the headline** (rejected 2026-10-09): subsumed by PB1. 3-B is about *spurious*
  correlations, shown causal/exploitable.
- **Ambiguity as a filter** on which credit forms spans (user, 2026-10-09: forced).
- Import-via-LIEF (new dependency); runtime functionality of modified files (parse-only verification, no sandbox).

## Open

- Whether to scale discovery or the transplant beyond pilot scale (seeds 1-2), when the user decides.
