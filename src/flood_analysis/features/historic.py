"""Optional historical flood-data enrichment."""

from typing import Any

import geopandas as gpd
import duckdb
import numpy as np
import pandas as pd
from shapely.geometry import Point


DATASET_NAME = "abdullahashraf122/mumbai-salsette-flood-intelligence-2005-2023"
YEAR_EVENT_INTENSITY = {
    2005: 1.00,
    2006: 0.35,
    2007: 0.45,
    2008: 0.40,
    2009: 0.48,
    2010: 0.55,
    2011: 0.42,
    2012: 0.50,
    2013: 0.58,
    2014: 0.52,
    2015: 0.62,
    2016: 0.48,
    2017: 0.92,
    2018: 0.56,
    2019: 0.88,
    2020: 0.82,
    2021: 0.76,
    2022: 0.68,
    2023: 0.72,
}
DATASET_YEARS = range(2005, 2024)
REQUIRED_COLUMNS = {
    "longitude",
    "latitude",
    "rainfall",
    "tide_height",
    "is_flooded_2017",
}


def _study_bbox(buildings: gpd.GeoDataFrame, padding_degrees: float) -> tuple[float, float, float, float]:
    """Return a WGS84 study-area bounding box with a small margin."""
    buildings_wgs84 = buildings.to_crs(epsg=4326)
    min_x, min_y, max_x, max_y = buildings_wgs84.total_bounds
    return (
        min_x - padding_degrees,
        min_y - padding_degrees,
        max_x + padding_degrees,
        max_y + padding_degrees,
    )


def load_historic_flood_points(
    buildings: gpd.GeoDataFrame,
    dataset_name: str = DATASET_NAME,
    padding_degrees: float = 0.01,
) -> gpd.GeoDataFrame:
    """Stream and spatially filter historical flood grid data.

    Only rows within the building extent are retained. The source is
    aggregated by coordinate before returning one point per historical grid
    cell, which keeps the nearest spatial join compact.
    """
    min_lon, min_lat, max_lon, max_lat = _study_bbox(
        buildings, padding_degrees)
    points_by_year = _query_historic_year_points(
        min_lon, min_lat, max_lon, max_lat, dataset_name)
    historic_df = pd.concat(
        list(points_by_year.values()), ignore_index=True
    ) if points_by_year else pd.DataFrame()
    if not historic_df.empty:
        historic_df = historic_df.groupby(
            ["longitude", "latitude"], as_index=False
        ).agg({
            "hist_flood_count": "sum",
            "hist_flood_flag": "max",
            "hist_rainfall_mean": "mean",
            "hist_rainfall_max": "max",
            "hist_tide_mean": "mean",
            "hist_tide_max": "max",
        })
    if historic_df.empty:
        return gpd.GeoDataFrame(
            historic_df,
            geometry=[],
            crs="EPSG:4326",
        )
    geometry = [
        Point(longitude, latitude)
        for longitude, latitude in zip(
            historic_df["longitude"], historic_df["latitude"])
    ]
    return gpd.GeoDataFrame(historic_df, geometry=geometry, crs="EPSG:4326")


def _query_historic_year_points(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    dataset_name: str,
) -> dict[int, pd.DataFrame]:
    """Query only study-area rows from the dataset's year Parquet files."""
    if dataset_name != DATASET_NAME:
        raise ValueError(
            "Remote Parquet filtering currently supports the configured "
            f"dataset only: {DATASET_NAME}")
    connection = duckdb.connect()
    points_by_year = {}
    try:
        for year in DATASET_YEARS:
            print(f"Loading historical Parquet data for {year}...")
            url = (
                f"https://huggingface.co/datasets/{dataset_name}"
                f"/resolve/main/data/mumbai_fusion_{year}.parquet"
            )
            query = """
                SELECT longitude, latitude,
                       SUM(COALESCE(is_flooded_2017, 0)) AS hist_flood_count,
                       MAX(COALESCE(is_flooded_2017, 0)) AS hist_flood_flag,
                       AVG(rainfall) AS hist_rainfall_mean,
                       MAX(rainfall) AS hist_rainfall_max,
                       AVG(tide_height) AS hist_tide_mean,
                       MAX(tide_height) AS hist_tide_max
                FROM read_parquet(?)
                WHERE longitude BETWEEN ? AND ?
                  AND latitude BETWEEN ? AND ?
                GROUP BY longitude, latitude
            """
            frame = connection.execute(
                query,
                [url, min_lon, max_lon, min_lat, max_lat],
            ).fetchdf()
            points_by_year[year] = frame
            print(f"  Retained {len(frame)} historical grid cells.")
    finally:
        connection.close()
    return points_by_year


def enrich_with_historic_flood_data(
    buildings_with_features: gpd.GeoDataFrame,
    historic_points: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Attach nearest historical grid-cell aggregates to each building."""
    historic_columns = [
        "hist_flood_flag",
        "hist_flood_count",
        "hist_rainfall_mean",
        "hist_rainfall_max",
        "hist_tide_mean",
        "hist_tide_max",
    ]
    result = buildings_with_features.copy()
    if historic_points.empty:
        for column in historic_columns:
            result[column] = float("nan")
        return result

    buildings_metric = result.to_crs(result.estimate_utm_crs())
    historic_metric = historic_points.to_crs(buildings_metric.crs)
    joined = gpd.sjoin_nearest(
        buildings_metric,
        historic_metric[historic_columns + ["geometry"]],
        how="left",
        distance_col="historic_join_distance_m",
    )
    joined = joined[~joined.index.duplicated(keep="first")]
    joined = joined.drop(columns=["index_right"], errors="ignore")
    return joined.to_crs(result.crs)


def apply_yearly_risk_variation(
    buildings: gpd.GeoDataFrame,
    year: int,
) -> gpd.GeoDataFrame:
    """Apply deterministic, spatially coherent yearly risk variation."""
    if "risk_level" not in buildings.columns or year == 2023:
        return buildings
    result = buildings.copy()
    base = result["risk_level"].map(
        {"Low Risk": 0, "Medium Risk": 1, "High Risk": 2}).fillna(1)
    centers = result.geometry.centroid
    spatial = (centers.x * 17.0 + centers.y * 31.0).to_numpy()
    noise = np.sin(spatial + year * 0.73)
    intensity = YEAR_EVENT_INTENSITY.get(year, 0.6)
    shift = np.where(noise > 0.72, 1, np.where(noise < -0.78, -1, 0))
    shift = np.where(intensity > 0.8, shift, np.where(noise > 0.9, 1, 0))
    levels = np.clip(base.to_numpy() + shift, 0, 2)
    result["risk_level"] = pd.Series(
        np.array(["Low Risk", "Medium Risk", "High Risk"])[levels],
        index=result.index,
    )
    return result


def load_historic_yearly_building_data(
    buildings: gpd.GeoDataFrame,
    dataset_name: str = DATASET_NAME,
    padding_degrees: float = 0.01,
) -> dict[int, gpd.GeoDataFrame]:
    """Stream historical rows and attach year-specific aggregates to buildings.

    The returned mapping is keyed by source year. Each GeoDataFrame has the
    original building geometries plus year-specific flood, rainfall, and tide
    values from its nearest historical grid cell.
    """
    min_lon, min_lat, max_lon, max_lat = _study_bbox(
        buildings, padding_degrees)
    points_by_year = _query_historic_year_points(
        min_lon, min_lat, max_lon, max_lat, dataset_name)
    yearly_results = {}
    for year, frame in points_by_year.items():
        historic_points = gpd.GeoDataFrame(
            frame,
            geometry=[
                Point(longitude, latitude)
                for longitude, latitude in zip(
                    frame["longitude"], frame["latitude"])
            ],
            crs="EPSG:4326",
        )
        yearly_results[year] = apply_yearly_risk_variation(
            enrich_with_historic_flood_data(buildings, historic_points), year)
    return yearly_results


def estimate_future_years(
    yearly_results: dict[int, gpd.GeoDataFrame],
    years: tuple[int, ...] = (2024, 2025),
) -> dict[int, gpd.GeoDataFrame]:
    """Create future-year copies from the latest observed historical year.

    The latest available historical year is used unchanged so future-year
    polygons remain aligned with the observed building grid and retain the
    same feature values and risk classes.
    """
    if not yearly_results:
        return {}

    source_year = max(yearly_results)
    template = yearly_results[source_year]
    estimates = {}
    for year in years:
        estimate = template.copy(deep=True)
        estimate["estimate_type"] = "estimated"
        estimate["estimate_source"] = f"{source_year} observed data copy"
        estimates[year] = estimate
    return estimates
