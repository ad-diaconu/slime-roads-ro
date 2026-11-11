# Backlog

Single source of truth for the [planner](https://github.com/users/ad-diaconu/projects/4). Edit here, then sync
with the `gh-backlog` skill; do not edit the issues on GitHub. Keep descriptions to one or two sentences.

**Status:** `todo` · `in progress` · `blocked` · `done` · `rejected`
**Priority:** P0 (required) · P1 (recommended) · P2 (optional)

## E. Experiments

| ID | Title | Description | Branch | P | Status |
|---|---|---|---|---|---|
| E1 | flat map vs. terrain map | Simulate on a flat map vs. the terrain map (DEM as cost), same cities and parameters. Shows how much the Carpathians shape the network. | `exp-e1-flat-vs-relief` | P0 | todo |
| E2 | GA evolution over generations | Plot GA fitness per generation and the best network at generations 1, 10, 50. RQ5. | `exp-e2-ga-evolution` | P0 | todo |
| E3 | optimised network vs. real roads | Compare with real roads on the city graph: link F1, length, efficiency, fault tolerance, plus a visual overlay. RQ1, RQ3. | `exp-e3-vs-real-roads` | P0 | todo |
| E4 | proposed and ignored links | Links the slime builds that Romania lacks, and real roads it ignores (e.g. Moldova–Transylvania, Transfăgărășan). RQ2. | `exp-e4-missing-links` | P0 | todo |
| E5 | train/test on regions | Optimise road similarity on one region (e.g. Transylvania), test on the rest of the country. RQ5. | `exp-e5-region-split` | P1 | todo |
| E6 | resilience to a blocked corridor | Block a corridor (e.g. Valea Oltului) mid-simulation and record how the network reorganises. RQ4. | `exp-e6-corridor-block` | P1 | todo |
| E7 | comparison with MST and A* union | Place MST, the A* union, Physarum + GA and real roads on one cost vs. efficiency chart. RQ3. | `exp-e7-mst-astar` | P2 | todo |

## T. Tasks

Pipeline work that is not an experiment (data, simulation, graph extraction, metrics, GA, visualisation).

| ID | Title | Description | Branch | P | Status |
|---|---|---|---|---|---|
