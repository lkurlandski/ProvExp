# Resume: does §3.3 belong in the framework? (ProvExp, writing + research decision)

Paste this into a fresh session. It is a **dedicated analysis session**: decide what to do with §3.3 ("Edits Given
as Writes") and, if the answer is a restructuring, plan the new structure. **No manuscript edits in this session**
unless the user approves a plan at the end. Written 2026-11-08 at the end of session 19.

## Why this session exists

The §3 review sprint (`docs/sprint-framework-review.md`) reached §3.3 and stalled. Two rounds of revision failed:

- Round 1 (simulated review P1-P22, ten-paragraph spine, rewritten): the user "became confused very early on" and
  gave up at Definition 7 ("after about five minutes ... I've given up"). Comments U1-U18 in the log.
- Round 2, items 1-4 only (lead, Def 7 written set, Algorithm 2 with "located" records and "scanned" tokens,
  structure positions and margins, the three cases, Def 8 local kinds; commit `61eb5fa`): the user stopped after the
  first paragraph and questioned the subsection itself. Their points, in their words where possible:
  - It "adds/considers an additional property to the sum-then-readout extractor (the way it finds elements) and then
    tries to formally model this behavior", and that behavior "feels very specific to or oriented toward PE files (or
    executable file formats more broadly)". "The goal of the research is to provide a general-purpose and powerful
    framework for understanding any objects. If all we're doing is providing a formalized description of EMBER
    features for PE files, then we've failed."
  - "Locates" appears nowhere else in the framework.
  - The motivation was "because we need it for the next subsection": "Every subsection should be able to stand on its
    own. If a subsection doesn't provide any value or do anything important by itself, then it doesn't really deserve
    to exist."
  - The located/scanned distinction "made no sense". The whole read as "soup", "pointless formalization of something
    completely unimportant".
  - But also: "I hope that I'm wrong about this and that my criticism just comes down to poor presentation on your
    part and misunderstanding on mine."

Claude's position at the end of session 19 (to be tested here, not assumed):

- Partly right: as a subsection, §3.3 has no standalone value (for a single write, re-extraction is exact and cheap;
  its only use is giving §3.4 the signatures of operations given as writes), and introducing it through *how an
  extractor parses* (located vs scanned, a header with counts and offsets) reopens what §3.1 keeps out (only $\pi$
  depends on the format) and reads as executable parsing.
- Partly wrong: the idea is load-bearing for the evaluation and not PE-specific. §5's strongest result (the derived
  direction table corrects the hand rules; every disagreement is the hand rule's error, witnessed) rests on it: e.g.,
  appending to a file whose section table points past its truncated end makes the appended bytes a section's raw
  data, found by "an interval query of the written positions against the recorded locating positions, with no rule
  written for this case" (`manuscript/_f_evaluation.tex`, ~lines 84-91 and 150-160; also the "Flagged" column of the
  side-effect table, ~line 44-76). Any format where content says where other content lies has the same issue (length
  fields in packets; offsets in PDF xref, ZIP directories, DEX tables); text-like formats (n-grams, tokens) are the
  easy case. The question worth asking: *which items can "write anything here" change, on this input, without trying
  any content?*
- Options proposed: **A** drop §3.3, signatures become a pure input of §3.4 (risk: §5's headline rests on an unstated
  method; "how was the append signature derived, and why is it sound?"); **B** (recommended then) fold one paragraph
  into §3.4 on where the signature of a write-given operation comes from, with Def/Lemma in the appendix; **C** keep a
  short subsection built on the question above.

The user wants a deep analysis before deciding, thinking "carefully about the research more broadly as well as how
we'll want to present and document our experiments". If major restructuring is best, plan it; **hopefully nothing in
§3.1 and §3.2 changes** (both were accepted after review).

## What to do

1. **Read, in order** (do not skim the user's reactions; they are the main constraint):
   - `CLAUDE.md`, `PLAN.md`, `docs/status.md` (session-19 block), `docs/paper-mock.md` (thesis, contributions,
     outline, tables: what the paper claims and what supports it).
   - `docs/sprint-framework-review.md`: the §3.3 section entire (P1-P22, U1-U18, the classification, round 2, the
     user's last reaction), and the §3.2 retro. `.claude/skills/paper-prose/reader-model.md`.
   - The manuscript as it stands: `manuscript/_c_background.tex` (§2), `manuscript/_d_framework.tex` (§3; §3.3 is
     half round-2: items 1-4 new, the rest round-1 below the `% ROUND 2` comment), `manuscript/_j_proofs.tex`,
     `manuscript/_e_instances.tex` (§4, where "locating positions" and margins are described for EMBER),
     `manuscript/_f_evaluation.tex` (§5: the side-effect table with its Flagged column, the direction table vs hand
     rules and its disagreements), `manuscript/_g_related_work.tex` (incremental parsing, ~line 94).
   - The design record: `docs/framework-design.md` (Sections 1-5 and 13: why §3.3 exists, its spine and decisions
     Q1-Q4), `docs/formalization.md` (frozen; the three example domains EMBER, Drebin, CICFlowMeter, and its
     Requirement 4 on margins), `docs/item-layer-design.md` (the automatic derivation), `docs/direction-A-summary.md`.
   - Older reactions to the same material in `docs/writing-spec.md`'s reaction log (2026-11-05: "identity" as
     "wet clay" and "a leaky abstraction"; locating positions "the same thing as identity again; boring, overblown";
     "honest tools"; "an unhinged rant"). The concept has now failed with the user in three framings (identity,
     locating positions, structure positions/margins): weigh that.
2. **Analyze** (reason from the documents; this is a conceptual decision, do not run experiments or data):
   - **Which results in the paper rest on §3.3's machinery?** For each table and claim in §5 (and the paper mock's
     contributions), say whether it needs structure positions, margins, flagging, or Lemma 1, and what it would
     rest on under each option. Separate "needed for soundness" from "needed for the side-effect predictions of
     element-stated edits" from "presentation only".
   - **Generality, honestly.** Does the concept apply as stated to Drebin and CICFlowMeter (the formalization's other
     domains), and to text-like features? Where is it essential, where trivial? Is it a property of the extractor at
     the level of the framework (like sums and readouts), or of one instance's instrumentation? Be harsh: the user's
     test is "general-purpose and powerful framework for understanding any objects".
   - **Standalone value.** Can the material be stated so that it does something by itself (the user's criterion), for
     example as a result about which items an operation can change on an input without trying any content, with the
     append-past-the-end case (written generically) as the motivating surprise? Or is it inherently a supporting
     lemma, which belongs in an appendix or in §4?
   - **The realistic alternative** (`CLAUDE.md`: each application must cross the gap in a way only provenance makes
     cheap): without it, who writes the signature of "append anything" and how do they know it is sound? Is the
     hand-signature alternative realistic, and what did the hand rules get wrong (§5)?
   - **Options A, B, C, and any better one** (e.g., stating signatures as an input with a soundness condition in §3.4
     and moving the localization to §4 as the instance's way of meeting it; or an abstract "dependency" formulation
     that never mentions parsing). For each: what the body says, what moves to the appendix or §4, what §3.4 and §5
     must change, word cost, risk with reviewers, risk with the user (the concept's three failed framings).
   - **Presentation and documentation of the experiments** (the user asked for this explicitly): how §4 and §5
     present the instrumentation, the flags, and the derived-vs-hand comparison under the chosen option; what a
     reader must know from §3 to read §5.
   - Keep §3.1 and §3.2 unchanged if at all possible; if a change there is unavoidable, say exactly what and why.
3. **Write the analysis** to `docs/s33-decision.md`: a plain-language summary first (what §3.3 is for, whether it
   earns its place, the recommendation), then the analysis above, the options compared, one recommendation, and, if
   it restructures, a **new structure for §3 after §3.2** (subsections, each with its formal endpoint, its single
   job, and why it stands on its own; then a paragraph spine for whatever replaces §3.3, the ripples into §3.4,
   the appendix, §4, §5, the symbol table, and the §3 lead), with open questions last. Follow `/paper-prose` lessons
   32-33 and "Explain plainly"; apply the staging scan to your own sentences.
4. **Present it to the user** in the chat: the plain summary, the recommendation, and the questions. Discuss. Do not
   edit the manuscript until the user approves a plan.

## Working rules that matter here

- Be self-critical about our own contribution and about Claude's earlier recommendation (option B); the user hopes
  they are wrong, so do not tell them what they hope to hear, and do not tell them the opposite to seem rigorous.
  Ground every claim about what the paper needs in the text of §4/§5 and the paper mock.
- The framework must stay as agnostic as Pierazzi et al.'s; PE specifics only in experiments (`CLAUDE.md`, framework
  conventions). Keep machinery simple (memory: constrain experiment complexity; consistency and simplicity).
- `_e_instances.tex` and `_f_evaluation.tex` belong to the research track: propose changes to them in the analysis,
  but do not edit them.
- Commit only your own files (`git status` first; `tmp.txt` and `tmp/` are the user's). Do not push.
- At the end: update `docs/status.md`, `PLAN.md` (sprint position), `docs/resume-prompt-review.md` ("Current
  position"), and the §3.3 section of `docs/sprint-framework-review.md` with the decision.
