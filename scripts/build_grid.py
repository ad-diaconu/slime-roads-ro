"""Build the simulation inputs on the 2 km grid (the only data the slime mould gets; no roads).

Writes:
  data/processed/grid_2km.npz   mask, water, elev, elev_min, slope (+ grid definition)
  data/processed/cities.csv     the 42 county seats with population and grid row / col
  outputs/validation/grid_layers.png

Layers (all height x width, EPSG:3844, 2 km cells):
  mask      bool   Romanian land: >= half the cell inside the national border, Black Sea removed
  water     float  fraction of the cell covered by OSM natural=water (Danube, lakes, reservoirs)
  elev      float  mean elevation, m
  elev_min  float  lowest elevation in the cell (valley floor), m
  slope     float  degrees, from elev_min: a narrow valley stays passable at 2 km/px

Usage:  uv run python scripts/build_grid.py
"""

import sys
import time

import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

from slime import DATA_PROCESSED, OUTPUTS
from slime.data import dem, grid, osm

GRID_FILE = DATA_PROCESSED / "grid_2km.npz"
CITIES_FILE = DATA_PROCESSED / "cities.csv"


def sea_cells(elev):
    """Cells at or below 0 m connected to the east edge (the Black Sea). Delta lakes stay inland water."""
    low = np.nan_to_num(elev, nan=0.0) <= 0
    lab, _ = ndimage.label(low)
    edge = np.unique(lab[:, -1])
    return np.isin(lab, edge[edge > 0])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "validation").mkdir(parents=True, exist_ok=True)
    g = grid.romania(2.0)

    t = time.time()
    elev, elev_min = dem.to_grid(g, how=("average", "min"))
    print(f"DEM: {time.time() - t:.0f}s")

    t = time.time()
    border = osm.load_border()
    import geopandas as gpd

    border_xy = gpd.GeoSeries([border], crs="EPSG:4326").to_crs(g.crs)
    country = grid.coverage(g, border_xy)
    sea = sea_cells(elev)
    mask = (country >= 0.5) & ~sea
    print(f"border: {mask.sum()} land cells = {mask.sum() * (g.cell / 1000) ** 2:,.0f} km2 ({time.time() - t:.0f}s)")

    t = time.time()
    water_gdf = osm.load_water().to_crs(g.crs)
    water = grid.coverage(g, water_gdf.geometry)
    print(f"water: {len(water_gdf)} polygons, {(water * mask).sum() * 4:,.0f} km2 inside the mask, "
          f"{((water >= 0.5) & mask).sum()} cells >= 50% water ({time.time() - t:.0f}s)")

    slope = grid.slope_deg(g, elev_min)
    slope_mean = grid.slope_deg(g, elev)

    seats = osm.county_seats()
    row, col = g.to_pixel(seats.lon.to_numpy(), seats.lat.to_numpy())
    seats["row"], seats["col"] = np.floor(row).astype(int), np.floor(col).astype(int)
    outside = seats[~mask[seats.row, seats.col]]
    if len(outside):
        raise ValueError(f"county seats outside the land mask: {outside.name.tolist()}")
    seats.to_csv(CITIES_FILE, index=False)

    grid.save(GRID_FILE, g, mask=mask, water=water, elev=elev, elev_min=elev_min, slope=slope)
    print(f"wrote {GRID_FILE.name} ({GRID_FILE.stat().st_size / 1e6:.1f} MB) and {CITIES_FILE.name}")
    m = mask
    print(f"slope inside mask: mean-elev {slope_mean[m].mean():.2f} deg, valley-floor {slope[m].mean():.2f} deg; "
          f"cells > 5 deg: {(slope_mean[m] > 5).mean():.1%} vs {(slope[m] > 5).mean():.1%}")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    panels = [
        ("land mask (white) + county seats", np.where(mask, 1.0, 0.0), "gray", None),
        ("water fraction (OSM natural=water)", np.where(mask, water, np.nan), "Blues", (0, 1)),
        ("slope from mean elevation, deg", np.where(mask, slope_mean, np.nan), "magma", (0, 15)),
        ("slope from valley floor (used), deg", np.where(mask, slope, np.nan), "magma", (0, 15)),
    ]
    for ax, (title, arr, cmap, lim) in zip(axes.ravel(), panels):
        im = ax.imshow(arr, cmap=cmap, vmin=lim and lim[0], vmax=lim and lim[1], interpolation="nearest")
        ax.set_title(title)
        ax.set_xticks([])
        ax.set_yticks([])
        if lim:
            fig.colorbar(im, ax=ax, shrink=0.7)
    axes[0, 0].scatter(seats.col, seats.row, s=12, c="#ffd400", edgecolors="black", linewidths=0.5)
    fig.suptitle(f"Simulation inputs on the {g.width}x{g.height} grid, {g.cell / 1000:.0f} km/px")
    fig.tight_layout()
    fig.savefig(OUTPUTS / "validation" / "grid_layers.png", dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    main()
