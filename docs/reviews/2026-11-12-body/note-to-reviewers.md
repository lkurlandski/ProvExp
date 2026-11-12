# Note from the authors to the reviewers

This is a draft of the body. Please review it as a submission, with the points below in mind.

## What the paper claims

The introduction is not written yet, so here is the claim it will make. Many feature extractors used by security
classifiers have one shape: they find the pieces of the input, add up what each piece contributes, and compute each
feature by a formula over a few totals. For extractors of this shape, the effect of an attacker's edits on the features
can be computed from the instrumented extractor instead of being found by trial, by an analyst's reading of the code,
or from attacks that were observed: exactly for one edit (Proposition 1), and as a sound bound on the direction each
feature can move under every edit a threat model allows (Theorem 1). From these directions follow monotone detectors
that no edit in the threat model can evade (Corollary 1). The paper instantiates this for PE malware and the EMBER
feature extractor, and its evaluation (Section 5) asks what hand analysis and observed attacks miss that the computed
directions catch, and what the resulting robustness costs.

## Missing on purpose

The abstract, the introduction (Section 1), the discussion (Section 7), and the ethics and open-science appendices are
empty and will be written last. Judge the paper as it would be with these written competently, and say what they must
establish for you to accept it. The title is a placeholder.

## Numbers are preliminary

The experiments ran at reduced scale (subsamples of the dataset, one seed, 50 attacked malware). They will be re-run
at full scale, so treat every number as a preliminary value: judge whether each experiment's design supports its
claim, and whether the claim would survive plausible shifts (a narrower margin, a smaller count), not the exact values.

The setup (Section 5.1) describes the final protocol, which uses only the files below 4 MB (our copy of the dataset
holds only the first 4 MB of each file). Most numbers in Section 5 and Appendix D still come from the earlier run on
all files. Flag a mismatch between the setup and a result only if you expect it to persist on the files below 4 MB.
You may judge the scope itself: what leaving out the larger files means for the claims.

## One placeholder

Section 5.4 (*Where the guarantee holds*) gives the share of the attacked malware inside the population as 89%. This
value is a prediction from a pending run, not a measurement. Review it as a claim: would the design support the
paper's statement if the run came out as predicted, and what would a different value change?
