"""Download the raw geodata into data/raw/ (gitignored).

- OSM extract for Romania from Geofabrik (~330 MB), checked against Geofabrik's .md5.
- Copernicus DEM GLO-90 tiles covering Romania (lat 43-48, lon 20-29) from AWS Open Data, no account needed.
  Tiles that are all sea do not exist on the bucket (404) and are skipped.

Writes data/raw/manifest.json with the download date and file sizes, because romania-latest changes daily.

Usage:  uv run python scripts/download_data.py [--only osm|dem]
"""

import argparse
import datetime as dt
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

import requests

from slime import DATA_RAW

OSM_URL = "https://download.geofabrik.de/europe/romania-latest.osm.pbf"
DEM_URL = ("https://copernicus-dem-90m.s3.amazonaws.com/{n}/{n}.tif")
DEM_NAME = "Copernicus_DSM_COG_30_N{lat:02d}_00_E{lon:03d}_00_DEM"
LATS = range(43, 49)   # tiles are named by their south-west corner; Romania spans ~43.6-48.3 N
LONS = range(20, 30)   # and ~20.3-29.7 E


def fetch(url, dest, chunk=1 << 20):
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=60) as r:
        if r.status_code in (403, 404):
            return None
        r.raise_for_status()
        md5 = hashlib.md5()
        with open(tmp, "wb") as f:
            for block in r.iter_content(chunk):
                f.write(block)
                md5.update(block)
    tmp.replace(dest)
    return md5.hexdigest()


def download_osm():
    dest = DATA_RAW / "romania-latest.osm.pbf"
    expected = requests.get(OSM_URL + ".md5", timeout=30).text.split()[0]
    if dest.exists() and hashlib.md5(dest.read_bytes()).hexdigest() == expected:
        print(f"osm: up to date ({dest.stat().st_size / 1e6:.0f} MB)")
    else:
        print("osm: downloading ~330 MB ...")
        got = fetch(OSM_URL, dest)
        if got != expected:
            raise SystemExit(f"osm: md5 mismatch ({got} != {expected})")
        print(f"osm: ok ({dest.stat().st_size / 1e6:.0f} MB, md5 verified)")
    return {"url": OSM_URL, "md5": expected, "bytes": dest.stat().st_size}


def download_dem():
    out = DATA_RAW / "dem_glo90"
    out.mkdir(parents=True, exist_ok=True)

    def one(lat, lon):
        name = DEM_NAME.format(lat=lat, lon=lon)
        dest = out / f"{name}.tif"
        if dest.exists():
            return name, dest.stat().st_size
        return name, (dest.stat().st_size if fetch(DEM_URL.format(n=name), dest) else None)

    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda ll: one(*ll), [(a, b) for a in LATS for b in LONS]))
    tiles = {n: s for n, s in results if s}
    print(f"dem: {len(tiles)} tiles ({sum(tiles.values()) / 1e6:.0f} MB), "
          f"{len(results) - len(tiles)} missing on the bucket (sea / outside coverage)")
    return {"url": DEM_URL.format(n="<tile>"), "tiles": sorted(tiles), "bytes": sum(tiles.values())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["osm", "dem"])
    a = ap.parse_args()
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = DATA_RAW / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if a.only in (None, "dem"):
        manifest["dem"] = download_dem()
    if a.only in (None, "osm"):
        manifest["osm"] = download_osm()
    manifest["downloaded"] = dt.date.today().isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
