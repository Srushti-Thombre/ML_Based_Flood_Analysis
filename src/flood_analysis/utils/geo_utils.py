"""Shared geospatial helpers."""

from pathlib import Path
from typing import Any

import geopandas as gpd


def to_wgs84(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Return a GeoDataFrame in the notebook's EPSG:4326 map CRS."""
    return gdf.to_crs(epsg=4326)


def export_geopackage(gdf: gpd.GeoDataFrame, output_path: Path) -> None:
    """Export a GeoDataFrame using the notebook's GPKG driver."""
    gdf.to_file(Path(output_path), driver="GPKG")
