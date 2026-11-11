"""The shared simulation grid: every layer (terrain, roads, cities, pheromone) is an array of this shape."""

from dataclasses import dataclass

import numpy as np

CRS = "EPSG:3844"                          # Stereo 70, metres
ROMANIA_LONLAT = (20.2, 43.6, 29.8, 48.3)  # W, S, E, N

# pyproj / rasterio are imported lazily: the cluster only needs load(), without the geo stack.


def _transformer(src, dst):
    from pyproj import Transformer

    return Transformer.from_crs(src, dst, always_xy=True)


def from_origin(west, north, xsize, ysize):
    from rasterio.transform import from_origin as f

    return f(west, north, xsize, ysize)


@dataclass(frozen=True)
class Grid:
    x0: float      # west edge, metres
    y0: float      # north edge, metres
    cell: float    # metres per pixel
    width: int
    height: int
    crs: str = CRS

    @property
    def shape(self):
        return (self.height, self.width)

    @property
    def transform(self):
        return from_origin(self.x0, self.y0, self.cell, self.cell)

    @property
    def extent(self):
        """(left, right, bottom, top) for matplotlib imshow."""
        return (self.x0, self.x0 + self.width * self.cell, self.y0 - self.height * self.cell, self.y0)

    def bounds_lonlat(self, pad_deg=0.0):
        t = _transformer(self.crs, "EPSG:4326")
        l, r, b, top = self.extent
        xs, ys = np.meshgrid(np.linspace(l, r, 20), np.linspace(b, top, 20))
        lon, lat = t.transform(xs.ravel(), ys.ravel())
        return (lon.min() - pad_deg, lat.min() - pad_deg, lon.max() + pad_deg, lat.max() + pad_deg)

    def to_pixel(self, lon, lat):
        """lon/lat (degrees) -> fractional (row, col)."""
        x, y = _transformer("EPSG:4326", self.crs).transform(lon, lat)
        return (self.y0 - np.asarray(y)) / self.cell, (np.asarray(x) - self.x0) / self.cell


def save(path, grid, **layers):
    """Write layers + the grid definition to one .npz (data/processed, committed to git)."""
    meta = dict(x0=grid.x0, y0=grid.y0, cell=grid.cell, width=grid.width, height=grid.height)
    np.savez_compressed(path, crs=np.array(grid.crs), **{f"grid_{k}": v for k, v in meta.items()}, **layers)


def load(path):
    """-> (Grid, {name: array}) as written by save()."""
    with np.load(path) as z:
        g = Grid(x0=float(z["grid_x0"]), y0=float(z["grid_y0"]), cell=float(z["grid_cell"]),
                 width=int(z["grid_width"]), height=int(z["grid_height"]), crs=str(z["crs"]))
        layers = {k: z[k] for k in z.files if not k.startswith("grid_") and k != "crs"}
    return g, layers


def coverage(grid, geoms, factor=10):
    """Fraction (0..1) of each cell covered by `geoms` (already in grid.crs).

    Rasterises at cell/factor and averages back, so thin features (the Danube at ~1 km) are not lost
    or exaggerated the way a single centre-point test would.
    """
    from rasterio.features import rasterize

    fine = from_origin(grid.x0, grid.y0, grid.cell / factor, grid.cell / factor)
    hi = rasterize(((g, 1) for g in geoms), out_shape=(grid.height * factor, grid.width * factor),
                   transform=fine, fill=0, dtype="uint8")
    return hi.reshape(grid.height, factor, grid.width, factor).mean(axis=(1, 3)).astype("float32")


def slope_deg(grid, elev):
    """Slope in degrees between neighbouring cells (central differences, metres / metres)."""
    gy, gx = np.gradient(np.nan_to_num(elev, nan=0.0), grid.cell)
    return np.degrees(np.arctan(np.hypot(gx, gy))).astype("float32")


def romania(cell_km=2.0):
    """Grid covering Romania's bounding box, snapped to whole cells."""
    t = _transformer("EPSG:4326", CRS)
    w, s, e, n = ROMANIA_LONLAT
    lon, lat = np.meshgrid(np.linspace(w, e, 50), np.linspace(s, n, 50))
    x, y = t.transform(lon.ravel(), lat.ravel())
    cell = cell_km * 1000
    x0, x1 = np.floor(x.min() / cell) * cell, np.ceil(x.max() / cell) * cell
    y0, y1 = np.floor(y.min() / cell) * cell, np.ceil(y.max() / cell) * cell
    return Grid(x0=x0, y0=y1, cell=cell, width=int((x1 - x0) / cell), height=int((y1 - y0) / cell))
