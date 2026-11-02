"""OpenStreetMap data loading for the flood analysis pipeline."""

from typing import Tuple

import geopandas as gpd
import osmnx as ox


def load_osm_data(
    place_name: str,
    search_dist: int = 2500,
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, tuple[float, float]]:
    """Load buildings and waterways around a geocoded place.

    The search order and fallback radii match the active loading cell in
    ``Project_Files/flood.ipynb``.
    """
    print(f"Geocoding '{place_name}' to a point...")
    try:
        center_point = ox.geocode(place_name)
    except Exception as error:
        print(f"Error geocoding '{place_name}': {error}")
        print("Please try a different or more specific place name.")
        raise

    print(f"Fetching features within {search_dist}m of the point...")

    buildings = ox.features_from_point(
        center_point=center_point,
        tags={"building": True},
        dist=search_dist,
    )
    print(f"Found {len(buildings)} buildings.")

    rivers = None
    for dist in [search_dist, 5000, 10000]:
        try:
            rivers = ox.features_from_point(
                center_point=center_point,
                tags={"waterway": True},
                dist=dist,
            )
            print(f"Found {len(rivers)} waterway features within {dist}m.")
            break
        except Exception:
            print(f"No waterways found within {dist}m, expanding search...")
            continue

    if rivers is None or rivers.empty:
        raise RuntimeError(
            "No waterway features found even at 10km radius. "
            "Cannot compute flood vulnerability."
        )

    return buildings, rivers, center_point
