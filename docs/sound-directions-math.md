# Sound Directions: the mathematics, settled before the prose (session 22, 2026-11-09)

Working note for the rewrite of `sec:fw:directions` (round 4, written in blocks with the user's review after each).
Not paper text. Approved by the user: pending.

## What changed from round 3, in one paragraph

Round 3 had two vocabularies for one idea (directions; sign sets with a sign sum), an undefined central object (the
derived table, written with the generic $D$), and a rewrite whose four restrictions were a leftover of the cut §3.3.
Settling the mathematics removes all three: (1) a *direction* is one of four sign sets, and the union of two
directions is again a direction, so the sign sum is not needed; (2) a *change* is a pair (old content, new content),
either of which may be absent, so adding, removing, and replacing are one notion, and the restrictions on a
replacement become simply which pairs the signature allows; (3) with an absent content contributing the neutral
element, one rule gives the direction of every sum, additive or pool; (4) the derived table $D_{\mathcal{M}}$ gets its
own definition.

## The objects, in order

**Def 7 (threat models, populations, direction tables).** A threat model $\mathcal{M}$ is a set of transformations
(the edits allowed in one step); $\mathcal{T}$ are their finite sequences. A population is a subset
$Z \subseteq \mathcal{Z}$; it is closed under $\mathcal{M}$ if $T(z) \in Z$ for every $z \in Z$, $T \in \mathcal{M}$.
The four directions are the sign sets fixed $= \{0\}$, up $= \{0,+\}$, down $= \{-,0\}$, both $= \{-,0,+\}$. A
direction table $D$ gives each feature $j$ a direction $D_j$; it is sound for $\mathcal{M}$ over $Z$ if
$\operatorname{sgn}(\varphi_j(T(z)) - \varphi_j(z)) \in D_j$ for every $z \in Z$, $T \in \mathcal{M}$, and $j$.
*Why the theorem needs it:* this is what the theorem claims, and what Cor 1 consumes.

**Def 8 (changes and signatures).** A change of kind $\tau$ is a pair $(c, c')$ of contents of kind $\tau$, either of
which may be absent ($\bot$), not both: $(\bot, c')$ adds an item, $(c, \bot)$ removes one, $(c, c')$ replaces one in
place. A delta $(I^-, I^+)$ is *made of* a set of changes if its items can be paired so that every removed and every
added item belongs to exactly one change, and the two items of a replacement have the same kind. A signature $\Delta$
gives each kind $\tau$ a set $\Delta_\tau$ of changes; it *covers* $\mathcal{M}$ over $Z$ if every $T \in \mathcal{M}$
on every $z \in Z$ has a delta made of changes in $\Delta$. *Why a replacement is not a removal plus an addition:* the
delta does not say which added item took the place of which removed one, and the bound needs it: an edit that may add
and may remove items of a kind can move their count either way, while one that replaces items one for one cannot move
it. Restrictions such as "keeps the key" or "extends the content" are just which pairs $\Delta_\tau$ contains;
they appear as examples in the table of common contributions, not in the definition.
*Why the theorem needs it:* it is the theorem's hypothesis, the description of the edits that replaces their deltas.

**Def 9 (the direction of a sum).** With $\nu_\tau(\bot) = \mathbf{e}$, the sign of a change on sum $k$ is
the sign of $\nu_\tau(c')_k$ compared with $\nu_\tau(c)_k$ (for an additive sum, the sign of the difference; for a
pool, which of the two values is larger, with $\pm\infty$ as the neutral element). The direction $d_k$ of sum $k$ under
$\Delta$ is the smallest direction containing the signs of all changes of $\Delta$ on $k$: fixed if none moves it, up
if none lowers it, down if none raises it, both otherwise.
*Plain claim (Lemma, proof in the appendix):* if $\Delta$ covers $\mathcal{M}$, every edit moves every sum within its
direction. Additive: the change is the total of the changes' differences, and a total of non-negative terms is
non-negative. Max pool: if no change lowers it, every old value has a new value at least as large (an addition has
none to beat; a removal would lower it and is excluded), so the maximum does not fall. Min pool: the same, and the
neutral element $+\infty$ makes a removal a raise and an addition a lowering, so no separate rule is needed.

**Readout rules (table in the body, as the user asked).** A rule gives a feature a direction from the directions of the
sums in its support, and is valid if the feature moves within it whenever every sum moves within its own:
identity $s_k$: $d_k$; presence $[s_k > 0]$: $d_k$; distinct count: the union of the counts' directions; ratio $a/b$
($a \ge 0$, $b > 0$): $d_a \cup (-d_b)$; normalized bin: as the ratio; any other readout: fixed if every sum of its
support is fixed, both otherwise (from Def 5 alone). The union of directions replaces the sign sum: on directions the
two coincide.

**Def 10 (the derived table $D_{\mathcal{M}}$).** $(D_{\mathcal{M}})_j$ is the readout rule of feature $j$ applied to
the directions $d_k$, $k \in K_j$.

**Theorem 1.** If $\Delta$ covers $\mathcal{M}$ over $Z$, then $D_{\mathcal{M}}$ is sound for $\mathcal{M}$ over $Z$.
If $Z$ is moreover closed under $\mathcal{M}$, then for every $z \in Z$ and every $\mathbf{x}' \in \mathcal{R}(z)$,
$\operatorname{sgn}(x'_j - \varphi_j(z)) \in (D_{\mathcal{M}})_j$ for every $j$.
*Why:* one step = the Lemma, then the readout rule. A sequence: closure keeps every intermediate input in $Z$, and a
direction is closed under adding changes (two rises are a rise), which is why directions, not arbitrary sign sets,
are what the table holds.

**Cor 1.** Call $h$ monotone with respect to $D$ if $h(\mathbf{x}') \ge h(\mathbf{x})$ whenever
$\operatorname{sgn}(x'_j - x_j) \in D_j$ for every $j$. If $D$ is sound over a closed $Z$ and $h$ is monotone with
respect to it, $h(\mathbf{x}') \ge h(\varphi(z))$ for every $z \in Z$ and $\mathbf{x}' \in \mathcal{R}(z)$ (Gimenez
et al.'s argument). A gradient-boosted tree with monotone constraints that reads no feature marked both is such an $h$.

## What leaves the body

The sign sum $\boxplus$ and the letters $A$, $B$; general sign sets; the four rewrite restrictions in the definition;
the separate pool and min-pool rules; the last paragraph after Cor 1 (its "sums as features" remark stays in the
proof appendix). Appendix Table 6 becomes the signs of common changes (add, remove, replace keeping the key, replace
by an extension) per contribution form.

## Blocks for the rewrite (user's review after each)

1. Lead (two small clarifications) and Def 7 with $Z$ and directions, plus the Omega explanation (2-3 sentences).
2. The lead-in to signatures (2-3 sentences), Def 8, the short justification of replacements, where signatures come
   from.
3. Def 9 and the sums paragraph, the readout rules with the table, Def 10.
4. Theorem 1, why it holds, the lead-in to Cor 1, Cor 1; the closing paragraph deleted.
