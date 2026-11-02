"""Elevation feature engineering."""

from typing import Any

import geopandas as gpd
import pandas as pd
import rasterstats
from numpy.typing import NDArray


def add_elevation_feature(
    buildings: gpd.GeoDataFrame,
    dem_crs: Any,
    dem_array: NDArray[Any],
    affine: Any,
) -> tuple[gpd.GeoDataFrame, list[dict[str, Any]], pd.DataFrame]:
    """Calculate mean DEM elevation for each building.

    This preserves the notebook's reprojection, zonal-statistics parameters,
    feature index, and output column name.
    """
    buildings_dem_crs = buildings.to_crs(dem_crs)
    elevation_stats = rasterstats.zonal_stats(
        buildings_dem_crs.geometry,
        dem_array,
        affine=affine,
        stats=["mean"],
        nodata=-9999,
    )

    features_df = pd.DataFrame(elevation_stats, index=buildings_dem_crs.index)
    features_df.rename(columns={"mean": "elevation"}, inplace=True)

    return buildings_dem_crs, elevation_stats, features_df
