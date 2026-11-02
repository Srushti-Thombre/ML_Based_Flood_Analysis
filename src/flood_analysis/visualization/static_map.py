"""Static vulnerability map generation."""

from pathlib import Path
from typing import Any

import geopandas as gpd
import matplotlib.pyplot as plt


def create_static_map(
    buildings_with_features: gpd.GeoDataFrame,
    rivers_proj: gpd.GeoDataFrame,
    place_name: str,
    output_path: Path,
) -> tuple[Any, Any]:
    """Create and save the notebook's PNG vulnerability map."""
    fig, ax = plt.subplots(figsize=(12, 12))
    buildings_with_features.plot(
        ax=ax,
        column="risk_level",
        categorical=True,
        legend=True,
        legend_kwds={"title": "Flood Vulnerability"},
        cmap="Reds_r",
    )
    rivers_proj.plot(ax=ax, color="blue", linewidth=2)
    ax.set_title(f"Flood Vulnerability Map for {place_name}")
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(Path(output_path))
    return fig, ax
