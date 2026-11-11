"""Copernicus DEM GLO-90 tiles -> one mosaic, optionally resampled onto the simulation grid."""

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.merge import merge
from rasterio.warp import reproject

from slime import DATA_RAW

DEM_DIR = DATA_RAW / "dem_glo90"


def tiles():
    paths = sorted(DEM_DIR.glob("*.tif"))
    if not paths:
        raise FileNotFoundError(f"no DEM tiles in {DEM_DIR}; run scripts/download_data.py")
    return paths


def mosaic(bounds=None, res_deg=None):
    """Merged DEM in EPSG:4326. bounds=(W, S, E, N); res_deg coarsens it (average) to save memory."""
    srcs = [rasterio.open(p) for p in tiles()]
    try:
        arr, transform = merge(srcs, bounds=bounds, res=res_deg, nodata=np.nan, dtype="float32",
                               resampling=Resampling.average)
    finally:
        for s in srcs:
            s.close()
    return arr[0], transform


def to_grid(grid, res_deg=1 / 240, how=("average",)):
    """DEM resampled onto a Grid (see slime.data.grid). No-data cells are NaN.

    `how` lists rasterio resampling names; one array per name, e.g. ("average", "min").
    "min" keeps the valley floor of each cell: a 2 km cell holding a narrow valley stays low.
    """
    lon_w, lat_s, lon_e, lat_n = grid.bounds_lonlat(pad_deg=0.2)
    src, src_t = mosaic((lon_w, lat_s, lon_e, lat_n), res_deg=res_deg)
    outs = []
    for name in how:
        out = np.full(grid.shape, np.nan, dtype="float32")
        reproject(src, out, src_transform=src_t, src_crs="EPSG:4326", src_nodata=np.nan,
                  dst_transform=grid.transform, dst_crs=grid.crs, dst_nodata=np.nan,
                  resampling=Resampling[name])
        outs.append(out)
    return outs[0] if len(outs) == 1 else outs
