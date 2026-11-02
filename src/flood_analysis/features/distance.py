"""Distance-based feature engineering."""

from typing import Any

import geopandas as gpd
import osmnx as ox
import pandas as pd


def add_distance_to_river_feature(
    buildings: gpd.GeoDataFrame,
    rivers: gpd.GeoDataFrame,
    features_df: pd.DataFrame,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, Any, pd.DataFrame]:
    """Calculate distance from each building to the nearest waterway.

    The projection and geometry operations are identical to the notebook.
    ``features_df`` is updated in place with the ``dist_to_river`` column.
    """
    buildings_proj = ox.projection.project_gdf(buildings, to_latlong=False)
    rivers_proj = ox.projection.project_gdf(rivers, to_crs=buildings_proj.crs)
    all_rivers = rivers_proj.geometry.union_all()
    features_df["dist_to_river"] = buildings_proj.geometry.distance(all_rivers)

    return buildings_proj, rivers_proj, all_rivers, features_df
