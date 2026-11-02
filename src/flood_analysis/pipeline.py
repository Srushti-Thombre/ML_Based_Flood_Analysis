"""End-to-end flood vulnerability analysis pipeline."""

from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

from flood_analysis.data.dem_loader import load_dem
from flood_analysis.data.osm_loader import load_osm_data
from flood_analysis.features.distance import add_distance_to_river_feature
from flood_analysis.features.elevation import add_elevation_feature
from flood_analysis.features.hydrology import add_hydrology_features
from flood_analysis.features.historic import (
    estimate_future_years,
    load_historic_yearly_building_data,
)
from flood_analysis.features.terrain import add_terrain_features
from flood_analysis.models.clustering import run_clustering
from flood_analysis.reporting.report_generator import generate_report
from flood_analysis.utils.geo_utils import export_geopackage
from flood_analysis.visualization.interactive_map import (
    create_enhanced_interactive_map,
    create_interactive_map,
)
from flood_analysis.visualization.static_map import create_static_map
from flood_analysis.visualization.dashboard import create_dashboard


def run_pipeline(
    place_name: str = "Kurla, Mumbai, India",
    dem_path: str | Path = Path("Project_Files") / "kurla.tif",
    output_dir: str | Path = Path("Project_Files"),
    include_historic: bool = False,
    generate_report_output: bool = True,
    generate_dashboard_output: bool = True,
) -> dict[str, Any]:
    """Run the notebook workflow in its original operational order."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    buildings, rivers, center_point = load_osm_data(place_name)
    dem_array, affine, dem_crs = load_dem(Path(dem_path))

    buildings_dem_crs, elevation_stats, features_df = add_elevation_feature(
        buildings, dem_crs, dem_array, affine)
    buildings_proj, rivers_proj, all_rivers, features_df = (
        add_distance_to_river_feature(buildings, rivers, features_df))
    dem, slope_deg_grid, buildings_dem_crs_temp, features_df = add_terrain_features(
        buildings_dem_crs, dem_crs, dem_array, affine, features_df)
    metric_crs, b_metric, r_metric, major_rivers, major_union, drainage_gdf, densities, features_df = (
        add_hydrology_features(buildings_proj, rivers_proj, features_df, place_name))

    features_df.dropna(subset=["elevation", "dist_to_river"], inplace=True)
    buildings_with_features = buildings_proj.join(features_df, how="inner")
    if buildings_with_features.empty:
        raise RuntimeError("No buildings with valid features found. Check your DEM coverage.")

    (
        buildings_with_features, available_features, feature_columns, imputer,
        scaler, cluster_labels, kmeans, cluster_analysis, risk_mapping,
    ) = run_clustering(buildings_with_features)

    X_imputed = imputer.transform(
        buildings_with_features[available_features])
    X_clean = pd.DataFrame(
        X_imputed,
        columns=available_features,
        index=buildings_with_features.index,
    )
    X_scaled = scaler.transform(X_clean)
    evaluation_metrics = {
        "Silhouette": silhouette_score(X_scaled, cluster_labels),
        "Davies-Bouldin": davies_bouldin_score(X_scaled, cluster_labels),
        "Calinski-Harabasz": calinski_harabasz_score(
            X_scaled, cluster_labels),
    }

    historic_points = None
    historic_years = {}
    if include_historic:
        historic_years = load_historic_yearly_building_data(
            buildings_with_features)
        historic_years.update(estimate_future_years(historic_years))

    create_static_map(
        buildings_with_features, rivers_proj, place_name,
        output_dir / "flood_vulnerability_map.png")
    buildings_for_map, base_map = create_interactive_map(
        buildings_with_features, output_dir / "interactive_flood_map.html")
    export_geopackage(
        buildings_for_map, output_dir / "flood_vulnerability_data.gpkg")

    buildings_for_enhanced_map, enhanced_map = create_enhanced_interactive_map(
        buildings_with_features,
        output_dir / "interactive_flood_map_enhanced.html",
    )
    report_columns = [
        c for c in buildings_for_enhanced_map.columns if c != "geometry"]
    buildings_for_enhanced_map[report_columns].to_csv(
        output_dir / "flood_vulnerability_feature_report.csv", index=False)
    export_geopackage(
        buildings_for_enhanced_map,
        output_dir / "flood_vulnerability_data_enhanced.gpkg")

    dashboard_path = None
    if generate_dashboard_output:
        dashboard_path = create_dashboard(
            buildings_with_features,
            output_dir / "flood_risk_dashboard.html",
            historic_years=historic_years,
        )

    results = {
        "place_name": place_name,
        "dem_path": Path(dem_path),
        "output_dir": output_dir,
        "buildings": buildings,
        "rivers": rivers,
        "center_point": center_point,
        "dem_array": dem_array,
        "affine": affine,
        "dem_crs": dem_crs,
        "buildings_dem_crs": buildings_dem_crs,
        "elevation_stats": elevation_stats,
        "features_df": features_df,
        "buildings_proj": buildings_proj,
        "rivers_proj": rivers_proj,
        "all_rivers": all_rivers,
        "dem": dem,
        "slope_deg_grid": slope_deg_grid,
        "buildings_dem_crs_temp": buildings_dem_crs_temp,
        "metric_crs": metric_crs,
        "b_metric": b_metric,
        "r_metric": r_metric,
        "major_rivers": major_rivers,
        "major_union": major_union,
        "drainage_gdf": drainage_gdf,
        "densities": densities,
        "buildings_with_features": buildings_with_features,
        "available_features": available_features,
        "feature_columns": feature_columns,
        "imputer": imputer,
        "scaler": scaler,
        "cluster_labels": cluster_labels,
        "kmeans": kmeans,
        "cluster_analysis": cluster_analysis,
        "risk_mapping": risk_mapping,
        "historic_points": historic_points,
        "include_historic": include_historic,
        "historic_years": historic_years,
        "dashboard_path": dashboard_path,
        "evaluation_metrics": evaluation_metrics,
        "buildings_for_map": buildings_for_map,
        "base_map": base_map,
        "buildings_for_enhanced_map": buildings_for_enhanced_map,
        "enhanced_map": enhanced_map,
    }
    if generate_report_output:
        results["report_paths"] = generate_report(results, output_dir)
    return results
