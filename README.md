# Ranking Algorithm

## Introduction

There are many ways to rank competitors using results from one-on-one games. Professional leagues such as the NFL and NBA use deterministic rules based on record, division standings, and head-to-head outcomes. Tennis uses a cumulative point system to determine ATP world rankings. College sports, however, typically rely on committees to make subjective decisions.

Committee-based systems generate controversy, yet relying solely on win–loss records is inadequate in some leagues because teams play vastly different schedules.

My view is that **the most important property of a ranking is consistency**—if competitor $A$ defeats competitor $B$, then $A$ should be ranked higher than $B$.

This document introduces a deterministic ranking system that **prioritizes consistency above all else**, and then enhances it with tunable parameters that address realistic edge cases.

## Quick Start

1.  **Prepare your data:** Place game results in `data/games.json` following the [Input File Format](#input-file-format-game-results).
2.  **Competitor Filtering:** Create `data/filter.json` with competitors to include in the final ranking (optional).
3.  **Configure parameters:** Set environment variables in `.env` (optional).
4.  **Run the solver:** Execute `python rank.py` and response to console prompts.
5.  **View results:** Find the ranking in `rankings/output.json` or specified output file.

## The First Ranking System

### Competitors, Games, and Ranks

Suppose we have $n$ competitors labelled $c_1, c_2, ..., c_n$.

A **game** is an ordered pair $(c_i, c_j)$ indicating that $c_i$ defeated $c_j$. We treat the set of games $G$ as a **multiset**: the same match may appear multiple times, and each appearance contributes separately to totals.

Each competitor is assigned a unique integer rank from $1$ (best) to $n$ (worst). Thus,

-   $1 \leq r_i \leq n$ for all $i$,
-   $r_i \neq r_j$ for all $i \neq j$.

In other words, the rank vector $r = (r_1, ..., r_n)$ is a permutation of $\{1, ..., n\}$.

### First Mathematical Formulation

An **inconsistency** occurs when a lower-ranked competitor defeats a higher-ranked one. For a game $(c_i, c_j)$:

-   If the ranking agrees with the outcome ($r_i < r_j$), the inconsistency score is $0$.
-   If the ranking contradicts the result ($r_i > r_j$), the inconsistency score is $r_i - r_j$.

These cases can be written compactly as:

$$
max(0, r_i - r_j).
$$

The **total inconsistency score** is the sum of these values over all games. To prioritize consistency, we minimize this score subject to ranking constraints:

$$
\min \sum_{(c_i, c_j) \in G} \max(0, r_i - r_j)\\
\text{s.t. } r_i \neq r_j \text{ } \forall \text{ } i \neq j \\
r_i \in {1, ..., n} \text{ } \forall \text{ } i
\tag{1}
$$

This formulation is valid and captures the idea of minimizing ranking contradictions. However, it has some shortcomings, which motivate additional refinements.

## The Improved Ranking System

Optimization problem $(1)$ focuses solely on the **total magnitude** of inconsistencies. While this is desirable, it misses two features commonly valued in rankings:

1. Respecting head-to-head results, even when inconsistency magnitudes tie.

2. Considering strength of schedule, once consistency is maximized.

We address each separately.

### Respecting Head-To-Head Results

Consider three competitors $c_1$, $c_2$, and $c_3$ among many:

-   $c_1$ beats $c_2$
-   $c_1$ loses to $c_3$

Suppose $c_1$ and $c_2$ are clearly above the rest. Under formulation $(1)$:

-   Ranking $c_1 = 1, c_2 = 2$ yields a total inconsistency score of $r_3 - 1$.
-   Ranking $c_1 = 2, c_2 = 1$ yields a total inconsistency score of $1 + (r_3 - 2) = r_3 - 1$.

Thus, both are equally consistent under $(1)$. But intuitively—and in common ranking systems—**if inconsistency magnitude ties, the ranking with fewer inconsistent games should be preferred**. In this example, $c_1$ should be ranked above $c_2$ since that ranking gives 1 inconsistent game of magnitude $r_3 - 1$ instead of 2 inconsistent games with the same total magnitude.

To accomplish this, we introduce a parameter $\alpha \geq 0$ that assigns an additional penalty per inconsistent game. Define a new game inconsistency score function $I$:

$$
I(r_i, r_j, \alpha) =
\begin{cases}
    0 & \text{if } r_i < r_j,\\
    (r_i - r_j) + \alpha  & \text{if } r_i > r_j.
\end{cases}
\tag{2}
$$

Interpretation of $\alpha$:

-   $\alpha = 0$: pure magnitude—this recovers formulation $(1)$.
-   $\alpha = 1$: ties in magnitude are broken by counting inconsistent games.
-   $\alpha > 1$: strongly prioritizes minimizing the number of inconsistent games, potentially over the magnitude of them.

Requiring $\alpha$ to be an integer ensures inconsistency scores remain integer-valued, which will be important later when we add a fractional tie-breaker.

### Considering Strength Of Schedule

It is still possible for multiple rankings to have identical inconsistency scores. To distinguish these, we incorporate a **strength of schedule (SOS)** measure.

#### Computing SOS

Critically, **we evaluate strength of schedule _only_ using consistent games.** Inconsistent games already strongly affect the objective through inconsistency penalties.

For competitor $c_i$:

-   $W_i$: multiset of opponents that $c_i$ defeated in **consistent** games.
-   $L_i$: multiset of opponents that defeated $c_i$ in **consistent** games.

Define:

-   Quality of wins:
    $$
    Q_i^{\text{win}} = \sum_{c_j \in W_i} (n - r_j + 1)^k
    $$
-   Severity of losses:
    $$
    Q_i^{\text{loss}} = \sum_{c_j \in L_i} (r_j)^k
    $$

Let:

-   $Q_{\text{max}}^{\text{win}} = \max_{m} Q_m^{\text{win}}$ (maximum quality of wins among all competitors)

-   $Q_{\text{max}}^{\text{loss}} = \max_{m} Q_m^{\text{loss}}$ (maximum severity of losses among all competitors)

We then define:

$$
\text{SOS}_i = \lambda \cdot \frac{Q_i^\text{win}}{Q_\text{max}^\text{win} + \epsilon} - (1 - \lambda) \cdot \frac{Q_i^\text{loss}}{Q_\text{max}^\text{loss} + \epsilon}.
\tag{3}
$$

Here:

-   $\epsilon > 0$ ensures division remains well-defined and keeps SOS strictly less than $1$ in magnitude, which will preserve consistency dominance.
-   $\lambda \in [0, 1]$ sets the win/loss weighting.
-   $k \geq 0$ controls the emphasis on opponent quality.

Parameter interpretations:

-   $\lambda = 1$: only wins influence SOS
-   $\lambda = 0$: only losses influence SOS
-   $\lambda = 0.5$: balanced wins and losses
-   $k = 0$: all wins and losses count equally
-   $k = 1$: linear emphasis on opponent rank
-   $k > 1$: rewards elite wins heavily and penalizes bad losses harshly

SOS behaves intuitively:

-   Adding a consistent win always increases $\text{SOS}_i$.
-   Adding a consistent loss always decreases $\text{SOS}_i$.

#### Using SOS as a tie-breaker

We incorporate strength of schedule adding the following term to the objective:

$$
\frac{2}{n(n+1)} \cdot \sum_{i=1}^n(\text{SOS}_i \cdot r_i).
$$

Multiplying by $r_i$ ensures:

-   Because the objective is minimized, a higher SOS is preferred when paired with a smaller $r_i$ (a better rank).
-   This aligns the minimization with the intuitive principle that stronger schedules should correspond to better ranks.

From equation $(3)$, each $\text{SOS}_i$ is bounded by $(\lambda - 1, \lambda)$. The extreme values of the sum $\sum_{i=1}^n(\text{SOS}_i \cdot r_i)$ occur when:

-   All $\text{SOS}_i = \lambda$ and competitors are ordered optimally, giving $\lambda \cdot n(n+1)/2$

-   All $\text{SOS}_i = \lambda - 1$ and competitors are ordered optimally, giving $(\lambda - 1) \cdot n(n+1)/2$

The scaling factor $\frac{2}{n(n+1)}$ normalizes these extremes to ensure the range of the SOS term remains $(\lambda - 1, \lambda)$. This guarantees that inconsistency scores—which are integers due to integer $\alpha$—always dominate SOS effects.

Thus, the system remains philosophically consistent: strength of schedule matters _only after_ consistency is maximized.

### Improved Mathematical Formulation

Combining everything, the final optimization problem is:

$$
\min \sum_{(c_i, c_j) \in G} I(r_i, r_j, \alpha) + \frac{2}{n(n+1)} \cdot \sum_{i=1}^n(\text{SOS}_i \cdot r_i)\\
\text{s.t. } r_i \neq r_j \text{ } \forall \text{ } i \neq j, \\
r_i \in {1, ..., n} \text{ } \forall \text{ } i.
\tag{4}
$$

Where:

-   $I$ is defined in $(2)$
-   $\text{SOS}_i$ is defined in $(3)$
-   $W_i = \{c_j : (c_i, c_j) \in G \text{ and } r_i < r_j\}$
-   $L_i = \{c_j : (c_j, c_i) \in G \text{ and } r_i > r_j\}$
-   $\alpha \geq 0$ is an integer
-   $\epsilon > 0, k \geq 0, \lambda \in [0, 1]$

This formulation:

-   **Minimizes inconsistency magnitude**
-   **Minimizes number of inconsistencies** (via $\alpha$)
-   **Breaks remaining ties using strength of schedule**, scaled so that consistency always dominates

Together, these components produce rankings that are consistent, interpretable, and tunably sensitive to quality of competition.

## The Computation

The optimization problem in $(4)$ is combinatorial: the feasible set consists of all permutations of ${1, ..., n}$, and even for moderate $n$, the search space $n!$ is far too large for exhaustive search.

Accordingly, the solver employs **stochastic discrete optimization** consisting of two complementary procedures:

1. **Simulated Annealing** — a global heuristic designed to escape poor local minima;
2. **Sliding Optimization** — a deterministic local refinement method restricted to small contiguous moves.

The annealing stage explores the permutation space broadly and identifies a near-optimal basin, while the sliding stage performs a fine-grained local search to converge to a stable minimum of the objective.

Both methods evaluate candidate rankings using the complete objective function in $(4)$, including inconsistency penalties and the normalized SOS tie-breaker. All computations treat the rank vector as an ordered list (a permutation of competitors), with index position $i$ corresponding to rank $i+1$.

### Simulated Annealing

Simulated annealing provides a probabilistic framework for minimizing a discrete objective function that may contain many local minima.

Let $r$ denote the current permutation and $L(r)$ the current **loss**, which we define as the value of the objective function in $(4)$.

At each iteration:

1. Two competitors are selected uniformly at random.
2. Their positions in the ordering are swapped, producing a new permutation $r'$.
3. The loss difference $\Delta=L(r')-L(r)$ is computed.
4. The new state is accepted according to the Metropolis criterion:

    $$
    r \leftarrow \begin{cases}
        r' & \text{if } \Delta < 0,\\
        r' & \text{with probability } \exp(-\Delta / T),\\
        r & \text{otherwise},
    \end{cases}
    $$

    where $T>0$ is the current temperature.

The temperature decreases geometrically every 1,000 iterations according to

$$
T_{k+1}=\begin{cases}
    \gamma T_k & \text{if } k \equiv 0 \mod 1000,\\
    T_k & \text{otherwise},
\end{cases}
$$

where $T_0 = 1$ and $0<\gamma<1$ is a specified **cooling rate** parameter.

This schedule enables broad exploration early (high $T$) and increasingly selective refinement as $T \rightarrow 0$.

Several properties of this implementation are worth noting:

-   **Move structure.** Each proposal is a single transposition, the simplest non-trivial move on the permutation group. Because any permutation can be expressed as a sequence of transpositions, and the algorithm selects every possible transposition with positive probability, the induced Markov chain is irreducible: every ranking is reachable from every other ranking. This ensures the annealing process can fully explore the permutation space rather than becoming trapped in a restricted subset.
-   **Energy landscape.** Because inconsistency losses are integer-valued and SOS contributions are strictly bounded by construction, the annealing dynamics primarily explore the integer part of the objective with fractional corrections discouraging but never overriding the consistency-driven structure.
-   **Best-state tracking.** The algorithm retains the best permutation observed at any temperature, guaranteeing monotonic improvement of the reported solution even though the Markov chain itself may accept uphill moves.

This stage terminates after a predetermined amount iterations and returns a near-optimal ranking that typically lies within the attraction basin of the true minimum.

### Sliding Optimization

Following annealing, a deterministic **sliding optimization** procedure refines the ranking by examining small localized adjustments.

For each competitor currently at position $i$, the method considers moving that competitor a bounded number of positions upward or downward:

$$
i \rightarrow i + s, \text{ } i \rightarrow i - s, \text{ } 1 \leq s \leq W
$$

where $W$ is a specified **window search size**.

For each feasible shift, a new permutation is formed by removing the competitor from its original position and reinserting it at the candidate location; all other relative orders are preserved.

For each competitor:

1. All upward and downward slides within the window are evaluated.
2. The slide yielding the smallest loss is identified.
3. If that slide improves the global objective, it is applied immediately.
4. The process restarts from the top of the ranking after every successful improvement.

This “first-improvement restart” strategy ensures that local dependencies are respected: repositioning a single competitor often alters the optimal moves for those around it, so restarting prevents stale assumptions about local structure.

The sliding stage repeats until either:

-   a full pass over all competitors yields no improvement, or

-   the predetermined maximum number of passes is reached.

Because slides are strictly loss-decreasing, this stage converges to a **local minimum within the neighborhood of contiguous moves up to size $W$.**

Empirically, annealing identifies a strong basin, and sliding then resolves fine-grained rank ordering that transposition dynamics alone are unlikely to discover.

## The Repository

This section describes the structure of the repository, the required environment variables, the expected file formats, and how to run the ranking procedure on an arbitrary set of pairwise game results. An example using 2025 college football data is also provided.

### Repository Structure

```
.
├── rank.py                 # Optimization solver implementing the ranking algorithm
├── helpers/                # Helper scripts
├── data/                   # Input game and competitor filter files
├── rankings/               # Output files
├── .env                    # Environment variable definitions (optional)
└── README.md               # This document
```

The core solver is `rank.py`, which loads game results, applies the filtering rules, constructs the optimization problem described in $(4)$, and performs simulated annealing followed by sliding optimization to obtain a final ranking.

### Installation

1. **Clone or download** this repository
2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Optional:** Create a `.env` file for custom parameters (see [Environment Variables](#environment-variables))

### Environment Variables

The solver reads several configuration parameters from the environment. Any parameter omitted from the environment uses its built-in default value.

| Variable             | Meaning                                                                     | Default  |
| -------------------- | --------------------------------------------------------------------------- | -------- |
| `ALPHA`              | Penalty per inconsistent game (favors fewer inconsistencies over magnitude) | `1`      |
| `K`                  | Exponent in SOS computations (emphasizes elite wins/bad losses)             | `2.0`    |
| `LAMBDA`             | Weighting of wins (1.0) vs. losses (0.0) in SOS                             | `0.5`    |
| `EPSILON`            | Small constant ensuring strict SOS bounds                                   | `0.001`  |
| `SEED`               | Random seed for reproducible results                                        | `42`     |
| `ANNEALING_ITER`     | Total simulated annealing iterations                                        | `200000` |
| `COOLING_RATE`       | Temperature reduction rate (per 1,000 iterations)                           | `0.99`   |
| `WINDOW_SEARCH_SIZE` | Maximum slide distance in local optimization                                | `3`      |
| `MAX_SLIDE_PASSES`   | Maximum full passes during sliding optimization                             | `1000`   |

### Input File Format (Game Results)

The solver expects the game list in a JSON file. Each entry must contain exactly two fields:

```json
[
  { "winner": "Team A", "loser": "Team B" },
  { "winner": "Team C", "loser": "Team D" },
  ...
]
```

-   Each item represents one completed game.
-   The objects are interpreted literally: in the example above, Team A defeated Team B, and Team C defeated Team D.

This file may contain any number of games and any number of repeated matchups. The algorithm automatically treats the list as a multiset, as described in the formulation. The file must be placed in the `data/` directory.

### Competitor Filtering

You may optionally restrict the ranking to a subset of competitors—for example, only FBS teams, or only teams in a particular conference.

To do this, create a file containing a JSON array of competitor names:

```json
["Team A", "Team B", "Team C", ...]
```

The solver computes a ranking for **all competitors** present in the game data. Then, it filters out any competitors not listed in the filter file. This approach ensures that games against filtered-out opponents (e.g., an FBS team beating an FCS team) are still counted in the inconsistency and Strength of Schedule calculation for the remaining competitors, while excluding those opponents from the final ranking list.

### Output Files

Rankings are written to the `rankings/` directory. Output file name is specified as input in the console, but defaults to `output.json`.

An output file has the structure:

```json
{
	"parameters": {
		"ALPHA": 1,
		"K": 2.5,
		"LAMBDA": 0.67,
		"EPSILON": 0.001,
		"SEED": 42,
		"ANNEALING_ITER": 2000000,
		"COOLING_RATE": 0.998,
		"MAX_SLIDE_PASSES": 2000,
		"WINDOW_SEARCH_SIZE": 5
	},
	"info": {
		"final_loss": 1979.991882573818,
		"loss_after_annealing": 1981.993108416549,
		"slide_improvements_made": 63,
		"total_games": 1351,
		"total_competitors": 265,
		"ranked_competitors": 136
	},
  "ranking": [
    {
      "rank": 1,
      "competitor": "Team A",
      "inconsistency_score": 0,
      "SOS": 0.658520019039728,
      "inconsistent_games": []
    },
    ...
    {
      "rank": 5,
      "competitor": "Team B",
      "inconsistency_score": 53,
      "SOS": 0.6627604786107557,
      "inconsistent_games": [
        {
          "type": "loss",
          "opponent": "Team C",
          "magnitude": 52
        }
      ]
    },
    ...
  ]
}
```

## Example: 2025 College Football Rankings

This repository includes an example using real college football data. It contains:

-   a CFB game scraper: `helpers/pull_cfb.py`,
-   a JSON array of FBS teams: `data/fbs_team.json`
-   a final college football ranking: `rankings/cfb_2025_ranking.json`

This example demonstrates how to generate fully reproducible rankings from publicly available CollegeFootballData (CFBD) results.

### The Scraper

The `pull_cfb.py` file in the `helpers/` directory downloads game data for a given year using the CollegeFootballData API.

#### Prerequisites

1. Get a free API key from [CollegeFootballData.com](https://collegefootballdata.com/key)
2. Add it to your `.env` file:

```
CFBD_API_KEY=your_key_here
```

#### Usage

```bash
cd helpers
python pull_cfb.py
```

The script will:

1. Prompt you for a year (e.g., 2024)

2. Download all completed FBS/FCS games for that year

3. Save to `data/cfb_YYYY_games.json`

#### Output Format

The generated file follows the required input format and includes:

-   All regular season and postseason games

-   Both FBS and FCS teams

-   Games filtered to completed status only

### FBS Ranking

Even though the goal is to rank only the FBS teams, the scraped data includes both FBS and FCS teams because they can play each other. This ensures that FBS teams are properly rewarded or penalized for beating or losing to an FCS team.

To filter out the FCS teams from the final ranking, the filter file `fbs_teams.json` in the `data/` directory can be specified in the console when running the ranking script.

The computed FBS ranking can be found in `rankings/cfb_2025_ranking.json`. The file contains information on the parameters used.

## Helpers and Included Data

The repository contains a few helper scripts to pull and simulate miscellaneous data. Details will not be specified here, but the scripts are fairly straight-forward.

The repository also includes some game data, team data, and rankings. Files in the `data/` directory ending in `_games` contain game data. Files in the `data/` directory ending in `_teams` contain team filters. Files in the `rankings/` directory contain the ranking computed from the games and team filter, if applicable.

<!-- ## Observations, Recommendations, and Shortcomings

- conference/division clustering
- set k high for leagues with a variety of skill levels (college sports), low for leagues with higher parity (like the nfl)
- ranking system does not consider point differential, when the game was played, or any external factors (injuries, roster/staff changes, expectations, "eye test", etc)
- The winner of the "championship" will not necessarily be ranked first. In general, the ranking considers all games as equally "important"
-->
