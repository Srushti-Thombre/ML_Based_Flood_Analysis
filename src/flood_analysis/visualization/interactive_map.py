"""Folium map generation."""

from pathlib import Path

import geopandas as gpd
import folium


def create_interactive_map(
    buildings_with_features: gpd.GeoDataFrame,
    output_path: Path,
) -> tuple[gpd.GeoDataFrame, folium.Map]:
    """Create and save the notebook's base interactive map."""
    buildings_for_map = buildings_with_features.to_crs(epsg=4326)
    if buildings_for_map.empty:
        raise RuntimeError("No building data to map.")
    map_center_point = buildings_for_map.geometry.union_all().centroid
    map_center = [map_center_point.y, map_center_point.x]
    m = folium.Map(
        location=map_center,
        zoom_start=15,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), Esri (Thailand), TomTom, 2012",
    )
    color_map = {"High Risk": "red", "Medium Risk": "orange", "Low Risk": "green"}

    def style_function(feature):
        risk = feature["properties"]["risk_level"]
        return {
            "fillColor": color_map.get(risk, "gray"),
            "color": "black",
            "weight": 0.5,
            "fillOpacity": 0.7,
        }

    folium.GeoJson(
        buildings_for_map,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=["risk_level", "elevation", "dist_to_river"],
            aliases=["Risk Level:", "Elevation (m):", "Distance to River (m):"],
            style=("background-color: white; color: black; font-family: arial; "
                   "font-size: 12px; padding: 10px;"),
        ),
    ).add_to(m)
    folium.LayerControl().add_to(m)
    m.save(Path(output_path))
    return buildings_for_map, m


def create_enhanced_interactive_map(
    buildings_with_features: gpd.GeoDataFrame,
    output_path: Path,
) -> tuple[gpd.GeoDataFrame, folium.Map]:
    """Create the notebook's filtered, risk-layered interactive map."""
    enhanced_columns = [
        "risk_level", "elevation", "dist_to_river", "dist_to_drainage_m",
        "slope_deg", "local_relief_m", "dist_to_major_waterway",
        "waterway_density_300m", "geometry",
        "hist_flood_flag", "hist_flood_count", "hist_rainfall_mean",
        "hist_rainfall_max", "hist_tide_mean", "hist_tide_max",
    ]
    available_columns = [
        c for c in enhanced_columns if c in buildings_with_features.columns]
    buildings_for_enhanced_map = buildings_with_features[available_columns].to_crs(
        epsg=4326).copy()
    center_point = buildings_for_enhanced_map.geometry.union_all().centroid
    m2 = folium.Map(
        location=[center_point.y, center_point.x],
        zoom_start=15,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), Esri (Thailand), TomTom, 2012",
    )
    risk_order = ["High Risk", "Medium Risk", "Low Risk"]
    risk_colors = {"High Risk": "red", "Medium Risk": "orange", "Low Risk": "green"}
    tooltip_fields = [
        c for c in [
            "risk_level", "elevation", "dist_to_river", "dist_to_drainage_m",
            "slope_deg", "local_relief_m", "dist_to_major_waterway",
            "waterway_density_300m",
            "hist_flood_flag", "hist_flood_count", "hist_rainfall_mean",
            "hist_rainfall_max", "hist_tide_mean", "hist_tide_max",
        ] if c in buildings_for_enhanced_map.columns
    ]
    tooltip_aliases = [f"{c}:" for c in tooltip_fields]
    for risk in risk_order:
        subset = buildings_for_enhanced_map[
            buildings_for_enhanced_map["risk_level"] == risk]
        if subset.empty:
            continue
        layer = folium.FeatureGroup(name=risk, show=True)
        folium.GeoJson(
            subset,
            style_function=lambda feature, rc=risk_colors[risk]: {
                "fillColor": rc, "color": "black", "weight": 0.5,
                "fillOpacity": 0.7,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=tooltip_fields, aliases=tooltip_aliases,
                localize=True, sticky=False,
            ),
        ).add_to(layer)
        layer.add_to(m2)
    folium.LayerControl().add_to(m2)
    m2.save(Path(output_path))
    return buildings_for_enhanced_map, m2
