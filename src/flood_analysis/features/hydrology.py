"""Hydrology feature engineering."""

from typing import Any

import geopandas as gpd
import numpy as np
import osmnx as ox


def add_hydrology_features(
    buildings_proj: gpd.GeoDataFrame,
    rivers_proj: gpd.GeoDataFrame,
    features_df: Any,
    place_name: str,
) -> tuple[Any, gpd.GeoDataFrame, gpd.GeoDataFrame, Any, Any, Any, Any, Any]:
    """Add major-waterway, waterway-density, and drainage distances."""
    metric_crs = buildings_proj.estimate_utm_crs()
    b_metric = buildings_proj.to_crs(metric_crs)
    r_metric = rivers_proj.to_crs(metric_crs)
    river_lengths = r_metric.geometry.length
    length_threshold = river_lengths.quantile(0.75)
    major_rivers = r_metric[river_lengths >= length_threshold].copy()
    if major_rivers.empty:
        major_rivers = r_metric.copy()
    major_union = major_rivers.geometry.union_all()
    features_df["dist_to_major_waterway"] = b_metric.geometry.distance(
        major_union).values

    buffer_radius_m = 300.0
    circle_area = np.pi * (buffer_radius_m ** 2)
    river_geoms = r_metric.geometry
    sindex = river_geoms.sindex if (
        hasattr(river_geoms, "sindex") and river_geoms.sindex is not None) else None
    densities = []
    for geom in b_metric.geometry:
        buf = geom.buffer(buffer_radius_m)
        if sindex is not None:
            candidate_idx = list(sindex.intersection(buf.bounds))
            candidates = river_geoms.iloc[candidate_idx] if candidate_idx else river_geoms.iloc[[]]
        else:
            candidates = river_geoms
        if len(candidates) == 0:
            densities.append(0.0)
            continue
        clipped = candidates.intersection(buf)
        total_len_m = clipped.length.sum()
        densities.append(float(total_len_m / circle_area))
    features_df["waterway_density_300m"] = densities

    drainage_gdf = None
    try:
        drainage_tags = {"waterway": ["drain", "ditch", "canal"]}
        drainage_gdf = ox.features_from_place(place_name, tags=drainage_tags)
        if drainage_gdf is not None and not drainage_gdf.empty:
            drainage_gdf = drainage_gdf.to_crs(metric_crs)
    except Exception:
        pass
    if (drainage_gdf is None or drainage_gdf.empty):
        r_metric_drain = rivers_proj.to_crs(metric_crs)
        if "waterway" in r_metric_drain.columns:
            drainage_mask = r_metric_drain["waterway"].astype(
                str).str.lower().isin(["drain", "ditch", "canal"])
            drainage_gdf = r_metric_drain[drainage_mask].copy()
            if drainage_gdf.empty:
                drainage_gdf = None
    if drainage_gdf is None or drainage_gdf.empty:
        features_df["dist_to_drainage_m"] = np.nan
    else:
        drainage_gdf = drainage_gdf[drainage_gdf.geometry.notnull()].copy()
        drainage_union = drainage_gdf.geometry.union_all()
        features_df["dist_to_drainage_m"] = b_metric.geometry.distance(
            drainage_union).values
    return metric_crs, b_metric, r_metric, major_rivers, major_union, drainage_gdf, densities, features_df
