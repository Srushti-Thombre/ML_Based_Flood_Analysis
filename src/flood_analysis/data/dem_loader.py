"""Digital elevation model loading for the flood analysis pipeline."""

from pathlib import Path
from typing import Any, Tuple

import rasterio
from numpy.typing import NDArray


def load_dem(
    dem_path: str | Path,
) -> Tuple[NDArray[Any], Any, Any]:
    """Read the first DEM band and return it with its transform and CRS."""
    dem_path = Path(dem_path)

    try:
        with rasterio.open(dem_path) as src_dem:
            dem_array = src_dem.read(1)
            affine = src_dem.transform
            dem_crs = src_dem.crs
            print(f"\nDEM loaded successfully. CRS: {dem_crs}")
    except rasterio.errors.RasterioIOError:
        print(f"Error: Could not find or open {dem_path}.")
        print(
            "Please make sure you've downloaded the DEM and placed it "
            "in the correct folder."
        )
        raise

    return dem_array, affine, dem_crs
