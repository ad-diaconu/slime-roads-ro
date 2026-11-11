"""The shared simulation grid: every layer (terrain, roads, cities, pheromone) is an array of this shape."""

from dataclasses import dataclass

import numpy as np
from pyproj import Transformer
from rasterio.transform import from_origin

CRS = "EPSG:3844"                          # Stereo 70, metres
ROMANIA_LONLAT = (20.2, 43.6, 29.8, 48.3)  # W, S, E, N


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
        t = Transformer.from_crs(self.crs, "EPSG:4326", always_xy=True)
        l, r, b, top = self.extent
        xs, ys = np.meshgrid(np.linspace(l, r, 20), np.linspace(b, top, 20))
        lon, lat = t.transform(xs.ravel(), ys.ravel())
        return (lon.min() - pad_deg, lat.min() - pad_deg, lon.max() + pad_deg, lat.max() + pad_deg)

    def to_pixel(self, lon, lat):
        """lon/lat (degrees) -> fractional (row, col)."""
        x, y = Transformer.from_crs("EPSG:4326", self.crs, always_xy=True).transform(lon, lat)
        return (self.y0 - np.asarray(y)) / self.cell, (np.asarray(x) - self.x0) / self.cell


def romania(cell_km=2.0):
    """Grid covering Romania's bounding box, snapped to whole cells."""
    t = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
    w, s, e, n = ROMANIA_LONLAT
    lon, lat = np.meshgrid(np.linspace(w, e, 50), np.linspace(s, n, 50))
    x, y = t.transform(lon.ravel(), lat.ravel())
    cell = cell_km * 1000
    x0, x1 = np.floor(x.min() / cell) * cell, np.ceil(x.max() / cell) * cell
    y0, y1 = np.floor(y.min() / cell) * cell, np.ceil(y.max() / cell) * cell
    return Grid(x0=x0, y0=y1, cell=cell, width=int((x1 - x0) / cell), height=int((y1 - y0) / cell))
