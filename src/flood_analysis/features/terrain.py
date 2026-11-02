"""Terrain feature engineering from a DEM."""

from typing import Any

import geopandas as gpd
import numpy as np
import rasterio
from numpy.typing import NDArray


def sample_raster_at_centroids(raster: NDArray[Any], gdf: gpd.GeoDataFrame, transform: Any) -> NDArray[Any]:
    """Sample raster values at representative building points."""
    points = gdf.geometry.representative_point()
    values = []
    nrows, ncols = raster.shape
    for pt in points:
        if pt is None or pt.is_empty or (not np.isfinite(pt.x)) or (not np.isfinite(pt.y)):
            values.append(np.nan)
            continue
        r, c = rasterio.transform.rowcol(transform, pt.x, pt.y)
        if (not np.isfinite(r)) or (not np.isfinite(c)):
            values.append(np.nan)
            continue
        r, c = int(r), int(c)
        if r < 0 or r >= nrows or c < 0 or c >= ncols:
            values.append(np.nan)
            continue
        values.append(raster[r, c])
    return np.array(values, dtype=float)


def sample_local_relief(
    dem_grid: NDArray[Any],
    gdf: gpd.GeoDataFrame,
    transform: Any,
    radius_px: int = 1,
) -> NDArray[Any]:
    """Sample local DEM elevation range around representative building points."""
    points = gdf.geometry.representative_point()
    values = []
    nrows, ncols = dem_grid.shape
    for pt in points:
        if pt is None or pt.is_empty or (not np.isfinite(pt.x)) or (not np.isfinite(pt.y)):
            values.append(np.nan)
            continue
        r, c = rasterio.transform.rowcol(transform, pt.x, pt.y)
        if (not np.isfinite(r)) or (not np.isfinite(c)):
            values.append(np.nan)
            continue
        r, c = int(r), int(c)
        if r < 0 or r >= nrows or c < 0 or c >= ncols:
            values.append(np.nan)
            continue
        r0, r1 = max(0, r - radius_px), min(nrows, r + radius_px + 1)
        c0, c1 = max(0, c - radius_px), min(ncols, c + radius_px + 1)
        win = dem_grid[r0:r1, c0:c1]
        values.append(np.nanmax(win) - np.nanmin(win))
    return np.array(values, dtype=float)


def add_terrain_features(
    buildings_dem_crs: gpd.GeoDataFrame,
    dem_crs: Any,
    dem_array: NDArray[Any],
    affine: Any,
    features_df: Any,
) -> tuple[NDArray[Any], NDArray[Any], gpd.GeoDataFrame, Any]:
    """Add ``slope_deg`` and ``local_relief_m`` using notebook calculations."""
    dem = np.array(dem_array, dtype=float)
    dem[~np.isfinite(dem)] = np.nan
    dem[dem <= -9999] = np.nan
    cell_x = float(abs(affine.a))
    cell_y = float(abs(affine.e))
    grad_y, grad_x = np.gradient(dem, cell_y, cell_x)
    slope_deg_grid = np.degrees(np.arctan(np.sqrt(grad_x**2 + grad_y**2)))

    if buildings_dem_crs.crs != dem_crs:
        buildings_dem_crs_temp = buildings_dem_crs.to_crs(dem_crs)
    else:
        buildings_dem_crs_temp = buildings_dem_crs
    features_df["slope_deg"] = sample_raster_at_centroids(
        slope_deg_grid, buildings_dem_crs_temp, affine)
    features_df["local_relief_m"] = sample_local_relief(
        dem, buildings_dem_crs_temp, affine, radius_px=1)
    return dem, slope_deg_grid, buildings_dem_crs_temp, features_df
