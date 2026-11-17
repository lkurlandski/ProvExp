# Resume prompt: small tasks while the scale-up runs (Sonnet)

Written 2026-11-17 (session 79, Opus) for a Sonnet session. The scale-up runs on tigris; nothing here depends on
its numbers. Read `CLAUDE.md` and `docs/status.md`'s *Current state* first. You need not read `PLAN.md` beyond step 4
of *Next steps*. Work in the order below, **one task at a time**, and report to the user after each one.

Ground rules for this session:

- **Order: mechanical first (A), then code (B), then the manuscript (C).**
- A and B: commit each task on its own after its checks pass (`ruff`, `mypy` strict, the relevant tests; CLAUDE.md).
- **C: write it into the `.tex` files, but do not commit it.** It waits for the user's review. Before the user reads
  it, run the `humanistic-paper-review` skill on the changed passages, apply the findings, and run it again if the
  first pass found much (user: first drafts need one or two automated passes before they can give feedback). Use
  the `paper-prose` skill when writing.
- Citations: **quote the PDFs in `papers/`**; never write a claim about a paper, or a bib entry, from memory. If a
  paper is not in `papers/`, say so to the user and leave a `% TODO cite` comment; do not guess.
- Out of scope: anything number-dependent (R2, R3, R8, R12, R13, R19), the sample-read claim, the theory track,
  Lemma 1's instance work, and **§2's closing motivation** (see C.6).

## A. Mechanical

**A.1 The overfull vertical box.** `make check` in `manuscript/` reports a 1 pt overfull vbox on the last pages of
Appendix D (`_j2_ember.tex`) since commit c2fee51. Fix it with the smallest change (e.g., a float placement or a
break), not by cutting text or changing fonts, margins or spacing. Check: `make` and `make check` are clean.

**A.2 The status log.** `docs/status.md`'s session log is past ten entries. Move sessions 66-70 to
`docs/archive/status-log-2026-11-15-s66-70.md` (same format as the other archive files), and add the file to the
list in the header's first paragraph. Move text verbatim; do not edit it.

**A.3 SLURM output names for job arrays.** Array tasks should write `./logs/%x_%A_%a.out`, not share one `%x_%j.out`.
Already right: `5-attacks/adaptive`, `5-attacks/toolkit`, `4-detectors/adversarial-training`. To fix:
`5-attacks/mab-malware/run.sh` (has `--array` but `%x_%j`), and `4-detectors/learned` (its ERDALT part is
submitted as an array by `pipeline/submit.sh`: check whether `submit.sh` passes `--output` and fix it there or in
the header so that the GBDT part and the array part both get sensible names). Also check the rest of `submit.sh`
for arrays submitted with `--array` on the command line. Editing is safe while jobs run (SLURM runs its own copy of a
submitted script), but never edit a script a `bash` process is running.

## B. Code

**B.1 Monotone violations on the scale-up's models.** §5.1 (`manuscript/_f_evaluation.tex`, near line 46, the
comment `% SYNTHETIC, TO VERIFY EXPERIMENTALLY`) predicts a property of the trained monotone detectors. The check
exists: `provexp.models.gbdt.monotone_violations(booster, constraints, tolerance)` (`src/provexp/models/gbdt.py:110`,
with tests). It was meant to be called in `4-detectors/train` before training; training has finished, so add it as
a small read-only step instead:

- a thin command line (in the style of the other `pipeline/` steps; no script imports another, shared code stays in
  `src/provexp/`) that loads each monotone detector of the registry's `scaleup` set with its constraint vector and
  writes the count and largest violation per model to a small JSON/CSV under the artifacts' `6-results` folder;
- a `run.sh` beside it (SLURM header sized to what it uses: one or a few cores, minutes), with an `echo` naming the
  output file, one argument per line;
- add it to `pipeline/README.md`'s map (it confirms §5.1's blue sentence);
- smoke-test it here on the pilot's models if they load; it runs on tigris after the user pulls.

State the hypothesis first (read the comment in `_f_evaluation.tex`). Do not touch the manuscript sentence; that
happens when the result is read.

## C. Manuscript (uncommitted, pending review)

The register is `docs/reviews/2026-11-12-body/meta-review.md` (rows R4, R5, R15, R21 near lines 385-394; the
earlier table at lines 170-176 has more detail on R4, R5, R15). Triage verdicts: `.../rebuttal/triage.md`. Each fix
is a sentence or a short paragraph, not a new subsection. Keep cited work in its authors' own terms.

**C.1 R4: claims about a class, shown on one instance.** Scope the claims that rest on the experiment to "on EMBER"
where they are not already. Replace §2's "for a broad class of feature mappings" (`_c_background.tex`, around line
79) with a scoped wording. Name once what falls outside the class: features that depend on order, learned
embeddings, and models that read raw bytes. Check first what session 53b's R17 fix already says (§3, after the
definitions: any mapping fits with one whole-input item; the results are informative when items are local) and do
not repeat it.

**C.2 R5: Pierazzi et al.** (`papers/pierazzi2020intriguing.pdf`). Where §2 paraphrases that side effects "cannot be
computed in advance", give their reason (the side-effect feature vector Γ "cannot be expressed analytically in
closed-form", p. 1336). Credit their estimate of a gadget's side effects by injecting it into a minimal app as the
closest precedent of Proposition 1, which computes them exactly per host (they note the effects can differ from host
to host, pp. 1336, 1340). Cite the TOPS 2025 version if it exists in `papers/` or the bib; otherwise tell the user.
Respect `credit-without-diminishing`: credit the precedent without conceding the result.

**C.3 R15: the attacker named.** Name the attacker the threat model covers: binary only, structural edits, no
recompilation, packing or code rewriting. Reword the exclusion of code-level edits so it is accurate against Lucas et
al. 2021 (`papers/lucas2021malware.pdf`; reviewer C-W4 contested the current wording; find it in
`reviewer-C.md`). The exclusions themselves are settled; this is wording only. Do not frame anything around packing
as motivation.

**C.4 R21: prior work.** (a) Attribute the byte budget to the released code it comes from (see the register).
(b) A short paragraph in related work (`_g_related_work.tex`) on certified defenses for malware detectors: they
bound byte edits or a feature-space radius; our edits are unbounded in size but typed. Available: RS-Del
(`huang2023rs.pdf`), DRSM (`saha2024drsm.pdf`); **Gibert et al. and Giri et al. are not in `papers/`**: tell the
user. (c) Cite where they fit: Cortellazzi (`cortellazzi2025intriguing.pdf`), Kantchelian et al.
(`kantchelian2016evasion.pdf`) and Calzavara et al. (verification of the model, not the extractor), Lucas et al. 2024
(`lucas2024training.pdf`), Tsingenopoulos et al. (`tsingenopoulos2024train.pdf`). Check `main.bib` for existing keys
before adding entries; build new entries from the PDFs' own front matter.

**C.5 The review passes.** After C.1-C.4, and separately on §3.3's Lemma 1 (*Closure*), the readout rule and Table 1
(`_d_framework.tex`; proofs in `_j_proofs.tex`): run `humanistic-paper-review`, apply the findings, `make` and `make
check`. The user reads §3.3 only after this. Report what changed per finding.

**C.6 Not now: §2's closing and contribution 4.** §2's closing says §5 "uses them to attack malware detectors and to
build robust ones", while in §5 the attack is an instrument; `docs/paper-mock.md`'s contribution 4 is stale ("four
to six points", "learned constraints"). **Do not edit either.** The user wants to discuss and brainstorm the
motivation first. At most, prepare a short note for that discussion: the current sentences quoted, what §5 actually
shows (its three findings), and the mismatch, without proposing rewrites unless asked.

## At the end

Update `docs/status.md` (a short session-log entry; what is uncommitted and waiting for the user's review) and
commit the docs change.
