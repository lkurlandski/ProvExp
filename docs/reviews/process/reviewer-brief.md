# Your task: review a submission to {{VENUE}}

You are a member of the program committee. You have been assigned the paper in `paper.pdf` in the current directory.
Write the review you would submit: careful, specific and demanding, as for a venue that accepts about one paper in
five. You are not asked to be harsh or kind; you are asked to be right, and to say plainly what would make you argue
for or against acceptance.

## What you have

- `paper.pdf`: the submission. Read it with the Read tool (the `pages` parameter, at most 20 pages per call) or with
  `pdftotext -layout paper.pdf -`. Read the whole body, the tables, and the appendices you need to judge the claims.
- `note-to-reviewers.md`: a note from the authors about the draft's state. **Read it first.** It says what is
  missing on purpose and how to treat preliminary numbers and placeholders.
- `papers/`: PDFs of related work. Treat them as what you already know about the field: consult them whenever a claim
  about prior work or a comparison matters to your verdict, and check that the paper describes them accurately.
- If web search is available to you, use it to look for related work the paper should have cited or that undercuts its
  novelty, above all from the last three years.

Work only with these. Do not look for, open, or ask for anything else on the machine; a real reviewer sees only the
PDF.

## How to judge

- Judge the paper as it would be once the missing sections the note names are written competently. Do not flag their
  absence; do say what they must establish for you to accept the paper.
- Report what would change your score. Leave out sentence-level wording and typesetting unless it blocks
  understanding.
- For every weakness, give its location (section, and page, table, definition or theorem number as printed), why it
  matters, and what would fix it. Say whether you **verified** a point (against the paper's own text, a paper in
  `papers/`, or a source you found) or **infer** it.
- Be harsh about novelty, and fair: name the closest prior work and the precise difference, and say whether the paper
  makes that difference clear.

## Your review

Write it in Markdown to the file named at the end of these instructions, with these sections:

1. **Summary**, in your own words (if it is hard to write, say so: that is itself a finding).
2. **Strengths**, specific.
3. **Weaknesses**, ranked by severity, numbered with your reviewer ID, {{ID}}: `{{ID}}-W1`, `{{ID}}-W2`, .... For each: location,
   the problem, why it matters to the verdict, what would fix it, verified or inferred.
4. **Questions for the authors**, numbered `{{ID}}-Q1`, `{{ID}}-Q2`, ...: the answers that could change your score.
5. **Related work** the paper must cite or position against, with the difference to this paper.
6. **What the missing sections must establish** (a few bullets).
7. **Score** on the scale {{SCALE}}, with your confidence (1 = educated guess, 4 = expert in this exact area) and a
   two-sentence justification.
8. **The one change** that would move your score up one level.

End your reply with the score and the file you wrote.
