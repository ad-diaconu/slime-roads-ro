"""Agent-based Physarum (Jeff Jones, 2010) on the Romania grid, with terrain and water as cost.

Each agent senses the trail ahead, ahead-left and ahead-right, turns toward the strongest, moves and deposits.
The trail diffuses (3x3 mean) and evaporates every step. Cities project food onto the trail, weighted by
sqrt(population). The model sees only the land mask, slope and water; never roads.

Terrain enters through one passability map P in [0, 1] (0 = blocked):
    P = exp(-terrain * slope / SLOPE_SCALE) * (1 - water * water_fraction),   P = 0 outside Romania
Agents move `step * (MIN_SPEED + (1 - MIN_SPEED) * P)` px and deposit `deposit * P`, so steep or wet cells
are slower and hold less trail. terrain = 0 gives the flat map of E1.

The agent loop is serial on purpose: a run is deterministic for a given seed, and the GA parallelises over
individuals instead.
"""

from dataclasses import asdict, dataclass

import numpy as np
from numba import njit

SLOPE_SCALE = 3.0  # degrees; with terrain = 1, a 3 deg cell keeps exp(-1) = 37% passability
MIN_SPEED = 0.25


@dataclass(frozen=True)
class Params:
    n_agents: int = 30_000
    sensor_angle: float = 45.0  # deg, how wide an agent looks
    sensor_dist: float = 6.0    # px, how far it looks
    rotate_angle: float = 45.0  # deg, how sharply it turns
    step: float = 1.0           # px per step on flat ground
    deposit: float = 5.0        # trail left per step
    decay: float = 0.20         # fraction of trail evaporated per step
    food: float = 500.0         # trail projected per step by the largest city
    terrain: float = 1.0        # 0 = flat map; higher = slopes cost more
    water: float = 0.9          # 0..1, how much a fully wet cell blocks
    steps: int = 2_000
    spawn: str = "uniform"      # "uniform": agents start all over Romania; "cities": they grow out of the cities

    def to_dict(self):
        return asdict(self)


def passability(layers, p):
    slope, water, mask = layers["slope"], layers["water"], layers["mask"]
    P = np.exp(-p.terrain * slope / SLOPE_SCALE) * (1.0 - p.water * water)
    return np.where(mask, np.clip(P, 0.0, 1.0), 0.0).astype(np.float32)


def food_map(shape, cities, p, radius=1):
    """Food added to the trail each step: a (2r+1)^2 patch per city, sqrt(population) weighted."""
    food = np.zeros(shape, np.float32)
    w = np.sqrt(cities["population"].to_numpy(float) / cities["population"].max())
    for r, c, wi in zip(cities["row"], cities["col"], w):
        food[max(r - radius, 0):r + radius + 1, max(c - radius, 0):c + radius + 1] = p.food * wi
    return food


@njit(cache=True)
def _seed(seed):
    np.random.seed(seed)


@njit(cache=True)
def _spawn(n, P, ys, xs):
    """n agents uniformly on passable cells (ys, xs = indices where P > 0)."""
    idx = np.random.randint(0, ys.size, n)
    y = ys[idx].astype(np.float32) + np.random.random(n).astype(np.float32)
    x = xs[idx].astype(np.float32) + np.random.random(n).astype(np.float32)
    h = (np.random.random(n) * 2 * np.pi).astype(np.float32)
    return y, x, h


@njit(cache=True)
def _sense(trail, y, x, a, d):
    H, W = trail.shape
    r, c = int(y + d * np.sin(a)), int(x + d * np.cos(a))
    if r < 0 or r >= H or c < 0 or c >= W:
        return -1.0
    return trail[r, c]


@njit(cache=True)
def _agents(y, x, h, trail, P, sa, so, ra, step, deposit):
    H, W = trail.shape
    for i in range(y.size):
        f = _sense(trail, y[i], x[i], h[i], so)
        fl = _sense(trail, y[i], x[i], h[i] - sa, so)
        fr = _sense(trail, y[i], x[i], h[i] + sa, so)
        if f > fl and f > fr:
            pass
        elif f < fl and f < fr:
            h[i] += ra if np.random.random() < 0.5 else -ra
        elif fl < fr:
            h[i] += ra
        elif fr < fl:
            h[i] -= ra
        p = P[int(y[i]), int(x[i])]
        v = step * (MIN_SPEED + (1.0 - MIN_SPEED) * p)
        ny, nx = y[i] + v * np.sin(h[i]), x[i] + v * np.cos(h[i])
        r, c = int(ny), int(nx)
        if ny < 0 or nx < 0 or r >= H or c >= W or P[r, c] <= 0.0:
            h[i] = np.random.random() * 2 * np.pi  # blocked: Jones' rule, pick a new heading
            continue
        y[i], x[i] = ny, nx
        trail[r, c] += deposit * P[r, c]


@njit(cache=True)
def _diffuse(trail, food, P, keep):
    """trail <- (3x3 mean of trail + food) * keep, zero where P == 0."""
    H, W = trail.shape
    src = trail + food
    for r in range(H):
        for c in range(W):
            if P[r, c] <= 0.0:
                trail[r, c] = 0.0
                continue
            s = 0.0
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < H and 0 <= cc < W:
                        s += src[rr, cc]
            trail[r, c] = s / 9.0 * keep


def simulate(layers, cities, p=Params(), seed=0, snapshots=(), on_step=None):
    """Run p.steps steps. Returns (final trail, {step: trail copy} for each step in `snapshots`).

    on_step(t, trail, y, x) is called after every step (t = 0 is the initial state), e.g. to record video frames.
    """
    P = passability(layers, p)
    food = food_map(P.shape, cities, p)
    trail = np.zeros(P.shape, np.float32)
    _seed(seed)
    if p.spawn == "uniform":
        ys, xs = np.nonzero(P > 0)
    elif p.spawn == "cities":
        ys, xs = np.nonzero((food > 0) & (P > 0))
    else:
        raise ValueError(f"unknown spawn mode {p.spawn!r}")
    y, x, h = _spawn(p.n_agents, P, ys.astype(np.int32), xs.astype(np.int32))
    sa, ra = np.radians(p.sensor_angle), np.radians(p.rotate_angle)
    shots = {}
    if on_step:
        on_step(0, trail, y, x)
    for t in range(1, p.steps + 1):
        _agents(y, x, h, trail, P, sa, p.sensor_dist, ra, p.step, p.deposit)
        _diffuse(trail, food, P, 1.0 - p.decay)
        if t in snapshots:
            shots[t] = trail.copy()
        if on_step:
            on_step(t, trail, y, x)
    return trail, shots
