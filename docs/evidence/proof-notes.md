# Proof notes: five small corrections to §3.3 and Appendix C

Written 2026-11-16 (session 73). Found while reading the proofs of Proposition 1 (*Exact side effects*), Theorem 1
(*Sound directions*) and Corollary 1 (*Robustness*); numbers from `manuscript/main.aux`. Each has the text as it
stood, the proposed text, and the reason.

**Status (session 74, 2026-11-16):** all five approved by the user. Notes 1-4 are applied (commit d12ba89), notes 1
and 2 with the text and place of `theory-analysis.md` A.5 (both in Appendix C; Definitions 4 and 7 unchanged). Note 5
is not applied: it changes a pipeline step.

I found no error in the proofs of Proposition 1 and Theorem 1. Notes 1 and 2 are gaps in what the statements cover,
note 3 is an inaccurate comparison with prior work, notes 4 and 5 are things the paper relies on and does not say.

## 1. The sign of a change is not defined when a pool is empty

*Problem.* A max pool that no item touches has the value $-\infty$ (§3.1). Definition 4 (*Readouts*) gives a readout
real values, so the identity readout of such a pool is not covered; and Theorem 1 speaks of "the change
$x'_j - \varphi_j(z)$", which is undefined when the pool is empty before and after ($-\infty$ minus $-\infty$). The
proofs only ever compare the two values, so the fix is to define the sign by comparison.

*Where.* Definition 7 (*Threat models and directions*), `_d_framework.tex`.

*Old.* "A \emph{direction} is one of four sets of signs that the change of a value can have: ..."

*New, one sentence added before it.* "The \emph{sign} of the change of a value from $x$ to $x'$ is $+$ if $x' > x$,
$-$ if $x' < x$, and $0$ if the two are equal; this also covers a pool that no item touches, whose value is
infinite."

*Also, in Definition 4:* "$\rho_j: \mathcal{S} \to \mathbb{R}$" would read
"$\rho_j: \mathcal{S} \to \mathbb{R} \cup \{-\infty, +\infty\}$". If that is unwelcome in the definition, the
sentence above is enough for the theorem, and a footnote-free alternative is to say in §3.1 that a feature that
returns a pool returns a default when the pool is empty (which leads to note 2).

## 2. A readout that returns a default for an empty pool is not always nondecreasing

*Problem.* Extractors return a default (usually 0) for an empty pool. That is a function $g$ of the pool, and
Table 1's "monotone" rule needs $g$ nondecreasing. It is only if the default lies below every possible contribution
(max pool) or above every one (min pool). A minimum that defaults to 0 over positive values is not: adding the first
item raises the feature from 0, while the rule says additions can only lower a min pool. The table would call the
feature down, and an edit would raise it.

*Instance.* Not affected: thrember's three section minima take a literal 0 into the minimum and are constant on the
pilot test files, and the table has them fixed. The gap is in the general statement.

*Where.* Appendix C, the paragraph *The readout rules*, `_j_proofs.tex`, after the sentence on nondecreasing $g$.

*New, one sentence.* "A readout that returns a default value for an empty pool is nondecreasing only if the default
is at most every contribution to a max pool, or at least every contribution to a min pool; otherwise the feature
takes the last rule."

## 3. The comparison of Corollary 1 with Gimenez et al.'s Proposition 1

*Problem.* Their Proposition 1 asks the classifier to be increasing in every feature under the order $\le$. Ours
uses the order the table defines, under which two vectors that differ in a fixed feature are not comparable, so the
detector is unconstrained on fixed features. "This is Gimenez et al.'s Proposition 1" is not exact, and it gives away
the part that is ours.

*Where.* Appendix C, *Proof of Corollary 1*.

*Old.* "This is Gimenez et al.'s Proposition~1~\cite{gimenez2025certifiably}, with the preorder ``$z'$ is reachable
from $z$'' and a feature map made monotone by $D$."

*New.* "This is the argument of Gimenez et al.'s Proposition~1~\cite{gimenez2025certifiably}, with the preorder
``$z'$ is reachable from $z$'' and, in place of the order $\le$ on the features, the order that $D$ defines, under
which two vectors that differ in a fixed feature are not comparable."

## 4. §3.3 does not say that the monotone detector is unconstrained on fixed features

*Problem.* The sentence that introduces the detector lists what it must do on up, down and both features and is
silent on fixed ones. A reader will not infer that it may use them freely, which is what makes the detector usable.

*Where.* §3.3, the paragraph before Corollary 1.

*Old.* "A gradient-boosted tree trained with monotone constraints, increasing in the up features and decreasing in
the down features, and reading no feature marked both, is such a score."

*New.* "A gradient-boosted tree trained with monotone constraints, increasing in the up features, decreasing in the
down features, unconstrained in the fixed features, and reading no feature marked both, is such a score."

## 5. The trained detector's guarantee rests on the library enforcing the constraints

*Problem.* Corollary 1 applies to a score that is monotone with respect to the table. That the trained GBDT is one
rests on LightGBM's enforcement of its monotone constraints, which the paper does not state or check. (LightGBM also
silently uses its `basic` constraint method unless `feature_fraction` and `feature_fraction_bynode` are 1; all three
methods enforce the constraints, so this does not affect the guarantee.)

*What exists.* `provexp.models.gbdt.monotone_violations` checks the saved trees directly: every pair of leaves of a
tree that the table's order makes comparable has ordered values. It has tests, and found zero violations on the
pilot's monotone models. It is not yet called by any pipeline step.

*Proposed.* (a) Call it once per monotone model in `4-detectors/train` and record the count in `metrics.json`
(a few lines; needs your go-ahead since it touches a scale-up step). (b) One sentence in §5.1's setup, wording to be
agreed, to the effect that the constraints were verified on the trained trees. No sentence without (a) at the
scale-up.
