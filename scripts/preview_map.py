"""First look at the data, and the alignment checks from the plan.

Writes to outputs/validation/:
  map_overview.png   terrain on the 2 km grid (EPSG:3844) + motorway/trunk/primary + the 42 county seats
  map_checks.png     native-resolution zooms: DN1 up the Prahova Valley, DN7 through the Olt Gorge
and data/processed/cities.csv (the 42 county seats with OSM coordinates and population).

Usage:  uv run python scripts/preview_map.py
"""

import sys
import time

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource, LinearSegmentedColormap
from matplotlib.lines import Line2D
from pyproj import Transformer

from slime import DATA_PROCESSED, OUTPUTS
from slime.data import dem, grid, osm

OUT = OUTPUTS / "validation"
ROAD_STYLE = {
    "motorway": ("#e8231c", 2.0),
    "trunk": ("#ffffff", 1.2),
    "primary": ("#1f4fe0", 0.8),
}
DARKEN = 0.80  # multiply land colours: lower = darker map
CHECKS = {  # (W, S, E, N) in degrees, the road that must follow the valley
    "DN1 – Valea Prahovei (Ploiești → Brașov)": ((25.35, 44.9, 26.15, 45.75), "DN1"),
    "DN7 – Defileul Oltului (Râmnicu Vâlcea → Sibiu)": (
        (23.95, 45.05, 24.55, 45.85),
        "DN7",
    ),
}


def has_ref(refs, code):
    return (
        refs.fillna("")
        .str.split(";")
        .apply(lambda parts: code in [p.strip() for p in parts])
    )


LAND = LinearSegmentedColormap.from_list(
    "land", plt.cm.terrain(np.linspace(0.25, 1.0, 256))
)


def shaded(elev):
    z = np.nan_to_num(elev, nan=0.0)
    rgb = LightSource(azdeg=315, altdeg=45).shade(
        z, cmap=LAND, vert_exag=0.05, blend_mode="soft", vmin=0, vmax=2300
    )
    rgb[..., :3] *= DARKEN
    rgb[z <= 0] = (
        0.20,
        0.33,
        0.48,
        1.0,
    )  # sea level (Black Sea); rivers come from OSM later
    rgb[np.isnan(elev)] = (0.25, 0.25, 0.25, 1.0)  # outside the DEM tiles
    return rgb


def road_effects(lw):
    """Thin dark outline so white / gray roads stay visible on any terrain."""
    return [pe.Stroke(linewidth=lw + 1.2, foreground="#1a1a1a"), pe.Normal()]


def overview(g, elev, roads, seats):
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.imshow(shaded(elev), extent=g.extent, origin="upper")
    r = roads.to_crs(g.crs)
    for cls in ("primary", "trunk", "motorway"):
        color, lw = ROAD_STYLE[cls]
        r[r.highway == cls].plot(
            ax=ax, color=color, linewidth=lw, path_effects=road_effects(lw)
        )
    s = seats.copy()
    xs, ys = Transformer.from_crs("EPSG:4326", g.crs, always_xy=True).transform(
        s.lon, s.lat
    )
    ax.scatter(
        xs,
        ys,
        s=np.sqrt(s.population.fillna(5e4)) / 6,
        c="#ffd400",
        edgecolors="black",
        linewidths=0.8,
        zorder=5,
    )
    halo = [pe.withStroke(linewidth=2.5, foreground="black")]
    for x, y, name in zip(xs, ys, s.name):
        ax.annotate(
            name,
            (x, y),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7.5,
            color="white",
            path_effects=halo,
            zorder=6,
        )
    handles = [
        Line2D(
            [],
            [],
            color=c,
            linewidth=lw + 1,
            path_effects=road_effects(lw + 1),
            label=cls,
        )
        for cls, (c, lw) in ROAD_STYLE.items()
    ]
    ax.set_xlim(g.extent[:2])
    ax.set_ylim(g.extent[2:])
    ax.set_title(
        f"Terrain on the simulation grid ({g.width}×{g.height}, {g.cell / 1000:.0f} km/px, EPSG:3844), "
        "OSM main roads and the 42 county seats"
    )
    ax.legend(
        handles=handles,
        loc="lower left",
        facecolor="#333333",
        labelcolor="white",
        framealpha=0.9,
    )
    ax.set_xticks([])
    ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(OUT / "map_overview.png", dpi=130)
    plt.close(fig)


def checks(roads):
    fig, axes = plt.subplots(1, len(CHECKS), figsize=(16, 9))
    for ax, (title, (bounds, ref)) in zip(axes, CHECKS.items()):
        elev, t = dem.mosaic(bounds)
        ext = (t.c, t.c + elev.shape[1] * t.a, t.f + elev.shape[0] * t.e, t.f)
        ax.imshow(shaded(elev), extent=ext, origin="upper")
        clip = roads.cx[bounds[0] : bounds[2], bounds[1] : bounds[3]]
        for cls in ("primary", "trunk", "motorway"):
            color, lw = ROAD_STYLE[cls]
            clip[clip.highway == cls].plot(
                ax=ax, color=color, linewidth=lw, path_effects=road_effects(lw)
            )
        hit = clip[has_ref(clip["ref"], ref)]
        hit.plot(ax=ax, color="#ffd400", linewidth=2.8, path_effects=road_effects(2.8))
        ax.set_xlim(bounds[0], bounds[2])
        ax.set_ylim(bounds[1], bounds[3])
        ax.set_title(
            f"{title}\n{ref} in yellow ({len(hit)} OSM ways); motorway red, trunk white, primary blue",
            fontsize=10,
        )
        ax.set_aspect(1 / np.cos(np.radians((bounds[1] + bounds[3]) / 2)))
    fig.tight_layout()
    fig.savefig(OUT / "map_checks.png", dpi=130)
    plt.close(fig)


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # Windows console: Romanian diacritics
    OUT.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    t = time.time()
    g = grid.romania(2.0)
    elev = dem.to_grid(g)
    print(
        f"grid {g.width}x{g.height} @ {g.cell:.0f} m; elevation {np.nanmin(elev):.0f}..{np.nanmax(elev):.0f} m "
        f"({time.time() - t:.0f}s)"
    )

    t = time.time()
    roads = osm.load_roads()
    print(
        f"roads: {len(roads)} ways  {roads.highway.value_counts().to_dict()}  ({time.time() - t:.0f}s)"
    )
    for code in ("A1", "A2", "DN1", "DN7"):
        print(f"  ref {code}: {has_ref(roads['ref'], code).sum()} ways")

    t = time.time()
    seats = osm.county_seats()
    seats.to_csv(DATA_PROCESSED / "cities.csv", index=False)
    print(
        f"cities: {len(seats)} county seats, population known for {seats.population.notna().sum()} "
        f"({time.time() - t:.0f}s)"
    )

    overview(g, elev, roads, seats)
    checks(roads)
    print(f"figures in {OUT}")


if __name__ == "__main__":
    main()
