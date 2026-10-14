# Style guide: how top-tier security papers in our area read

A loose orientation for the section-level writing (2026-10-14), not a rulebook. It describes what a sample of
well-cited papers near our scope tend to do, so that our paper feels at home at CCS. It does not prescribe a template:
every pattern below has counterexamples in the sample, and we deviate wherever our material is better served another
way. **Do not borrow wording, section titles, figure designs, or framing devices from these papers**; the goal is the
general feel (pace, density, how claims are staged), not resemblance to any one paper.

## The sample (13 papers, 2020-2023)

Read for structure and voice (abstract, introduction, section headings, threat model, evaluation openers, discussion,
conclusion). Three are arXiv extended versions, so their lengths differ from the proceedings.

| paper | venue | type | why it is near us |
|---|---|---|---|
| Pierazzi et al., problem-space adversarial attacks | S&P 2020 | attack + formalization | feature space vs. problem space, malware |
| Barbero et al., Transcending Transcend | S&P 2022 | method + re-evaluation | malware classifiers, theory then practice |
| Yang et al., Jigsaw Puzzle | S&P 2023 | attack | malware backdoors, realizability |
| Severi et al., explanation-guided backdoors | USENIX 2021 | attack | SHAP on EMBER features, PE realizability |
| Yang et al., CADE | USENIX 2021 | system | explaining drift in malware/NIDS |
| Downing et al., DeepReflect | USENIX 2021 | tool | localizing malicious content in binaries |
| Arp et al., Dos and Don'ts of ML in security | USENIX 2022 | critique/SoK-like | evaluation norms reviewers now apply |
| Chen et al., continuous learning for Android malware | USENIX 2023 | method | malware ML, operational framing |
| Han et al., DeepAID | CCS 2021 | framework | explaining security DL models, applications |
| He et al., FINER | CCS 2023 | framework | feature attribution for malware analysis |
| Dambra et al., ML in Windows malware classification | CCS 2023 | measurement | PE features, static vs. dynamic |
| Warnecke et al., unlearning features and labels | NDSS 2023 | method + guarantees | ML-security method with theory and case studies |
| Kireev et al., adversarial robustness for tabular data | NDSS 2023 | method + threat model | threat model as the conceptual contribution |

Closest in shape to us: DeepAID and FINER (a general explanation method, then security uses), CADE (a method plus an
explanation component evaluated quantitatively and by case study), and Warnecke et al. (a general method, a bit of
theory, then several case studies).

## Overall shape

- **Common skeleton:** Introduction / Background (sometimes with related work) / the idea or method / evaluation /
  discussion with limitations / related work (if not earlier) / conclusion. About two-thirds put related work near
  the end; the rest fold it into background. Either works. Ours is early, which suits a paper whose novelty is best
  seen against prior attribution transfer.
- **The method section is usually shorter than the evaluation.** Evaluation, including case studies, is typically the
  largest part. Methods are introduced with motivation first ("why existing approaches fall short here") and then the
  design, often under a short "insight" or "intuition" heading or sentence.
- **Organization of the evaluation varies.** Some papers number research questions or goals up front (Jigsaw's three
  questions, DeepReflect's four goals, DeepAID, FINER), but most do not; they use descriptive subsection titles that
  say what is being tested. Our choice (no research questions; sections by operator, each going from a controlled check
  to a security task) is within the norm.
- **A setup subsection first.** Data, models, baselines, metrics, and budgets usually come once, before results, so the
  results subsections can stay focused on findings.
- **Case studies are normal and valued** (CADE, Jigsaw, Chen, DeepAID): one or two concrete files or families worked
  through in a paragraph or a small figure make an abstract method tangible. Our applications are where this fits.

## Abstract

- One paragraph, about 170-250 words in the sample (ours is 271: trim).
- Moves, roughly: the setting and why it matters; what is missing; what the paper does and the idea that makes it work;
  what the evaluation shows; sometimes the implication or a release. Each move is one or two sentences.
- About half the sample puts concrete numbers in the abstract (Chen, DeepReflect do so prominently); papers whose
  numbers need context often state qualitative results instead. Two or three numbers that a reader can grasp without
  definitions is a good target.

## Introduction

- **Length:** roughly 900-1,700 words in the sample (ours is about 700). A short introduction is fine only if each move
  is present; ours could spend more words on the problem and the gap before the method.
- **Typical moves, in an order that varies:**
  1. Deployed reality, often anchored with one fact about scale or practice (samples per day, analyst time,
     deployed detector stacks).
  2. The problem, concretely: what a defender cannot currently do.
  3. Why existing approaches do not settle it, naming the closest work and the specific reason, without disparaging it.
  4. The idea, stated plainly in one or two sentences and easy to find (many papers flag it as the key observation,
     insight, or intuition; the label is optional, the clarity is not).
  5. What was built and evaluated, with the headline results.
  6. Contributions as a short list (three or four items), each tied to a section and phrased as something shown, not a
     task performed. Bold lead-ins and section pointers are common.
- **Run-in labels inside the introduction** ("Our approach.", "Evaluation.", "Contributions.") are common at USENIX
  and CCS and help skimming. A closing roadmap paragraph is a minority habit; skip it if space is tight.
- **An overview figure on page 1 or 2** appears in most of the sample: a workflow or setting diagram, or a teaser of the
  main result. Ours are in Section 3; it is worth considering whether one of Figures 1-3 (or a compact variant) should
  appear by the end of the introduction.

## Threat model

- Attack papers give it its own subsection with goals, knowledge, and capabilities (Severi, Pierazzi, Jigsaw). Method
  and tool papers often state assumptions instead (DeepReflect: the input is unpacked, disassembly is reliable, the
  models are trusted), sometimes under the same heading.
- For us (a method with two defender-side applications), a short threat model per application, stating who acts, what
  they own, what the attacker may change, and what is out of scope, is proportionate. Keep it consistent with what the
  experiments actually do (AU: loader-safe changes only).

## Evaluation and results

- Results paragraphs **lead with the finding**, then the numbers, then the reading. "Results." as a run-in label works
  less well than a heading that states what was found, or a first sentence that does.
- Baselines are named and justified as what a practitioner would actually use; comparisons against "prior approaches"
  often get their own subsection.
- Each table and figure is referred to with its takeaway in the text; captions say what to notice.
- Statistics are reported plainly (N, a confidence interval or a test where it matters) without dominating the prose.
- Negative or limiting results appear in the body when they bound a claim (e.g., resolution limits); this reads as
  honest rather than weak.

## Discussion, limitations, conclusion

- Discussion sections in the sample are short, matter-of-fact, and organized by topic with run-in heads: design choices,
  limitations, attacks on the system itself, future work. Limitations are often framed as open problems shared with the
  field rather than as self-criticism. This matches the tone we want: light and confident, no "Threats to Validity".
- Conclusions are brief (about 100-200 words), restating what was shown; some papers merge them with the discussion.
- Ethics sections are rare in the 2020-2023 sample but are now expected (USENIX requires one). Our appendix is
  appropriate; check what the CCS 2027 CfP asks for when it appears.

## Voice and prose

- First-person plural, active voice, present tense for what the paper shows ("we find", "the pullback removes"); past
  tense for what was done in an experiment.
- Short declarative sentences in the introduction; longer, more technical ones are fine in the method.
- Terms are defined once and used consistently; key terms italicized at definition. Named systems are the norm in the
  sample (most give the method a short name); we use "explanation provenance", "pullback", and "pushforward", which is
  enough as long as they are used consistently.
- Formalism is light except where it is the contribution (Pierazzi, Warnecke): definitions in the method, proofs (if
  any) in the appendix.
- Bold run-in paragraph heads are common for structure within subsections, but the sample alternates them with
  ordinary prose paragraphs; a page made entirely of labeled paragraphs ("Motivation. ... Design. ... Results. ...")
  reads like a lab report.

## Observations about our draft (first pass, for the writing sessions)

- Abstract a little long (271 words); introduction short (about 700 words) relative to the sample.
- The idea (every feature is computed from specific bytes, so one recorded matrix transfers explanations both ways) is
  present but could be stated more prominently in the introduction.
- No figure before Section 3.
- Sections 4 and 5 rely heavily on run-in labels (Motivation / Threat model / What X adds / Design / Results /
  Summary); mixing in plain prose and leading with findings would help.
- Balance: Section 4 (pullback, about 3,500 words) is much longer than Section 5 (pushforward, about 2,100), although
  the pushforward is the more novel transfer.
