# Ranking Algorithm

## Introduction

There are many ways to rank a set of entities given results of one-on-one games between them. The NFL and NBA have a deterministic method to determine which teams make the playoffs, looking at record, division, and head-to-head matchups. The ATP uses a point system to determine world tennis rankings. College sports, on the other hand, typically relies on committees to make ranking decisions.

There is a lot of controversy behind some decisions made by college sports committees. However, it is difficult to rely on something as simple as win-loss record to determine college rankings due to a wide variety of schedules.

My personal opinion is that the most important quality of a ranking should be consistency; that is, if $A$ wins against $B$, $A$ should be ranked higher than $B$. I propose a new ranking system which prioritizes consistency above all else. This is a work in progress.

## The Ranking System

### Competitors, Games, and Ranking

Suppose we have $n$ competitors labelled $c_1, c_2, ..., c_n$.

Define a game as an ordered pair of two different competitors. For a game $(c_i, c_j)$, we say that competitor $c_i$ is the winner and competitor $c_j$ is the loser. Let $G$ be a collection of $m$ not necessarily unique games.

Let $r_i$ be the integer ranking of competitor $c_i$ for each $i \in \{1,...,n\}$. It must be the case that $r_i \neq r_j$ for all unique $i, j \leq n$. It must also be the case that $1 \leq r_i \leq n$ for all $i \leq n$. In other words, each team should be assigned a unique integer ranking from $1$ to $n$.

> [!NOTE]
> In this document, a "higher" ranking indicates a lower number; i.e., if $r_1 = 4$ and $r_2 = 6$, we say $c_1$ is ranked higher than $c_2$.

### Objective

As stated in the Introduction, our biggest priority is consistency, or conversely, minimizing inconsistency. An inconsistency occurs when a competitor $c_i$ is ranked higher th

## The Computation

Description of how the ranking is actually computed.

## The Repository

Description of the parts of the repository and how to use it.
