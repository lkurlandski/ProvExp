# Resume: ProvExp (after 2026-11-02): write the framework section in `.tex`

## Where we are

- **The paper is planned** in `docs/paper-mock.md`:
  - a thesis and four contributions;
  - an outline with word budgets: the body is about 9,500 words, the framework section 2,500;
  - Tables 1-4, with EMBER cells measured at pilot scale and CTU-13 cells missing.
- **The formal model** is in `docs/formalization.md` (revision 5, 13,100 words). It is **frozen** as the reference and
  appendix source. It is *not* a draft: it mixes paper text, appendix proofs, and project notes, and the user called
  it sprawling. Do not edit it except to fix facts, and do not write its Section 10.
- **Settled, do not reopen:**
  - The domain is adversarial examples in practical security tasks.
  - The framework is as agnostic as Pierazzi et al.'s.
  - PE malware is the inspiration and main instance; other domains are breadth.
  - Paper text goes straight into `.tex`; no markdown drafts of paper text.

## The work this session: the framework section, to 2,500 words

1. **Set up the file.**
   - Create `manuscript/_c_framework.tex`.
   - In `manuscript/main.tex`, replace Section 3 (`\section{Transferring Explanations with Provenance}`, which inputs
     the old `_c_method.tex`) with the new section, under a working title such as "Computing What Edits Do to
     Features".
   - Leave `_c_method.tex` on disk, and leave every other section untouched. They belong to the old direction and get
     rewritten later; an inconsistent PDF is fine for now.
2. **Write the section** from `docs/formalization.md`, Sections 1 and 3-7, to the mock's budget per part:

   | Part | Words |
   |---|---|
   | The problem and notation (Pierazzi et al.'s symbols: $Z$, $\varphi$, $\mathcal{T}$, $\Gamma \vdash \Omega$, $\delta^*$, $\eta$) | 300 |
   | Items, sums, and readouts: the term table, the readout table, one cross-domain table (PE/EMBER, APK/Drebin, traffic/CICFlowMeter) | 700 |
   | Edits, item deltas, and the four edit classes | 300 |
   | The two-step recipe; the five requirements as one compact list; Theorem 1 (exact side effects) | 600 |
   | Sign envelopes; the per-readout rules; Theorem 2 (sound directions) | 500 |
   | Robustness, as a corollary of Gimenez et al.'s result | 100 |

   - **Examples:** one running PE example (append `\0http://evil.example`), plus the traffic example only where it adds
     something (the longest gap after an injected packet, which shows why maxima need the item table).
   - **Proofs:** none in the body. Give each theorem a one-line proof idea and point to the appendix.
3. **Appendix, if the body is done:** a new appendix file with the proofs and the smaller lemmas (hashed keys,
   patterns under extension), taken from the formalization. Keep the EMBER checks and caveats out of it; they go to
   the instances and evaluation sections later.
4. **Citations.** Check `manuscript/main.bib` for the keys the section needs, and add missing ones with correct
   metadata:
   - Pierazzi et al. (S&P 2020); Gimenez et al.; Incer et al.; Demontis et al.;
   - Severi et al.; Chen et al. (CCS 2021);
   - Gray et al. (data cube); Wagner and Graham (incremental parsing);
   - Arp et al. (Drebin); Sharafaldin et al. (CICFlowMeter / CIC-IDS2017); Engelen et al.;
   - Chernikova and Oprea (FENCE); Simonetto et al.
5. **Build and measure.** Run `make` and `make check` in `manuscript/`. Report the word count against the budget (e.g.
   `texcount`, if it is installed, or `detex | wc -w`). Then show the user the section.

## How to write it

- **Paper prose, not notes.** Continuous prose, no stacks of labeled paragraphs, no internal IDs (no C1/A0/G7, no "formerly"), no revision history, no caveats lists. Present what works; keep limitations light (one sentence pointing to the discussion).
- **Plain first.** Each part opens with its question and the example, then the definition, then the result. Define every symbol. Name features in plain words.
- **No format in the framework.** PE details only inside the running example; the requirements are stated generally.
- Do not change fonts, margins, or spacing (ACM `acmart` `sigconf`).
- If a part runs over budget, cut. Do not add a subsection the mock does not list. Flag overruns early rather than at
  the end.

## Read first

- `CLAUDE.md`
- `docs/paper-mock.md`, in full
- `docs/status.md`, the top block
- `docs/formalization.md`: Sections 1 and 3-7 (the source), and the notation table

## After this session

- Next: the CTU-13 instance. First, find out what the MoEvA2 replication package ships (the raw-to-feature pipeline,
  or only feature vectors). Then A's gaps.
- Open decisions for the user: Drebin as an instance (default: examples only); the coupling row (default: out).
- At the end: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.

## Notes

- Untracked, leave alone: `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`,
  `slides/`.
- Local PDFs in `papers/`: Pierazzi et al., Gimenez et al., Incer et al., Severi et al., Simonetto et al., Dyrmishi et
  al., Demontis et al. (`pdftotext` works on them).
- The user still owes the upstream reports in `docs/upstream-issues.md`.
