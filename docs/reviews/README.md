# Reviews

Simulated reviews of the manuscript and their follow-ups, newest first. Each review is named
`<YYYY-MM-DD>-<stage>.md` (from 2026-11-12 on, a folder `<YYYY-MM-DD>-<stage>/` with one file per reviewer and the
meta-review). `review-prompt.md` is the runbook of the reusable procedure (independent reviewers, then a meta-reviewer;
configuration, prompts and launcher in `process/`). Update `process/note-to-reviewers.md` and `process/checklist.md`
before every run.

**Next review:** the full review of the body, designed in session 47 (2026-11-12), run in the session after; its
output decides what the full-scale run includes (PLAN.md, next steps 2-3).

## Feature provenance (current direction, since 2026-10-22)

| File | Date | What it reviews | Outcome |
|---|---|---|---|
| [2026-11-12-body/rebuttal/triage.md](2026-11-12-body/rebuttal/triage.md) | from 2026-11-13 | The 2026-11-12 register: a triage of every item, drafts for the groups the user picks (`process/run_rebuttal.sh`), the user's decisions (`docs/reviews/rebuttal-prompt.md`) | Triage to be run (R7 has a draft from the first design); the table holds each verdict and decision |
| [2026-11-12-body/meta-review.md](2026-11-12-body/meta-review.md) | 2026-11-12 | Body-only draft at commit 82eea08 (§2-6, App. A-D): four independent reviewers (A formal methods, B adversarial malware, C robust ML, D systems security), then a meta-review with full access | Weak accept / Weak reject / Weak reject / Weak accept; top risks R7 (routing around the population: one data-directory entry past the end leaves it), R1 (attacks below published strength; header-field edits never used by the adaptive attack), R2 (premises tested, not proven); register R1-R21; what the full-scale run must include |
| [2026-11-04-strategy.md](2026-11-04-strategy.md) | 2026-11-04 | Strategy, not prose: strongest claim, 2025-26 literature (ERDALT, Zainab et al. 2026), weaknesses W1-W3 | Recommends: diagnose the 1,060 two-sided features, strong attacks (budgeted adaptive search, MAB-Malware), fix the ERDALT portrayal; introduction waits |
| [2026-11-02-body.md](2026-11-02-body.md) | 2026-11-02 | Body-only draft: Sections 3-5 and Appendix A | Weak reject / Weak reject / Weak accept; risk register R1-R16. Triaged 2026-11-02: three-tier plan in `PLAN.md`; premises checked in `docs/status.md` (2 of 8 toolkit attacks out of catalogue, not 5; P2 answered) |

## Explanation provenance (abandoned 2026-10-22; for reference only)

These review the old manuscript. Do not read them when reviewing the current draft: they would only mislead.

| File | Date | What it reviews |
|---|---|---|
| [explanation-provenance/2026-10-21-ccs.md](explanation-provenance/2026-10-21-ccs.md) | 2026-10-21 | Simulated CCS review of the full old manuscript (weak reject; the user judged it a strong reject, which led to the restart) |
| [explanation-provenance/2026-10-19-reassessment.md](explanation-provenance/2026-10-19-reassessment.md) | 2026-10-19 | The 2026-10-16 review reassessed against the revised manuscript and plan |
| [explanation-provenance/2026-10-16-ccs.md](explanation-provenance/2026-10-16-ccs.md) | 2026-10-16 | Pre-submission simulated CCS review (formerly `REVIEW.md`) |
| [explanation-provenance/2026-10-14-sections-3-5.md](explanation-provenance/2026-10-14-sections-3-5.md) | 2026-10-14 | Self-review of old Sections 3-5 |
| [explanation-provenance/2026-10-14-self-review.md](explanation-provenance/2026-10-14-self-review.md) | 2026-10-14 | Self-review of the old draft (W1: thin technical novelty) |
