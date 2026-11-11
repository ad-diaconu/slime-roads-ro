"""Minimal simulation on the real map + timing benchmark (decides local vs cluster for the GA).

Runs the default parameters on the flat map (terrain = 0) and with relief (terrain = 1), same seed, and writes
outputs/validation/sim_minimal.png. Then times one simulation at several agent counts and extrapolates to a
full GA run (30 individuals x 50 generations = 1,500 simulations).

Usage:  uv run python scripts/sim_demo.py [--steps 2000] [--seed 1]
"""

import argparse
import os
import sys
import time
from dataclasses import replace

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LightSource

from slime import DATA_PROCESSED, OUTPUTS
from slime.data import grid
from slime.sim.agent import Params, simulate

GA_SIMS = 30 * 50


def hillshade(layers):
    elev = np.nan_to_num(layers["elev"], nan=0.0)
    hs = LightSource(azdeg=315, altdeg=45).hillshade(elev, vert_exag=0.02)
    return np.where(layers["mask"], 0.15 + 0.25 * hs, 0.05)


def figure(layers, cities, runs, path):
    steps = sorted(next(iter(runs.values())).keys())
    fig, axes = plt.subplots(len(runs), len(steps), figsize=(5 * len(steps), 3.7 * len(runs)))
    base = hillshade(layers)
    for i, (label, shots) in enumerate(runs.items()):
        for j, t in enumerate(steps):
            ax = axes[i, j]
            ax.imshow(base, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
            tr = shots[t]
            v = np.log1p(tr / np.percentile(tr[layers["mask"]], 99))
            ax.imshow(np.ma.masked_less(v, 0.02), cmap="inferno",
                      vmin=0, vmax=np.log1p(1.0), alpha=0.95, interpolation="nearest")
            ax.scatter(cities.col, cities.row, s=8, c="#4fc3ff", edgecolors="none")
            ax.set_title(f"{label}, step {t}", fontsize=10)
            ax.set_xticks([])
            ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    g, layers = grid.load(DATA_PROCESSED / "grid_2km.npz")
    cities = pd.read_csv(DATA_PROCESSED / "cities.csv")
    p = Params(steps=args.steps)
    print(f"grid {g.width}x{g.height}, {layers['mask'].sum()} land cells, {len(cities)} cities; {p}")

    t = time.time()
    simulate(layers, cities, replace(p, steps=2, n_agents=100))  # numba compile (cached afterwards)
    print(f"compile / cache load: {time.time() - t:.1f}s")

    snaps = (args.steps // 8, args.steps // 4, args.steps // 2, args.steps)
    runs = {}
    for label, terrain in (("flat map", 0.0), ("relief as cost", 1.0)):
        t = time.time()
        _, shots = simulate(layers, cities, replace(p, terrain=terrain), seed=args.seed, snapshots=snaps)
        print(f"{label}: {time.time() - t:.1f}s for {p.steps} steps")
        runs[label] = shots
    out = OUTPUTS / "validation" / "sim_minimal.png"
    figure(layers, cities, runs, out)
    print(f"figure: {out}")

    a, b = runs["flat map"][args.steps], runs["relief as cost"][args.steps]
    again, _ = simulate(layers, cities, replace(p, terrain=1.0), seed=args.seed)
    print(f"same seed twice -> identical trail: {np.array_equal(again, b)}; flat != relief: {not np.array_equal(a, b)}")

    print("\nbenchmark (1 process):")
    workers = os.cpu_count() or 1
    for n in (10_000, 30_000, 60_000):
        q = replace(p, n_agents=n, steps=500)
        t = time.time()
        simulate(layers, cities, q, seed=0)
        per_step = (time.time() - t) / q.steps
        sim = per_step * p.steps
        ga_serial = sim * GA_SIMS
        print(f"  {n:>6} agents: {per_step * 1e3:5.2f} ms/step, {sim:5.1f} s per {p.steps}-step sim, "
              f"GA 30x50: {ga_serial / 3600:5.2f} h serial, ~{ga_serial / 3600 / (workers * 0.6):4.2f} h on "
              f"{workers} threads (assumed 60% scaling)")


if __name__ == "__main__":
    main()
