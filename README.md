# Ranking Algorithm

## Introduction

There are many ways to rank a set of competitors given results of one-on-one games between them. The NFL and NBA have a deterministic method to determine which teams make the playoffs, looking at record, division, and head-to-head matchups. The ATP uses a point system to determine world tennis rankings. College sports, on the other hand, typically relies on committees to make ranking decisions.

There is a lot of controversy behind some decisions made by college sports committees. However, it is difficult to rely on something as simple as win-loss record to determine college rankings due to a wide variety of schedules.

My personal opinion is that the most important quality of a ranking should be consistency; that is, if $A$ wins against $B$, $A$ should be ranked higher than $B$. I propose a new ranking system which prioritizes consistency above all else. This is a work in progress.

## The First Ranking System

### Competitors, Games, and Ranks

Suppose we have $n$ competitors labelled $c_1, c_2, ..., c_n$.

Define a game as an ordered pair of two different competitors. For a game $(c_i, c_j)$, we say that competitor $c_i$ is the winner and competitor $c_j$ is the loser. Let $G$ be a collection of games. Games are not necessarily unique; $G$ can contain the same game multiple times. If this is the case, the game will contribute to totals as many time as it is present in $G$.

Let $r_i$ be the integer rank of competitor $c_i$ for each $i \in \{1,...,n\}$. It must be the case that $r_i \neq r_j$ for all unique $i, j \leq n$. It must also be the case that $1 \leq r_i \leq n$ for all $i \leq n$. In other words, each competitor should be assigned a unique integer rank from $1$ to $n$.

> [!NOTE]
> In this document, a "higher" rank indicates a lower number; i.e., if $r_1 = 4$ and $r_2 = 6$, we say $c_1$ is ranked higher than $c_2$.

### First Mathematical Formulation

As stated in the Introduction, our biggest priority is consistency, or conversely, minimizing inconsistency. An inconsistency occurs when a competitor $c_i$ is ranked higher than another competitor $c_j$ despite $c_j$ having beaten $c_i$ in a game.

For each game $(c_i, c_j)$, we can compute an inconsistency score. If $r_i > r_j$, then we say the inconsistency score is $0$ (since this is a "consistent" game). However, if $r_i < r_j$, then we say the inconsistency score is $r_j - r_i$, i.e. the difference of the two competitors' ranks. These two cases can be combined by saying the inconsistency score of a game $(c_i, c_j)$ is $\max(0, r_j - r_i)$.

The total inconsistency score of the ranking is just the sum of all the inconsistency scores of the games. Our objective is to minimize this total inconsistency score. Combine this objective with the rank constraints outlined earlier, and we see the optimization problem $(1)$ that defines our ranking system.

![eq1](img/eq1.png)

## The Improved Ranking System

Optimization problem $(1)$ is valid and prioritizes consistency, but there are a few features that could be viewed as problematic. We make small, parameterized changes to the formulation to solve these problems, allowing the ranking behavior to be tuned based on specific preferences and league characteristics.

### Respecting Head-To-Head Results

Consider a situation where we have a clear top two competitors $c_1$ and $c_2$. Suppose $c_1$ has beaten $c_2$, but $c_1$ has lost to a significantly lower ranked competitor $c_3$. Should $c_1$ or $c_2$ be ranked first?

Let's consider both cases with the objective function proposed in $(1)$. If we let $r_1=1$ and $r_2=2$, then the game between $c_1$ and $c_2$ is consistent. The game between $c_1$ and $c_3$ gives an inconsistency score of $r_3 - 1$.

Now, let $r_1=2$ and $r_2=1$. The game between $c_1$ and $c_2$ is now inconsistent with score $1$. The game between $c_1$ and $c_3$ is inconsistent with score $r_3 - 2$. The total inconsistency score here is $1 + (r_3 - 2) = r_3 - 1$.

Notice that in $(1)$, both rankings are equally consistent. However, I propose that a better ranking, when magnitude of inconsistency is equivalent, should then minimize the number of inconsistencies. This is certainly the precedent set in many rankings to prioritize head-to-head results. In this case, letting $r_1=1$ and $r_2=2$ should be preferred so the game between $c_1$ and $c_2$ is a consistent one with the ranking.

This can be achieved by not only tracking the size of each inconsistency, but also the number of inconsistencies. Therefore, we introduce a parameter $\alpha \geq 0$ to form a new game inconsistency score, $\max(0, \alpha + r_j - r_i)$ for game $(c_i, c_j)$. If $r_i > r_j$, then the game still has score $0$.

The parameter $\alpha$, which must be a non-negative integer, controls the trade-off between inconsistency magnitude and inconsistency count:

$\alpha = 0$: Pure magnitude-based scoring. Only the rank difference matters, not the number of inconsistencies. A single large inconsistency is equivalent to many small inconsistencies with the same total magnitude. This is the same as before.

$\alpha = 1$: Balanced approach. Each inconsistency contributes 1 point plus the magnitude difference. This favors minimizing the number of inconsistencies when total magnitudes are equal.

$\alpha > 1$: Count-prioritizing approach. More heavily emphasizes minimizing the number of inconsistencies over the size of the inconsistencies.

This can also be confirmed with our previous example. Letting $r_1 = 1$ and $r_2 = 2$ gives total inconsistency score $0 + (\alpha + r_3 - 1) = \alpha + r_3 - 1$. On the other hand, letting $r_1 = 2$ and $r_2 = 1$ gives total inconsistency score $(\alpha + 2 - 1) + (\alpha + r_3 - 2) = 2\alpha + r_3 - 1$. The first rank assignment now has a lower inconsistency score for any $\alpha > 0$, as desired.

Requiring $\alpha$ to be an integer ensures that inconsistency scores remain integers, which is crucial for maintaining the strict priority of consistency over strength of schedule (discussed in the next section).

### Considering Strength Of Schedule

While our primary objective remains consistency, we recognize that not all results are equal. A win against a top-tier competitor should carry more weight than a win against a bottom-tier competitor, and a loss to a bottom-tier competitor should be more damaging than a loss to a top-tier competitor.

To break ties between rankings with identical inconsistency scores, we introduce a comprehensive strength of schedule metric. We consider only consistent games—those where the ranking aligns with the game outcome—because inconsistent games already contribute to our primary inconsistency score. This ensures we don't double-penalize or double-reward results that are already accounted for in the core optimization.

We compute a strength of schedule metric $\text{SOS}_i$ for competitor $c_i$ using equation $(2)$, where:

-   $W_i$ denotes the set of opponents that $c_i$ has beaten in consistent games ($r_i < r_j$)

-   $L_i$ denotes the set of opponents that have beaten $c_i$ in consistent games ($r_i > r_j$)

Let:

-   $Q_i^{\text{win}} = \sum_{c_j \in W_i} (n - r_j + 1)^k$ (quality of wins)

-   $Q_i^{\text{loss}} = \sum_{c_j \in L_i} (r_j)^k$ (severity of losses)

Then:

![eq2](img/eq2.png)

Where:

-   $Q_{\text{max}}^{\text{win}} = \max_{m} Q_m^{\text{win}}$ (maximum quality of wins among all competitors)

-   $Q_{\text{max}}^{\text{loss}} = \max_{m} Q_m^{\text{loss}}$ (maximum severity of losses among all competitors)

-   $\epsilon > 0$ is a small constant ensuring this tie-breaker term remains strictly less than 1

Via the parameter $\lambda$, this formulation provides intuitive control over the balance between rewarding quality wins and penalizing bad losses:

-   $\lambda = 0$: Only losses matter ($\text{SOS}_i$ ranges from slightly less than -1 to 0)

-   $\lambda = 0.5$: Wins and losses are equally weighted ($\text{SOS}_i$ ranges from slightly more than -0.5 to slightly less than 0.5)

-   $\lambda = 1$: Only wins matter ($\text{SOS}_i$ ranges from 0 to slightly less than 1)

The parameter $k \geq 0$ controls the emphasis on opponent quality:

-   $k = 0$: No quality differentiation—pure win-loss counting where all wins contribute equally and all losses penalize equally

-   $0 < k < 1$: Diminishing returns—rewards consistency across many games, with less differentiation between elite and good wins

-   $k = 1$: Linear weighting—balanced emphasis on both quantity and quality

-   $k > 1$: Increasing returns—heavy emphasis on elite wins and terrible losses, with minimal credit for beating weak opponents

For any $k \geq 0$, adding a consistent win always increases $\text{SOS}_i$, and adding a consistent loss always decreases $\text{SOS}_i$, ensuring the metric behaves intuitively.

We then modify our objective function by adding the term:

![eq3](img/eq3.png)

The $\epsilon$ term from $(2)$ ensures $\text{SOS}_i$ is strictly bounded away from the theoretical extremes, guaranteeing the tie-breaker term has magnitude strictly less than 1. Since $\alpha$ is an integer and inconsistency scores are therefore integers, this ensures consistency always takes priority over strength of schedule considerations.

This approach maintains our philosophical commitment to consistency while comprehensively evaluating performance quality when rankings are otherwise equally consistent.

### Improved Mathematical Formulation

The improvements outlined above lead us to our final formulation of the optimization problem.

Given $n$ competitors $c_1, c_2, ..., c_n$ and a collection of games $G$, we seek to find ranks $r_1, r_2, ..., r_n$ that solve:

![eq4](img/eq4.png)

Where the strength of schedule metric $\text{SOS}_i$ is defined as:

![eq5](img/eq5.png)

With:

-   $W_i = \{c_j : (c_i, c_j) \in G \text{ and } r_i < r_j\}$ (consistent wins)

-   $L_i = \{c_j : (c_j, c_i) \in G \text{ and } r_i > r_j\}$ (consistent losses)

-   $Q_{\text{max}}^{\text{win}} = \max_{m} \sum_{c_j \in W_m} (n - r_j + 1)^k$

-   $Q_{\text{max}}^{\text{loss}} = \max_{m} \sum_{c_j \in L_m} (r_j)^k$

-   $\alpha \in \mathbb{Z}_{\geq 0}$ controlling the inconsistency count vs magnitude trade-off

-   $\epsilon > 0$ ensuring the tie-breaker term magnitude is strictly less than 1

-   $k \geq 0$ controlling quality emphasis

-   $0 \leq \lambda \leq 1$ controlling wins/losses balance

The first term minimizes ranking inconsistencies, while the second term breaks ties using strength of schedule, with the coefficient $\frac{2}{n(n+1)}$ guaranteeing that consistency always takes priority. The integer requirement for $\alpha$ ensures that inconsistency scores remain integers, preserving the strict dominance of consistency over the real-valued strength of schedule tie-breaker.

## The Computation

Description of how the ranking is actually computed.

## The Repository

Description of the parts of the repository and how to use it.
