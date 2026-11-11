"""How many simulations per hour does this machine do? Decides where the GA runs.

Runs --sims simulations (different seeds) over --workers processes, the way the GA will evaluate a
population, and extrapolates to a full GA run (30 individuals x 50 generations = 1,500 simulations).
Writes outputs/benchmark/<host>.json.

Usage:  uv run python scripts/benchmark.py --workers 8 --sims 24
        (cluster: slurm/benchmark.slurm)
"""

import argparse
import json
import os
import platform
import socket
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace

import pandas as pd

from slime import DATA_PROCESSED, OUTPUTS
from slime.data import grid
from slime.sim.agent import Params, simulate

GA_SIMS = 30 * 50
_W = {}


def _init(params):
    _, layers = grid.load(DATA_PROCESSED / "grid_2km.npz")
    _W.update(layers=layers, cities=pd.read_csv(DATA_PROCESSED / "cities.csv"), p=params)
    simulate(layers, _W["cities"], replace(params, steps=2, n_agents=100))  # load numba cache


def _run(seed):
    t = time.time()
    simulate(_W["layers"], _W["cities"], _W["p"], seed=seed)
    return time.time() - t


def main():
    default_workers = int(os.environ.get("SLURM_CPUS_PER_TASK", os.cpu_count() or 1))
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=default_workers)
    ap.add_argument("--sims", type=int, default=None, help="default: 3 x workers")
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--agents", type=int, default=30_000)
    args = ap.parse_args()
    sims = args.sims or 3 * args.workers
    p = replace(Params(), steps=args.steps, n_agents=args.agents)

    _init(p)  # compile once in the parent so workers only load the cache
    t = time.time()
    single = _run(0)
    print(f"1 simulation alone: {single:.1f}s ({args.agents} agents, {args.steps} steps)")

    t = time.time()
    with ProcessPoolExecutor(args.workers, initializer=_init, initargs=(p,)) as ex:
        per_sim = list(ex.map(_run, range(1, sims + 1)))
    wall = time.time() - t
    rate = sims / wall * 3600
    res = dict(
        host=socket.gethostname(), platform=platform.platform(), cpu_count=os.cpu_count(),
        slurm_job=os.environ.get("SLURM_JOB_ID"), workers=args.workers, sims=sims,
        steps=args.steps, agents=args.agents, single_sim_s=round(single, 2),
        mean_sim_s_in_pool=round(sum(per_sim) / sims, 2), wall_s=round(wall, 1),
        sims_per_hour=round(rate), ga_30x50_hours=round(GA_SIMS / rate, 2),
    )
    print(json.dumps(res, indent=2))
    out = OUTPUTS / "benchmark"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{res['host'].split('.')[0]}.json").write_text(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
