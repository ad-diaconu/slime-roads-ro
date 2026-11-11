"""Video of the network forming: trail (inferno), agents (faint white), cities (cyan) over the relief.

Usage:  uv run python scripts/make_video.py [--spawn uniform|cities] [--terrain 1.0] [--steps 2000] [--every 4]
        uv run python scripts/make_video.py --compare      # flat map | relief as cost, side by side
Writes outputs/videos/<name>.mp4 (gitignored) and a contact sheet <name>.png next to it.
"""

import argparse
import sys
from dataclasses import replace

import imageio.v2 as imageio
import numpy as np
import pandas as pd
from matplotlib import colormaps
from matplotlib.colors import LightSource
from PIL import Image, ImageDraw, ImageFont

from slime import DATA_PROCESSED, OUTPUTS
from slime.data import grid
from slime.sim.agent import Params, simulate

SCALE = 3
INFERNO = colormaps["inferno"]


def base_rgb(layers):
    elev = np.nan_to_num(layers["elev"], nan=0.0)
    hs = LightSource(azdeg=315, altdeg=45).hillshade(elev, vert_exag=0.02)
    g = np.where(layers["mask"], 0.12 + 0.28 * hs, 0.03)
    return np.repeat(g[..., None], 3, axis=2)


class Renderer:
    """Turns (trail, agents) into an RGB uint8 panel, with a slowly adapting brightness scale."""

    def __init__(self, layers, cities, title):
        self.mask, self.base, self.title, self.ref = layers["mask"], base_rgb(layers), title, None
        self.cities = cities[["row", "col"]].to_numpy()

    def __call__(self, t, trail, y, x):
        p99 = float(np.percentile(trail[self.mask], 99)) if trail.any() else 1.0
        self.ref = p99 if self.ref is None else max(0.97 * self.ref, p99, 1e-6)
        v = np.clip(np.log1p(trail / self.ref) / np.log1p(1.0), 0, 1)
        a = np.clip(v * 1.6, 0, 1)[..., None]
        img = self.base * (1 - a) + INFERNO(v)[..., :3] * a
        counts = np.zeros(self.mask.shape, np.float32)
        H, W = counts.shape
        np.add.at(counts, (np.clip(y.astype(int), 0, H - 1), np.clip(x.astype(int), 0, W - 1)), 1.0)
        ag = np.clip(counts * 0.12, 0, 0.35)[..., None]
        img = img * (1 - ag) + ag
        img = np.repeat(np.repeat((img * 255).astype(np.uint8), SCALE, 0), SCALE, 1)
        for r, c in self.cities:
            img[r * SCALE - 2:r * SCALE + SCALE + 2, c * SCALE - 2:c * SCALE + SCALE + 2] = (79, 195, 255)
        im = Image.fromarray(img)
        d = ImageDraw.Draw(im)
        d.text((12, 10), f"{self.title}   step {t}", fill=(255, 255, 255), font=FONT)
        return np.asarray(im)


def pad16(img):
    h, w = img.shape[:2]
    return np.pad(img, ((0, -h % 16), (0, -w % 16), (0, 0)))


def record(layers, cities, runs, steps, every, seed):
    """runs = [(title, Params)]. Returns frames for every `every` steps (panels side by side)."""
    per_run = []
    for title, p in runs:
        r, frames = Renderer(layers, cities, title), []

        def on_step(t, trail, y, x, r=r, frames=frames):
            if t % every == 0:
                frames.append(r(t, trail, y, x))

        simulate(layers, cities, replace(p, steps=steps), seed=seed, on_step=on_step)
        per_run.append(frames)
        print(f"  {title}: {len(frames)} frames")
    gap = np.zeros((per_run[0][0].shape[0], 8, 3), np.uint8)
    return [pad16(np.concatenate(sum(([f, gap] for f in fs), [])[:-1], axis=1)) for fs in zip(*per_run)]


def main():
    global FONT
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--spawn", default="uniform", choices=["uniform", "cities"])
    ap.add_argument("--terrain", type=float, default=1.0)
    ap.add_argument("--compare", action="store_true", help="flat map | relief as cost")
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--every", type=int, default=4)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    try:
        FONT = ImageFont.truetype("DejaVuSans.ttf", 22)
    except OSError:
        FONT = ImageFont.load_default(size=22)

    _, layers = grid.load(DATA_PROCESSED / "grid_2km.npz")
    cities = pd.read_csv(DATA_PROCESSED / "cities.csv")
    p = replace(Params(), spawn=args.spawn)
    if args.compare:
        runs = [("flat map", replace(p, terrain=0.0)), ("relief as cost", replace(p, terrain=1.0))]
        name = f"compare_{args.spawn}"
    else:
        runs = [(f"terrain={args.terrain:g}, spawn={args.spawn}", replace(p, terrain=args.terrain))]
        name = f"{'relief' if args.terrain else 'flat'}_{args.spawn}"

    frames = record(layers, cities, runs, args.steps, args.every, args.seed)
    out = OUTPUTS / "videos"
    out.mkdir(parents=True, exist_ok=True)
    imageio.mimwrite(out / f"{name}.mp4", frames, fps=args.fps, quality=8, macro_block_size=16)
    picks = [frames[int(i)] for i in np.linspace(0, len(frames) - 1, 6)]
    sheet = np.concatenate([np.concatenate(picks[:3], 1), np.concatenate(picks[3:], 1)], 0)
    Image.fromarray(sheet).resize((sheet.shape[1] // 3, sheet.shape[0] // 3)).save(out / f"{name}.png")
    print(f"wrote {out / name}.mp4 ({len(frames)} frames, {len(frames) / args.fps:.0f}s) and {name}.png")


if __name__ == "__main__":
    main()
