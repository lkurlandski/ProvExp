# Experiments: what we might reconsider or change, and why

Started 2026-11-24 (session 106, experiments track) at the user's request, by combing the documentation for aspects of
the experiments already flagged as worth revisiting. Each entry says what the aspect is, why it may need to change, the
options on record, its status, and where the record lives. It is a register of candidates, not of decisions: when the
user schedules one for a rerun, it also goes on the **next-round list** at the end of `docs/scaleup-protocol.md`
(changes are applied together in one full rerun, never one by one; user, session 105). Add new entries here as they
come up; mark an entry when it is decided, applied, or dropped rather than deleting it.

Status words: **open** (nobody has decided), **next round** (on the next-round list), **candidate** (the user's call,
on the next-round list as a candidate), **deferred** (approved or wanted, waits for something), **settled** (decided;
kept here because the decision has a known cost someone may want to revisit).

## 1. The attacks

**1.1 The GAMMA section attack skips a quarter of the files at the literature budget.** *Open; accepted for this round
(user, session 106).* GAMMA's section attack writes one new section header per donor section on every query (it
injects all donors, even those whose weight is zero; `docs/upstream-issues.md`, item 7). At the GAMMA paper's budget
(75 donors, protocol item (22)), many files' headers cannot hold 75 more, even after growing them, so the attack is not
applicable to them: 2,457 of 10,000 training malware in the session-105 material, against 126 at 30 donors (where 192
of 1,000 test malware already lacked room). Where it runs it evades little: 51 of 7,533 outputs (0.7%), against 1.5%
at the old budget, so the larger budget did not make it stronger, as we had expected. *Why reconsider:* the attack is
reported on a different, smaller set of files than every other attack, and the budget we adopted to be faithful to the
literature is the reason. *Options on record* (weighed in session 103, `docs/evidence/gamma-lief-relayout.md`): keep
it not applicable (chosen); write only the donors that fit; use fewer donors for this attack; fall back to LIEF's
rebuild (rejected then: it relayouts the file, outside the threat model); a new operation that makes room (e.g. growing
the last section). A further option from the upstream note: let the attack skip donors whose slice is empty, so it can
choose how many sections to add (a change to the published attack, so it would need saying).

**1.2 The GAMMA import attack is not applicable to 114 of the 1,000 test malware.** *Open, not planned (user, session
103).* Same cause: no room for one more section header even after growth. The only way to recover these files is an
operation that reaches files with no header room (e.g. growing the last section). Source: `docs/status.md`, session
103; resume prompt, "Noted for later".

**1.3 Drop the toolkit attacks that stay ineffective at a generous budget.** *Next round.* The five byte-level attacks
(DOS extension, content shift, padding, format exploit, header fields) barely move a feature-based GBDT; they were built
for byte-level models (checked against secml-malware's MalConv: they evade 16, 14, 9, 6 and 5 of 20 there). They stay
in this round, in an appendix, and are dropped before the final submission (protocol item (22)(c)). *To decide:* the
criterion for "ineffective". *Knock-on:* the learned defenses' training material changes with them, so PV, ERDALT and
adversarial training must be retrained. Related: these attacks stop early once their search stagnates, so the larger
budget barely changes them (smoke: same run time); one sentence where the paper states the budget.

**1.4 The adaptive search without signature cloning.** *Next round, optional.* 888 of its 932 evasions of the
unconstrained detector clone a signature (`ent`'s clone candidate). Expected (decisions.md, around line 208), but it
makes the result look like one trick. A run without the clone candidate would show what the search achieves otherwise.

**1.5 MAB-Malware against the official EMBER2024 model.** *Next round, optional.* At Zainab et al.'s setting ours
evades 52% (455 of 867) against their 83.4%. Accepted (user, session 105): their detector (the official model) and
their malware (files all eight of their models detect, checked for executability in Cuckoo) differ from ours, and code
randomization is not the cause. Running MAB-Malware against the official model on our test malware would separate the
detector's effect from the malware's.

**1.6 Outputs over 4 MB are discarded.** *Open, check when reading.* The rule "an output counts only if it is at most
4,000,000 bytes" (protocol item (22)(b)) removed 2,001 of the material's 76,049 outputs, all from the three GAMMA
attacks (7-8% of theirs). *Why look:* larger outputs carry more added content and may be the more evasive ones, so the
rule could weaken GAMMA selectively. Worth a count of how many discarded outputs would have evaded before deciding
whether the rule needs a sentence or a change.

**1.7 Code-level transformations are excluded.** *Settled (decision 9); do not re-propose unless the user reopens it
or a reviewer raises it.* MAB-Malware's code randomization, IPR and Disp, MalGuise's call-based redividing are outside
the threat model and the experiments; stated as a limitation. The cheap first step, if reopened: the pilot's direction
table with an in-place code-write operation, then retraining the detectors if the directions change.

## 2. The detectors

**2.1 The hand-table detector at scale.** *Candidate (session 108, the user's call).* §5.2's *What the error costs*
rests on the pilot only (10 of 29 lowered, none crossing). Either train and attack it at scale, or keep the pilot
result with the user's approval (memory: every paper number gets a scale-up step).

**2.2 The hand table extended to all fourteen operations.** *Open (user, session 106).* The hand table lacks the entry
write and header growth, while §5.2 says "each of the fourteen operations". Extend it and check whether its errors
(Table 3) change.

**2.3 A monotone-sums detector for the *shifts* threat model.** *Candidate, deferred (user, session 108).* The
derivation already computes the *shifts* table and the adaptive search accepts `--threat_model M_shift`; no detector
is trained or attacked. It would give §5.4's width-of-the-threat-model paragraph a middle point between additions and
full, and it is the threat model GAMMA's attacks need. Used in the paper only if implemented and run
(`docs/evaluation-note.md`, decision 6).

**2.4 More defense baselines.** *Open (user, session 108: very likely later, body or appendix undecided).* Three
learned defenses are too few for a state-of-the-art defense claim (the user would want at least six; decisions.md,
decision 10). §5 is organized so that a new defense is one row in its group (`docs/evaluation-note.md`, section 6).
Any borrowed defense is ported for its effect, not its letter (CLAUDE.md: tabulate their setup against ours first).

**2.5 ERDALT does not meet its own criterion.** *Settled (user, session 100).* Retrained with every setting rescaled
to Gimenez et al.'s setup: validation AUC 0.978, test 0.981, but 35,594 monotonicity violations against the rescaled
criterion of 381. Their literal penalty weight gives 769 violations at AUC 0.914. Kept as is; Appendix D states the
trade-off. Record: `docs/erdalt-diagnosis-plan.md` (open: move it under `docs/evidence/`).

**2.6 The certificate entry is writable (signature cloning inside the threat model).** *Settled (user; decision 11, R7,
session 48); alternative recorded.* Widening the population for the certificate and debug entries cost the monotone detectors about
4 points of TPR at 1% FPR (89.6 -> 85.7 for sums), almost all from the certificate entry. *Alternative not taken:*
widen for the debug entry only (0.1-0.6 points) and leave signature cloning outside the threat model as a stated
limitation (decisions.md, decision 11).

## 3. Validity, the population and the extractor

**3.1 Extractor quirks the validity rule exposes.** *Open, decide when reading this round.* Outputs rejected by pefile
alone ("pefile only": 21 in this round's material) point at parser quirks, e.g. pefile's 8,192-import cap. List them
from `invalid.parquet` and decide with the user which to patch (CLAUDE.md: no result may rest on an extractor quirk).

**3.2 Whether Windows loads the outputs is not checked.** *Open.* The validity rule is parser-based (pefile and LIEF
both read the output and lose no section, DLL or import). Not checked: whether Windows loads a file whose section
table runs past SizeOfHeaders (the population's fifth clause does not depend on it), or GAMMA's consecutive empty
sections at one RVA. Zainab et al. checked executability dynamically (Cuckoo); we do not.

**3.3 The extractor's design.** *Settled for now (session 62: stay on pefile); open in principle.* Our deviations from
EMBER-v3: files below 4 MB, warnings dropped, thrember quirks patched, LIEF's overlay rule. Designing the extractor
deliberately (perhaps on LIEF) remains possible (CLAUDE.md; PLAN.md step 2c).

## 4. Scale and protocol

**4.1 One seed.** *Deferred until the methodology is final* (protocol, item at line ~63). The scale-up uses seed 0
only; compute went to more files instead of seeds 0-2. The final submission reruns everything, which is when seeds
would be added.

**4.2 PV's usable features against sample size.** *Deferred, approved (user, session 85); run after this round.* An
appendix experiment explaining why PV works less well than prior work suggests: PV drops a feature once any output
lowers it, so the more training malware it sees, the fewer features it keeps (~1,450 kept at 100 files, 201 at
10,000; Gimenez et al. built from ~1,033 vectors). Design: protocol item (17).

**4.3 The not-applicable rows in the result tables.** *Open, check when reading.* `scaleup_tables.py` joins a job's
`room_check.parquet` names with every defense row of the attack, although a defense attacks only the files it detects;
the not-applicable counts per detector may be overstated.

**4.4 A budget curve for the bounds-on-size theory.** *Open, the user's call (theory track).* At the paper's budget
nothing can be shown on EMBER for bounds on size; a curve over smaller budgets would be a new experiment
(`docs/resume-prompt-theory.md`; `docs/evidence/theory-analysis.md`, parts G and H).

**4.5 Checks from the theory follow-ups.** *Open (PLAN.md step 8 (c)).* `monotone_violations` called in
`4-detectors/train`, so that §5.1's predicted sentence (proof note 5) is confirmed or reworded; optionally the tighter
rule for a normalized bin in `reach.py` (the current one is sound but looser).

**4.6 A second domain.** *The user's call, with this round's results in hand (PLAN.md step 6).* One instance is the
largest open risk to the paper's claims of generality.
