# Resume: §5's rewrite as three findings (plan agreed in session 30)

Read `docs/status.md` and `PLAN.md` (decision 10 above all; also 2, 3, 6; next step 3). The plan for §5, one line per
paragraph, the checks C1-C3, the drafting order, and the framing's known weaknesses are in `docs/paper-mock.md`, §5.
The structure is agreed with the user: do not reopen it. Write the prose from that plan.

**The framing in one paragraph.** §5 tests §2's claim that practitioners learn what edits do by trial, by reading the
extractor, or from observed attacks, and that each falls short. Three findings, each stated with a number: what hand
analysis misses (5.2), what observed attacks miss (5.3), what robustness costs (5.4). The adaptive search and the
monotone detectors are instruments, not the contribution. Not a validation section (the correctness check is two or
three sentences in 5.1; the side-effect table goes to Appendix D) and not a defense paper: no state-of-the-art defense
claim, and never call the detectors' cost "small" or "cheap" (memory `findings-not-defense-paper`). Claims say "on
EMBER".

**Order of work.**
1. Block 1: the lead and 5.1, and the side-effect table with a short paragraph moved into Appendix D (`sec:ember`).
2. Check C1 (side-effect breadth from the correctness runs' outputs) and C3 (published hand classifications of EMBER's
   features; verify before claiming), then block 2: 5.2.
3. Check C2 (share of the lowerable features any toolkit output lowered), then block 3: 5.3 with the new audit table.
4. Block 4: 5.4 with the detector table trimmed to the undefended, monotone, and additions rows.
5. §2's closing sentence and contribution 4 of the mock, re-read against the findings.

State a hypothesis before each check and report a failed one as such; the checks count existing outputs and must stay
under ~10 minutes (otherwise estimate and ask). Use the `paper-prose` skill; draft in blocks with `make` and
`make check`, shown as rendered text, with the user's review after each block.

Constraints carried over: no timing of Prop. 1 against extraction (memory `no-timing-claims`); check
`manuscript/main.aux` before naming a table or section number (the side-effect table's move renumbers Tables 4-5);
§5 ~3,200 words (50-75% over allowed while drafting).

Then: shorten §4 and §5 together (§4 ~1,540 words against ~1,000; §4.3 first), then PLAN.md step 4 (the review prompt,
the full simulated review, the truncation brainstorm).
