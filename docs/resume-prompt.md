# Resume: ProvExp (2026-10-13, evening) — manuscript writing

Read `CLAUDE.md`, then `docs/status.md` ("Where we are", "Next", and the 2026-10-13 decisions). This session is for
**deep thinking and manuscript writing**, not tooling: the LaTeX toolchain and template are settled (below); do not
spend time on them beyond `make` / `make check`.

**Goal:** a complete rough draft of the paper for **ACM CCS 2027, Cycle A** (CfP not out; by CCS 2026, abstract
~Jan 7 and paper ~Jan 14, 2027). Then decide on the scale-up.

## Where things stand

- **Research:** framework and intrinsic evaluation (CP, PB1, PF1, PB2/PF2) done at pilot scale. Both applications
  done and written up: **CM**, the pullback comparing a GBDT and MalConv per file (`docs/experiments/cm.md`); **AU**,
  the pushforward auditing MalConv across a corpus (`docs/experiments/audit.md`; 9/20 features confirmed, scrambling
  their bytes evades 22.5% of detected malware at 1% FPR).
- **Manuscript** (`manuscript/`, `main.tex` + section fragments):
  - written: introduction (`_b`, rewritten 2026-10-13: key insight, framework+symmetry framing, contributions C1-C4),
    framework (`_c`), evaluation/applications (`_d`), **related work** (`_d2_related_work.tex`, drafted 2026-10-13:
    propagation/G-DeepSHAP, malware XAI/FINER/Mohseni, feature-to-binary mapping by hand, multi-detector, shortcuts
    and planted triggers, provenance terminology).
  - missing: **abstract** (`_a` still holds the old dissertation-chapter bridge), **discussion/limitations** (`_e`),
    **summary/conclusion** (`_f`), a findable **threat/system model**, and the **Ethical Considerations** and
    **Open Science** appendices (empty headings in `main.tex`, after the bibliography as CCS requires).
  - still in **dissertation-chapter voice** ("this chapter", research questions Q1-Q3, an internal experiments/status
    table in `_d`, "Symbols used in this chapter" table, section titles like "Evaluation on Malware Detection",
    "Summary"). Needs the chapter->paper pass.
  - **Length: the body currently runs to page 14** (references start p. 14; 16 pp total) against CCS's **12-page**
    body limit, before the missing sections are written. Cutting ~2-3 pages is part of the conversion (candidates to
    discuss with the user, not to cut unilaterally: the status table, PB2/PF2 (demoted), the research questions,
    parts of `_c`'s theory to the appendix).
- **Build:** `cd manuscript && make` (also `make watch`, `make check`, `make clean`). ACM `acmart` `sigconf`,
  `anonymous`, `acmthm=false` (the fragments define their own `\definition`/`\theorem`/`\proposition` headers). Do not
  change fonts, margins, or spacing (CfP). CCS-specific copyright/DOI/ISBN are TODO until the CCS '27 template exists.

## Next steps (in order)

1. **Abstract** (five moves, >= 2 numbers), **discussion/limitations**, **conclusion**, **threat/system model**,
   **ethics** and **open science** appendices, in paper voice. Use the `security-paper-writing` skill.
2. **Chapter->paper pass:** voice, structure toward the security-paper skeleton, the 12-page body; check every
   contribution bullet (C1-C4) maps to a section and to evidence that has actually been run.
3. **Then the scale-up** (only once the draft convinces us the plan is solid, and when the user decides): 2,000 files,
   seeds 0-2; ~48 h on 16 cores plus GPU time for MalConv's IG and any AU retrain.

## Open decision for the user

- **CCS Cycle A (~mid-Jan) vs. Cycle B (~late April).** A Cycle A reject cannot go to Cycle B. The plan says Cycle A;
  Cycle B buys three months for the load-bearing pieces below.

## Commitments from "claim the fuller vision" (user, 2026-10-13)

The introduction's contributions were written toward the complete story, which makes three currently-deferred pieces
**load-bearing before submission**: AU's **mitigation** (test-time field zeroing + a retrain), CM's **real-attack
transfer**, and the **scale-up**. Track these; do not let the intro overclaim relative to what is run.

Explain in plain language; no dense shorthand. Ask before changing what a claim is for.
