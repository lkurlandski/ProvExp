# Resume: ProvExp (2026-10-13, after lunch)

Read `CLAUDE.md`, then `docs/status.md` ("Where we are", "Next", and the 2026-10-13 decisions). Current goal:
**finish a rough draft of the manuscript, then kick off a larger-scale set of experiments.**

## Where things stand

- Framework and intrinsic evaluation (CP, PB1, PF1, PB2/PF2) done at pilot scale.
- Both extrinsic applications done and written up: **CM**, the pullback comparing two detectors per file
  (`docs/experiments/cm.md`); **AU**, the pushforward auditing MalConv across a corpus (`docs/experiments/audit.md`).
  AU scrambles the bytes P names for the features MalConv rests on (9/20 confirmed, 22.5% evasion at 1% FPR) and
  compares the two detectors globally in feature space.
- **Manuscript** (`manuscript/`): the framework (`_c`) and applications (`_d`) sections are written; the
  **introduction (`_b`) was just rewritten** (key-insight sentence, framework+symmetry framing, contributions
  C1-C4, G-DeepSHAP `chen2022explaining` cited). Still to write: **related work** (no section file yet; only
  `docs/related_work.md`), **abstract** (`_a` is a one-line chapter bridge), **discussion** (`_e`) and **summary**
  (`_f`) are placeholders. The document is still written as a **dissertation chapter**; it needs a real
  chapter->paper conversion (voice, structure, plus a findable **threat/system model** and an **ethics/disclosure**
  section) for a USENIX submission.
- **Repository reorganized:** experiment docs merged and moved to `docs/experiments/{cp,pb1,pf1,trigger,cm,audit}.md`;
  dropped threads (3-B, the rule-based audit) archived under `scripts/archive/` and `run/archive/` and summarized in
  `docs/graveyard.md`; the "3-A/3-C" vocabulary retired (CM/AU are canonical).

## LaTeX toolchain (in progress)

- **user-space TeX Live + `latexmk` + `pdflatex`** in `~/texlive` (installed). `cd manuscript && make` builds
  `main.pdf`; `make check` lists undefined refs/citations and overfull boxes. `main.tex` is the complete document
  (placeholder preamble: plain `article`, the colors, `\textlangle`/`\textrangle`, numbered
  `\definition`/`\theorem`/`\proposition` headers, `notationbox`/`proposalbox`), to be replaced by the USENIX template.

## Next steps (in order)

1. ~~Verify the local compile~~ (done 2026-10-13).
2. **Draft the remaining sections in paper (not chapter) voice:** related work (position against G-DeepSHAP
   `chen2022explaining` and FINER `he2023finer`), abstract (five-move, >=2 numbers), discussion/limitations, summary.
   Then add the threat/system model and ethics/disclosure sections. Writing these in paper voice now avoids a second
   rewrite.
3. **Chapter->paper global pass:** voice, structure toward the security-paper skeleton, length (~13 pp USENIX body).
4. **Then scale up** (only once the draft convinces us the plan is solid): all 2,000 files, seeds 0-2. Budget up to
   ~48 h on 16 cores for the CPU work, **plus GPU time** for MalConv's IG (runs 39/45) and any AU retrain. This
   tightens the pilot numbers (especially AU's 22.5% evasion and CM) with seed variance / confidence intervals; it
   does not change the argument.

## Commitments from "claim the fuller vision" (user, 2026-10-13)

The introduction's contributions were written toward the complete story, which makes three currently-deferred pieces
**load-bearing before submission**: AU's **mitigation** (test-time field zeroing + a retrain), CM's **real-attack
transfer**, and the **scale-up**. Track these; do not let the intro overclaim relative to what is run.

Explain in plain language; no dense shorthand. Ask before changing what a claim is for.
