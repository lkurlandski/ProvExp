# Resume: the theory track, bounds on size (the mathematics is done; what remains is the user's decision and text)

Written at the end of session 76 (2026-11-16), the last theory session with Fable; the next one runs on Opus.
Self-contained; paste it into a fresh session or say "read `docs/resume-prompt-theory.md` and carry it out". The
main line (the scale-up on tigris) is a separate track with its own prompt, `docs/resume-prompt.md`; do not mix the
two.

## 1. The job

**No new mathematics.** The statements and proofs are in `docs/evidence/theory-analysis.md`, **part H** (the form
to write from) with parts F and G as the record. The job is to carry out what the user decides about the
manuscript (section 4), as text, in the way of section 6. If something in part H looks wrong or incomplete, say so
and stop; do not repair it by improvising a proof. Do not extend the theory (no new lemmas, no generalizations, no
"tighter" rules) unless the user asks, and then work it out in the note first, with a counterexample hunt on
Algorithm 1 before any proof.

Open the session by asking the user for the decision of section 4 if it has not been given. Do not write
manuscript text before it.

## 2. How to work

- **Read first:** `docs/status.md`, `PLAN.md` ("Thesis", next step 8), then `theory-analysis.md` parts G and H in
  full (B and F when needed), then §3 and Appendix C of the manuscript (`_d_framework.tex`, `_j_proofs.tex`).
  Paper numbers come from `manuscript/main.aux`.
- **Stay on theory and text.** No experiments, no detector training, no extractor changes. If something needs
  data, say what and why, and stop.
- **Plain language first, then mathematics.** One idea per paragraph. If the user finds a statement obvious,
  suspect the statement.
- **Say plainly what is elementary, published, or unknown.** Part H.10 lists the traps; read it before writing a
  sentence.
- **A' is not a verdict** (F.2). The four small ideas of session 74 (C.3-C.6) are set aside by the user; do not
  raise them.
- No option menus with invented names; no subagents.

## 3. Where things stand (three sentences each)

**Bounds on size (H.1-H.4).** Give each edit a cost and each change in the signature a size, totalled per kind of
item. A sum then *has a rate* (it moves by at most rate times budget, H.2) or has none and keeps its direction; the
readout rule carries the intervals to features by two corners (H.3), and a score monotone in each feature it reads
is certified for a file by one evaluation at the worst corner (H.4). All proved, all elementary.

**Strict monotonicity loses nothing under directions alone (H.5).** For any relaxed score with a certificate, the
lowest score the table lets the attacker reach is a strictly monotone score with the same guaranteed detections
and no more false positives. With a budget this is false (the example in H.5), which is where the user's idea of a
"somewhat monotone" detector lives. It is a statement about what a score can represent, not about training, and
it is not the converse of Corollary 1 that sessions 71-73 closed.

**EMBER (G.3, G.4).** At the paper's budget (512 KB on every file) nothing can be shown: the costly constraints sit
on features that one write or a few dozen bytes move as far as needed, and the bounded features are already read as
counts. Read from the pilot's table and price list only; the scale-up's are on tigris and unread. A budget curve
(certified detection at smaller budgets) would be a new experiment and is the user's call.

**Closest work, read in session 76 (H.8):** Chen et al. (USENIX Security 2021) and Vos and Verwer take per-feature
perturbation ranges from the analyst and train trees against them; PDFs in `papers/`, not yet in the bibliography.
The literature was not searched for H.5.

## 4. The decision that waits for the user (H.9)

1. A paragraph in the discussion on what the directions discard (Claude's advice: yes). Note that the discussion
   section is written late (PLAN.md step 7); ask whether to draft it now or leave a note in `docs/paper-mock.md`.
2. H.5 beside Corollary 1, as a short proposition with its proof in Appendix C or as a sentence. It changes how
   §5.4's price is read (the price of the guarantee under the table, not of the model class, within H.5's
   caveats), so it needs the user's explicit agreement.
3. A subsection after Sound Directions for H.1-H.4 (about 400-450 words). Claude's advice: only with a result
   behind it (the budget curve, or a second instance), and never woven into §3.3.

Also open, if the user wants them: re-reading the split of the cost from the scale-up's price list once it is
copied from tigris (G.4); the literature check for H.5.

## 5. The rest of the theory

`manuscript/main.aux` has Definitions 1-10, Proposition 1 (*Exact side effects*), Theorem 1 (*Sound directions*),
Lemma 1 (*Closure*), Corollary 1 (*Robustness*), Table 1 (the readout forms), Equation 11 (the readout rule),
Table 7 (the sign table, Appendix C). **The user's close read of Lemma 1 and the readout rule is still pending;**
expect comments on wording.

## 6. How the manuscript is changed (keep to it)

1. The idea is worked out in `theory-analysis.md` (done: part H).
2. On the user's go, the text goes into the manuscript **uncommitted**; the user sees it as rendered text with a
   list of the choices made, reviews, and approves the commit.
3. A statement that belongs to the framework gets its own environment in §3 with the proof in Appendix C. A
   paragraph in §3 that only points to the appendix was rejected ("splits the baby").
4. Prose with the project skill `paper-prose`; `make` and `make check` in `manuscript/`; small diffs; a few
   paragraphs per block, each reviewed by the user.

## 7. Follow-ups that are not this session's work

Only if the user asks (PLAN.md, next step 8 (c)): the instance-level work for Lemma 1; `monotone_violations` on the
scale-up's trained models; the tighter normalized-bin rule in `reach.py`; one overfull vertical box of 1 pt in
Appendix D.

## 8. Settled; do not reopen without a strong, specific reason

- Closed in sessions 71-73: converses of Corollary 1, bounds on the cost of robustness computed from data, feature
  engineering as theory, boosting rounds. `docs/archive/fable-cost-of-robustness.md` is not read by default.
- Every feature mapping meets Definition 5: a property of the framework, not a gap. The relational refinement of
  the sign table was declined as machinery without payoff on EMBER; H.7's items are of that family.
- The formalization is a contribution; harsh but fair about novelty; credit foundations without a
  borrowed-versus-new ledger. Elegant fixes only. Proofs carry the weight.
- The framework is format-free. No timing claims, no effort claims, no packing motivation, no sandbox execution, no
  extractor redesign for robustness. Cited work in its authors' terms, checked against the PDF in `papers/`.

## 9. Output and housekeeping

- Continue `theory-analysis.md` with part I onward; commit after each part. Do not push.
- The other track edits `docs/status.md`, `PLAN.md`, `docs/README.md` and `docs/resume-prompt.md` too. Keep this
  track's edits to its own paragraphs there, and rewrite **this** file at the end.
- Two sessions were numbered 74 (the head node on tigris, and the theory session); the theory track's are "74
  (theory)", 75 and 76.
