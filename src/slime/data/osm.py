"""Read roads and city points from the Geofabrik OSM extract (data/raw/romania-latest.osm.pbf)."""

import pandas as pd
from pyrosm import OSM

from slime import DATA_RAW, ROOT

PBF = DATA_RAW / "romania-latest.osm.pbf"
MAIN_ROADS = ["motorway", "trunk", "primary"]


def load_roads(classes=MAIN_ROADS):
    """Main road lines (EPSG:4326) with columns highway, ref, name, geometry."""
    osm = OSM(str(PBF))
    gdf = osm.get_data_by_custom_criteria(
        custom_filter={"highway": list(classes)}, filter_type="keep",
        keep_nodes=False, keep_ways=True, keep_relations=False,
    )
    keep = [c for c in ("id", "highway", "ref", "name", "geometry") if c in gdf.columns]
    return gdf[keep].reset_index(drop=True)


def load_places():
    """City / town points (EPSG:4326) with name and population tags."""
    osm = OSM(str(PBF))
    gdf = osm.get_data_by_custom_criteria(
        custom_filter={"place": ["city", "town"]}, filter_type="keep",
        keep_nodes=True, keep_ways=False, keep_relations=False,
        extra_attributes=["name", "population", "population:date"],  # pyrosm drops tags not asked for
    )
    keep = [c for c in ("name", "place", "population", "population:date", "lon", "lat", "geometry")
            if c in gdf.columns]
    return gdf[keep].reset_index(drop=True)


def county_seats(places=None):
    """The 42 food sources: data/county_seats.csv matched by name to OSM city/town nodes."""
    seats = pd.read_csv(ROOT / "data" / "county_seats.csv")
    places = load_places() if places is None else places
    places = places.assign(population=pd.to_numeric(places["population"], errors="coerce"))
    # a name can repeat (villages called like a city); keep the most populous city/town node
    best = places.sort_values("population", ascending=False).drop_duplicates("name")
    merged = seats.merge(best, on="name", how="left")
    missing = merged[merged["lon"].isna()]["name"].tolist()
    if missing:
        raise ValueError(f"county seats not found in OSM: {missing}")
    return merged[["name", "county", "place", "population", "population:date", "lat", "lon"]]
