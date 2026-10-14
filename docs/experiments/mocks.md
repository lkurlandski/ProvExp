# Mock experiments (predicted outcomes, NOT real data)

> **Everything in this file is fabricated.** The tables are guesses at what the experiments would produce, written to
> decide whether to run them and how they would be presented (the "mock the result first" rule). No number here comes
> from a run. Each table is labelled FAKE. Delete or replace a block the moment the real experiment lands.

Created 2026-10-14, in response to the self-review (`docs/review-2026-10-14.md`). These cover the three items that
touch MalConv or retraining, which we are not ready to run: the pushforward's faithfulness measured on MalConv (review
item 3), the header-attack comparison for the audit (item 4), and the audit's mitigation (item 10/W6).

---

## M1. Pushforward faithfulness, measured on MalConv (review item 3)

**The gap.** Section 5.1 tests the pushforward by pushing forward explanations of the *GBDT* and deleting features. But
the audit (5.3) pushes forward *MalConv's* Integrated Gradients, and we never test whether that pushed-forward
explanation is faithful as a whole; we only confirm individual fields by scrambling. A reviewer will ask what
"faithful" means for a model that never computes the features (W5).

**Design (what we would run).** MalConv lives on the bytes, so we test the pushforward there. Rank the features by the
pushed-forward IG (summed over files, as in the audit, or per file). For a single file, take the top-$k$ features, map
them back to their bytes through that file's $P$, scramble those bytes (loader-safe, the audit's operator), and measure
the drop in MalConv's log-odds. Compare, at the same number of bytes, with:
- the **surrogate** ranking mapped through $P$ the same way (what predicts MalConv, not what it reads);
- **IG aggregated over fixed windows** (no $P$): rank 512-byte windows by summed IG, scramble the top windows;
- **random features**.
A faithful pushforward puts MalConv's own evidence on few features, so scrambling their bytes should drop MalConv's
score faster than the window or random rankings, and at least as fast as the surrogate. Reuses `audit_evade.py`; runs
on the held-out malware; no retraining. (This *does* re-score MalConv, so it waits until we are ready to re-evaluate it.)

**FAKE — predicted deletion curve (per-file, 191 held-out malware, median MalConv log-odds removed):**

| bytes scrambled (top-k features) | pushforward | surrogate→P | IG over windows | random |
|---|---|---|---|---|
| ~32 (k=1) | 1.1 | 0.7 | 0.4 | 0.1 |
| ~128 (k≈4) | 2.6 | 2.1 | 1.3 | 0.3 |
| ~512 (k≈15) | 4.8 | 4.3 | 2.9 | 0.9 |
| ~2048 (k≈50) | 7.1 | 6.8 | 5.2 | 2.4 |

**FAKE — one-number summary.** Area ratio to the strongest baseline (IG-over-windows): pushforward ≈ 1.5×, surrogate ≈
1.4×, random ≈ 0.4×. Predicted reading: the pushforward concentrates MalConv's evidence on the features it names
better than aggregating IG over windows does, and about on par with the surrogate while needing no second model. This
is the pushforward analogue of the pullback's byte-resolution win in Table 1, and it tests the transfer on the model
the application uses.

**Risk if real numbers differ.** If the pushforward only matches IG-over-windows (ratio ≈ 1.0), the audit's "named,
recurring reliance" still stands by the field confirmations, but the "faithful on MalConv" claim weakens; we would
report it as partial, consistent with the resolution limit (IG over the bytes is itself a coarse source).

---

## M2. Header-attack comparison for the audit (review item 4) — DROPPED 2026-10-14

> **Dropped** (user): re-evaluates MalConv, adds a query-based search loop, and the benefit does not justify the
> complexity or the burden of explaining it. Kept below only as a record of what it would have been.


**What a reviewer wants (W6).** MalConv is known to be header-sensitive, and published attacks evade it far more often
than our 12.4%. Two questions: (a) are the audited fields genuinely *exploitable*, not merely correlated with evasion;
and (b) where does 12.4% sit relative to what an attacker who targets the same fields could get?

**What the comparison would add, concretely.** A query-based attacker that *optimizes* the same loader-safe fields
(greedy or random search over the allowed values per field, a few hundred MalConv queries per file), instead of our
single random/benign draw. Two reference points frame it:
- **Fields-restricted attack:** optimize only the audited loader-safe fields. Upper bound on evasion attributable to
  the audit's fields; its gap over our 12.4% is the cost of not searching.
- **Full-header attack (context only):** a published-style DOS-header + header manipulation, unrestricted. The
  well-known ceiling, which we do *not* claim to reach and which motivates restricting to loader-safe, non-DOS fields.

**What it solves.** It converts "12.4% evasion" into "these fields, when actually attacked, evade X%, and they lie
outside the DOS header that prior work already exploits" — i.e., it defends the finding's novelty (reliance beyond the
known region) and shows exploitability without proposing a new attack. **This is re-evaluating MalConv (queries), so
it waits.**

**Complexity, honestly.** Moderate. The search loop is new (optimize field values by MalConv queries), but it reuses
the audit's field list, loader-safe value sets, and scoring. The full-header reference needs a published attack's field
set, not its code. Main risk: the fields-restricted attack could evade so well that our single-draw 12.4% looks weak by
comparison, or so poorly that exploitability looks marginal.

**FAKE — predicted evasion at MalConv's 1% FPR, 902 detected held-out malware:**

| recipe | evasion | note |
|---|---|---|
| audit fields, single loader-safe draw (our 5.3 result) | 12.4% | real (runs 47-49) |
| audit fields, optimized by queries (fields-restricted attack) | ~27% | FAKE |
| other loader-ignored non-DOS fields, optimized | ~14% | FAKE |
| full header incl. DOS, unrestricted (published-style) | ~60% | FAKE, context only |

Predicted reading: searching the audited fields roughly doubles evasion over a single draw (so they are genuinely
exploitable), stays well above the optimized non-DOS null (so the audit found the right fields, not just any
loader-ignored ones), and remains far below the full-header ceiling (so we neither claim nor need a DOS-header attack).

---

## M3. The audit's mitigation (review item 10, W6)

**The claim to back.** Contribution 3 and the discussion say the audit "points to its mitigation": zero the audited
fields for every file, at test time or in retraining, since a field MalConv relies on but an attacker can change freely
should not be read. This is currently announced, not measured. **Retraining MalConv is out of scope right now**, so the
numbers below are predictions.

**Design (what we would run, later).** Two mitigations, each a defender action:
- **Test-time zeroing:** overwrite the audited fields with a constant before MalConv scores any file (no retraining).
  Measure the drop in clean detection (TPR at 1% FPR on untouched held-out files) and the drop in evasion (re-run M2's
  fields-restricted attack against the zeroed model).
- **Retrain-with-zeroing:** zero the fields in training and test, retrain MalConv, measure the same two quantities.

**FAKE — predicted mitigation effect:**

| model | clean TPR @1% FPR | evasion (fields-restricted attack) |
|---|---|---|
| MalConv, unmodified | 97.3% | ~27% (M2, FAKE) |
| + test-time zeroing of audited fields | ~96.8% | ~9% |
| + retrain with audited fields zeroed | ~97.1% | ~6% |

Predicted reading: zeroing the audited fields removes most of the evasion lever (27% → ~9% at test time, ~6% after
retraining) for a small clean-detection cost (≤0.5 pts), which is the point of the audit — it names a specific,
cheap-to-remove weakness. If the clean cost were large, the fields carried real signal and the mitigation would be a
trade-off rather than a free win; we would report whichever the data show.

---

## Decisions these mocks inform (for the user)

- **M1 (pushforward on MalConv):** cheap, reuses existing code, and closes the clearest methodological gap (W5). Worth
  running first, once we re-enable MalConv scoring.
- **M2 (header-attack comparison):** more complex (a query-based search loop) and re-evaluates MalConv. Run only if the
  predicted framing (exploitable, outside the DOS header, below the ceiling) reads as worth the added machinery.
- **M3 (mitigation):** needs retraining MalConv; defer to the cluster round. The test-time-zeroing half needs no
  retraining and could run with M2.
