# Ranking Algorithm

## Introduction

There are many ways to rank a set of entities given results of one-on-one games between them. The NFL and NBA have a deterministic method to determine which teams make the playoffs, looking at record, division, and head-to-head matchups. The ATP uses a point system to determine world tennis rankings. College sports, on the other hand, typically relies on committees to make ranking decisions.

There is a lot of controversy behind some decisions made by college sports committees. However, it is difficult to rely on something as simple as win-loss record to determine college rankings due to a wide variety of schedules.

My personal opinion is that the most important quality of a ranking should be consistency; that is, if $A$ wins against $B$, $A$ should be ranked higher than $B$. I propose a new ranking system which prioritizes consistency above all else. This is a work in progress.

## The First Ranking System

### Competitors, Games, and Ranks

Suppose we have $n$ competitors labelled $c_1, c_2, ..., c_n$.

Define a game as an ordered pair of two different competitors. For a game $(c_i, c_j)$, we say that competitor $c_i$ is the winner and competitor $c_j$ is the loser. Let $G$ be a collection of $m$ not necessarily unique games.

Let $r_i$ be the integer rank of competitor $c_i$ for each $i \in \{1,...,n\}$. It must be the case that $r_i \neq r_j$ for all unique $i, j \leq n$. It must also be the case that $1 \leq r_i \leq n$ for all $i \leq n$. In other words, each competitor should be assigned a unique integer rank from $1$ to $n$.

> [!NOTE]
> In this document, a "higher" rank indicates a lower number; i.e., if $r_1 = 4$ and $r_2 = 6$, we say $c_1$ is ranked higher than $c_2$.

### First Mathematical Formulation

As stated in the Introduction, our biggest priority is consistency, or conversely, minimizing inconsistency. An inconsistency occurs when a competitor $c_i$ is ranked higher than another competitor $c_j$ despite $c_j$ having beaten $c_i$ in a game.

For each game $(c_i, c_j)$, we can compute an inconsistency score. If $r_i > r_j$, then we say the inconsistency score is $0$ (since this is a "consistent" game). However, if $r_i < r_j$, then we say the inconsistency score is $r_j - r_i$, i.e. the difference of the two competitors' ranks. These two cases can be combined by saying the inconsistency score of a game $(c_i, c_j)$ is $\max(0, r_j - r_i)$.

The total inconsistency score of the ranking is just the sum of all the inconsistency scores of the games. Our objective is to minimize this total inconsistency score. Combine this objective with the rank constraints outlined earlier, and we see the optimization problem $(1)$ that defines our ranking system.

![eq1](img/eq1.png)

## The Improved Ranking System

Optimization problem $(1)$ is valid and prioritizes consistency, but there are a few features that could be viewed as problematic. We make small changes to the formulation to solve these problems.

### Respecting Head-To-Head Results

Consider a situation where we have a clear top two competitors $c_1$ and $c_2$. Suppose $c_1$ has beaten $c_2$, but $c_1$ has lost to a significantly lower ranked competitor $c_3$. Would we rather have $c_1$ or $c_2$ be ranked $1$?

Let's consider both cases with the objective function proposed in $(1)$. If we let $r_1=1$ and $r_2=2$, then the game between $c_1$ and $c_2$ is consistent. The game between $c_1$ and $c_3$ gives an inconsistency score of $r_3 - 1$.

Now, let $r_1=2$ and $r_2=1$. The game between $c_1$ and $c_2$ is now inconsistent with score $1$. The game between $c_1$ and $c_3$ is inconsistent with score $r_3 - 2$. The total inconsistency score here is $1 + (r_3 - 2) = r_3 - 1$.

Notice that in $(1)$, both rankings are equally consistent. However, I propose that a better ranking, when magnitude of inconsistency is equivalent, should then minimize the number of inconsistencies. This is certainly the precedent set in many rankings to prioritize head-to-head results. In this case, letting $r_1=1$ and $r_2=2$ should be preferred so the game between $c_1$ and $c_2$ is a consistent one with the ranking.

This can be achieved by not only tracking the size of each inconsistency, but also the number of inconsistencies. Therefore, our new objective function is the sum of all game inconsistency scores plus the number of inconsistent games. Equivalently, we can just add $1$ to each inconsistent game to form a new game inconsistency score, $\max(0, r_j - r_i + 1)$ for game $(c_i, c_j)$. Indeed, if $r_i > r_j$, then the game still has score $0$.

This can also be confirmed with our previous example. Letting $r_1 = 1$ and $r_2 = 2$ gives total inconsistency score $0 + (r_3 - 1 + 1) = r_3$. On the other hand, letting $r_1 = 2$ and $r_2 = 1$ gives total inconsistency score $(2 - 1 + 1) + (r_3 - 2 + 1) = r_3 + 1$. The first rank assignment now has a lower inconsistency score, as desired.

### Considering Strength Of Schedule

While our primary objective remains consistency, we recognize that not all wins and losses are equal. A win against a top-tier competitor should carry more weight than a win against a bottom-tier competitor when both are consistent with the ranking.

To break ties between rankings with identical inconsistency scores, we introduce a strength of schedule metric. However, we must ensure this never compromises our core consistency objective. We achieve this by adding a carefully bounded tie-breaking term to our optimization problem.

We compute a strength of schedule metric $SOS_i$ for competitor $c_i$ using equation $(2)$. Let $OPP_i$ be the collection of opponents that $c_i$ has played.

![eq2](img/eq2.png)

This formulation can be understood as follows:

-   $\frac{n - r_j}{n}$ converts each opponent's rank to a "quality score" between $0$ (worst opponent) and $\frac{n-1}{n}$ (best opponent)

-   We average these scores across all opponents by dividing by the number of opponents $|OPP_i|$ to get $SOS_i$.

-   The division by $n$ ensures $0 < SOS_i < 1$, since each opponent contributes at most $\frac{n-1}{n}$ to the average.

-   Thus, $SOS_a > SOS_b$ indicates that $c_a$ has faced tougher opponents on average than $c_b$.

To incorporate this into our ranking, we modify the objective function by adding the term computed in $(3)$.

![eq3](img/eq3.png)

This addition works as follows:

-   The term $SOS_i \cdot r_i$ is minimized when competitors with high $SOS_i$ (tough schedules) receive low $r_i$ (good ranks).

-   The maximum possible value of $\sum_{i=1}^{n}(SOS_i \cdot r_i)$ occurs when every competitor has $SOS_i close to $1$, yielding slightly less than $\frac{n(n+1)}{2}$.

-   Multiplying by $\frac{2}{n(n+1)}$ ensures the entire tie-breaker term is always less than $1$.

-   Since our inconsistency scores are integers greater than or equal to $1$, this guarantee means consistency always takes priority over strength of schedule.

This approach maintains our philosophical commitment to consistency while rewarding competitors that face tougher competition when rankings are otherwise equally consistent.

### Other Improvements

Description of other improvements made to the optimization problem.

### Improved Mathematical Formulation

The new mathematical formulation.

## The Computation

Description of how the ranking is actually computed.

## The Repository

Description of the parts of the repository and how to use it.
