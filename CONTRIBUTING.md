# Contributing

This repo holds the *Physarum on the map of Romania* project: we simulate slime mould on the terrain, tune its
parameters with a genetic algorithm and compare the resulting network with the real roads. Full plan:
[Physarum pe harta României rețele auto-organizate optimizate genetic.md](Physarum%20pe%20harta%20Rom%C3%A2niei%20re%C8%9Bele%20auto-organizate%20optimizate%20genetic.md).

Ground rule: the history must show **which code and which data produced each result**.

## 1. Workflow

1. Branch off an up-to-date `main` (§2).
2. Make small, single-purpose commits (§3).
3. Open a PR into `main`, get at least one review, merge, then delete the branch.

Never push directly to `main`.

## 2. Branches

Format: `<owner>/<type>-<description>`

- **owner**: your short handle, always the same one (`andrei`, `sebi`, ...).
- **type**: one of the types in §3, matching the branch's main goal.
- **description**: kebab-case, 2–5 words, ASCII.

One branch = one component or one experiment. Do not mix unrelated work.

### Feature branches (build steps B1–B7 in BACKLOG.md)

| ID | Stage | Example |
| --- | --- | --- |
| B1 | Project setup and cluster | `andrei/infra-project-setup` |
| B2 | Data: cities, roads, terrain, shared grid | `andrei/data-align-dem-roads` |
| B3 | Agent-based simulation with terrain cost | `andrei/sim-agent-terrain-cost` |
| B4 | Graph extraction (threshold, skeletonize) | `andrei/eval-graph-extraction` |
| B5 | Metrics (link F1, efficiency, fault tolerance) | `andrei/eval-link-f1` |
| B6 | Genetic algorithm | `andrei/ga-tournament-elitism` |
| B7 | Visualisation (live view, GIFs, overlays) | `andrei/viz-live-pygame` |

### Experiment branches

Format: `<owner>/exp-e<N>-<description>`, one branch per experiment.

| # | Experiment | Branch | Priority |
| --- | --- | --- | --- |
| E1 | Flat map vs. terrain map | `exp-e1-flat-vs-relief` | Required |
| E2 | GA evolution over generations | `exp-e2-ga-evolution` | Required |
| E3 | Optimised network vs. real roads | `exp-e3-vs-real-roads` | Required |
| E4 | Proposed and ignored links | `exp-e4-missing-links` | Required |
| E5 | Train/test on regions | `exp-e5-region-split` | Recommended |
| E6 | Resilience to a blocked corridor | `exp-e6-corridor-block` | Recommended |
| E7 | Comparison with MST and the A\* union | `exp-e7-mst-astar` | Optional |

A failed experiment is not deleted: open a PR with its results and a short note.

## 3. Commits

[Conventional Commits](https://www.conventionalcommits.org/): `<type>(<scope>): <summary>`. The summary is
imperative, lower case, no trailing period, at most ~72 characters. Example: `sim(agent): slow particles on steep terrain`.

**Types:** `exp`, `data`, `sim`, `ga`, `eval`, `results`, `viz`, `docs`, `fix`, `refactor`, `chore`.
**Common scopes:** `cities`, `roads`, `dem`, `grid`, `agent`, `tero`, `fitness`, `graph`, `metrics`,
`baselines`, `e1`…`e7`.

**`!` = earlier results can no longer be compared with new ones.** Use it for changes to the grid size or
resolution, the city list or populations, terrain cost, the fitness function, metric definitions or the ~10 km
matching tolerance. Add a trailer that says what must be re-run:

```
sim(grid)!: switch grid from 2 km to 1 km per pixel

BREAKING-RESULTS: E1-E4; re-run the GA and final simulations
```

Optional trailers: `Refs: E3`, `Metrics: link F1 0.62 ± 0.04`, `Config: <command>`, `Code: <hash>`, `Seeds: 1-5`.

## 4. Results and data

- **Real roads are for evaluation only.** They never feed the simulation or the fitness (exception: E5, and only on
  the training region).
- Code and results go in separate commits: code first, then `results(...)` with `Code: <hash>`.
- Do not commit results produced from uncommitted code, and never edit results by hand; re-run instead.
- Every experiment runs over several seeds; report mean ± standard deviation.
- Large raw data (`*.osm.pbf`, DEM `*.tif`) and large videos stay out of git; commit the script that downloads or
  generates them.

## 5. Pull requests

Every task lives as an issue in the [planner](https://github.com/users/ad-diaconu/projects/4), synced from
[BACKLOG.md](BACKLOG.md): experiments E1–E7 and build steps B1–B7.

- **Title** in commit-message format, e.g. `exp(e1): flat vs relief with 5 seeds`.
- **Description**: fill in the [PR template](.github/pull_request_template.md). Put the issue number in
  `Fixes #<n>` so merging closes the issue and moves it to Done in the planner.
- If the PR is results-breaking, say clearly what has to be re-run.
