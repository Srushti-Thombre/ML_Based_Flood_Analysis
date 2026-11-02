"""Generate dynamic HTML and PDF reports from pipeline results."""

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


VERSION = "0.1.0"
REPORT_HTML_NAME = "flood_analysis_report.html"
REPORT_PDF_NAME = "flood_analysis_report.pdf"


def _format_value(value: Any) -> str:
    if pd.isna(value):
        return "N/A"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.3f}"
    return str(value)


def _feature_summary(gdf: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    rows = []
    for feature in features:
        if feature in gdf.columns:
            values = pd.to_numeric(gdf[feature], errors="coerce").dropna()
            if not values.empty:
                rows.append({
                    "Feature": feature,
                    "Mean": values.mean(),
                    "Median": values.median(),
                    "Min": values.min(),
                    "Max": values.max(),
                })
    return pd.DataFrame(rows)


def _risk_distribution(gdf: pd.DataFrame) -> pd.DataFrame:
    if "risk_level" not in gdf.columns:
        return pd.DataFrame(columns=["Risk level", "Buildings", "Percentage"])
    counts = gdf["risk_level"].value_counts()
    total = len(gdf)
    return pd.DataFrame([
        {
            "Risk level": risk,
            "Buildings": int(counts.get(risk, 0)),
            "Percentage": (counts.get(risk, 0) / total * 100) if total else 0,
        }
        for risk in ("High Risk", "Medium Risk", "Low Risk")
    ])


def _risk_comparison(gdf: pd.DataFrame) -> pd.DataFrame:
    rows = []
    numeric_features = [
        ("Mean elevation (m)", "elevation"),
        ("Mean river distance (m)", "dist_to_river"),
        ("Mean slope (degrees)", "slope_deg"),
        ("Mean local relief (m)", "local_relief_m"),
        ("Mean major waterway distance (m)", "dist_to_major_waterway"),
        ("Mean drainage distance (m)", "dist_to_drainage_m"),
    ]
    for risk in ("High Risk", "Medium Risk", "Low Risk"):
        subset = gdf[gdf.get("risk_level", pd.Series(index=gdf.index)).eq(risk)]
        row = {"Risk level": risk, "Buildings": len(subset)}
        for label, column in numeric_features:
            row[label] = (
                pd.to_numeric(subset[column], errors="coerce").mean()
                if column in subset else np.nan
            )
        if "hist_flood_flag" in subset:
            flags = pd.to_numeric(subset["hist_flood_flag"], errors="coerce")
            row["Historic overlap (%)"] = flags.gt(0).mean() * 100
        rows.append(row)
    return pd.DataFrame(rows)


def _spatial_analysis(gdf: pd.DataFrame) -> pd.DataFrame:
    if "dist_to_river" not in gdf.columns:
        return pd.DataFrame()
    distance = pd.to_numeric(gdf["dist_to_river"], errors="coerce")
    bands = pd.cut(
        distance,
        bins=[-np.inf, 100, 250, 500, np.inf],
        labels=["0-100 m", "100-250 m", "250-500 m", "500+ m"],
    )
    grouped = gdf.assign(_distance_band=bands).groupby(
        "_distance_band", observed=False)
    result = grouped.size().rename("Buildings").reset_index()
    result.columns = ["Distance to river", "Buildings"]
    if "risk_level" in gdf.columns:
        high = grouped["risk_level"].apply(lambda values: values.eq("High Risk").sum())
        result["High Risk buildings"] = high.to_numpy()
    return result


def _priority_areas(gdf: pd.DataFrame) -> pd.DataFrame:
    if "risk_level" not in gdf.columns:
        return pd.DataFrame()
    high = gdf["risk_level"].eq("High Risk")
    historic = (
        pd.to_numeric(gdf["hist_flood_flag"], errors="coerce").fillna(0).gt(0)
        if "hist_flood_flag" in gdf.columns else pd.Series(False, index=gdf.index)
    )
    close = (
        pd.to_numeric(gdf["dist_to_river"], errors="coerce").le(100)
        if "dist_to_river" in gdf.columns else pd.Series(False, index=gdf.index)
    )
    categories = {
        "Immediate priority (High Risk + historic overlap)": high & historic,
        "High priority (High Risk + within 100 m of river)": high & close,
        "Monitoring priority (Medium Risk + historic overlap)":
            gdf["risk_level"].eq("Medium Risk") & historic,
        "Lower priority (Low Risk + no historic overlap)":
            gdf["risk_level"].eq("Low Risk") & ~historic,
    }
    total = len(gdf)
    return pd.DataFrame([
        {
            "Priority category": name,
            "Buildings": int(mask.sum()),
            "Percentage": float(mask.mean() * 100) if total else 0,
        }
        for name, mask in categories.items()
    ])


def _key_findings(
    gdf: pd.DataFrame,
    distribution: pd.DataFrame,
    historic: dict[str, Any] | None,
) -> list[str]:
    findings = []
    if distribution.empty:
        findings.append("Risk classifications were not available for this run.")
        return findings
    largest = distribution.loc[distribution["Buildings"].idxmax()]
    findings.append(
        f"{largest['Risk level']} is the largest group with "
        f"{int(largest['Buildings'])} buildings ({largest['Percentage']:.1f}%).")
    comparison = _risk_comparison(gdf)
    if not comparison.empty and "Mean elevation (m)" in comparison:
        valid = comparison.dropna(subset=["Mean elevation (m)"])
        if not valid.empty:
            row = valid.loc[valid["Mean elevation (m)"].idxmin()]
            findings.append(
                f"{row['Risk level']} has the lowest mean elevation "
                f"({_format_value(row['Mean elevation (m)'])} m).")
    if historic is not None:
        pct = historic["flooded_count"] / historic["total_count"] * 100 \
            if historic["total_count"] else 0
        findings.append(
            f"{historic['flooded_count']} buildings ({pct:.1f}%) overlap "
            "historically flooded grid cells.")
    spatial = _spatial_analysis(gdf)
    if not spatial.empty and "High Risk buildings" in spatial:
        row = spatial.loc[spatial["High Risk buildings"].idxmax()]
        findings.append(
            f"The greatest number of High Risk buildings is within the "
            f"{row['Distance to river']} river-distance band.")
    return findings


def _recommendations(gdf: pd.DataFrame) -> list[str]:
    recommendations = [
        "Prioritize field inspection and mitigation planning for High Risk buildings.",
        "Validate model classifications against municipal flood records and verified annual observations.",
        "Use updated DEM, drainage, and waterway data when repeating the assessment.",
    ]
    if "dist_to_river" in gdf.columns:
        close = pd.to_numeric(gdf["dist_to_river"], errors="coerce").le(100).sum()
        recommendations.insert(
            1, f"Review the {int(close)} buildings located within 100 m of a river or waterway.")
    if "hist_flood_flag" in gdf.columns:
        overlap = pd.to_numeric(gdf["hist_flood_flag"], errors="coerce").gt(0).sum()
        recommendations.insert(
            1, f"Prioritize the {int(overlap)} buildings with historic flood overlap.")
    return recommendations


def _create_charts(
    gdf: pd.DataFrame,
    distribution: pd.DataFrame,
    output_dir: Path,
) -> dict[str, Path]:
    paths = {}
    if not distribution.empty:
        path = output_dir / "report_risk_distribution.png"
        fig, ax = plt.subplots(figsize=(6, 3.2))
        ax.bar(distribution["Risk level"], distribution["Buildings"],
               color=["#d73027", "#fc8d59", "#1a9850"])
        ax.set_ylabel("Buildings")
        ax.set_title("Risk distribution")
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        paths["distribution"] = path
    spatial = _spatial_analysis(gdf)
    if not spatial.empty:
        path = output_dir / "report_spatial_bands.png"
        fig, ax = plt.subplots(figsize=(6, 3.2))
        ax.bar(spatial["Distance to river"], spatial["Buildings"], color="#2d7f9d")
        ax.set_ylabel("Buildings")
        ax.set_title("Buildings by river-distance band")
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        paths["spatial"] = path
    return paths


def _cluster_profile(results: dict[str, Any]) -> pd.DataFrame:
    profile = results["cluster_analysis"].copy()
    mapping = results["risk_mapping"]
    profile.index = [mapping.get(cluster, f"Cluster {cluster}") for cluster in profile.index]
    profile.index.name = "Risk level"
    return profile.reset_index()


def _historic_summary(gdf: pd.DataFrame) -> dict[str, Any] | None:
    required = {"hist_flood_flag", "hist_flood_count"}
    if not required.issubset(gdf.columns):
        return None
    valid_flags = pd.to_numeric(gdf["hist_flood_flag"], errors="coerce").fillna(0)
    flooded = gdf[valid_flags > 0]
    comparison = pd.crosstab(
        gdf["risk_level"],
        valid_flags > 0,
        rownames=["Risk level"],
        colnames=["Historically flooded"],
    )
    numeric = [
        column for column in (
            "hist_flood_count",
            "hist_rainfall_mean",
            "hist_rainfall_max",
            "hist_tide_mean",
            "hist_tide_max",
        )
        if column in gdf.columns
    ]
    stats = _feature_summary(gdf, numeric)
    return {
        "flooded_count": int(len(flooded)),
        "total_count": int(len(gdf)),
        "comparison": comparison.reset_index(),
        "stats": stats,
    }


def _insights(gdf: pd.DataFrame, risk_distribution: pd.DataFrame) -> list[str]:
    insights = []
    if not risk_distribution.empty:
        largest = risk_distribution.loc[
            risk_distribution["Buildings"].idxmax()]
        insights.append(
            f"{largest['Risk level']} is the largest risk group, containing "
            f"{int(largest['Buildings'])} buildings "
            f"({largest['Percentage']:.1f}% of the study buildings).")
    if "elevation" in gdf.columns:
        means = gdf.groupby("risk_level")["elevation"].mean()
        if not means.empty:
            lowest = means.idxmin()
            insights.append(
                f"The lowest mean elevation occurs in the {lowest} group "
                f"({_format_value(means.min())} m).")
    if "dist_to_river" in gdf.columns:
        nearest = gdf.groupby("risk_level")["dist_to_river"].mean()
        if not nearest.empty:
            closest = nearest.idxmin()
            insights.append(
                f"The {closest} group has the smallest average distance to "
                f"waterways ({_format_value(nearest.min())} m).")
    return insights


def _html_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "<p>No data available.</p>"
    display = frame.copy()
    for column in display.columns:
        display[column] = display[column].map(_format_value)
    return display.to_html(index=False, border=0, classes="data-table")


def _build_html(
    results: dict[str, Any],
    output_dir: Path,
    generated_at: str,
) -> str:
    gdf = results["buildings_with_features"]
    features = results.get("available_features", results.get("feature_columns", []))
    summary = _feature_summary(gdf, features)
    distribution = _risk_distribution(gdf)
    profile = _cluster_profile(results)
    historic = _historic_summary(gdf)
    metrics = results.get("evaluation_metrics", {})
    comparison = _risk_comparison(gdf)
    spatial = _spatial_analysis(gdf)
    priorities = _priority_areas(gdf)
    findings = _key_findings(gdf, distribution, historic)
    recommendations = _recommendations(gdf)
    charts = _create_charts(gdf, distribution, output_dir)
    area = results.get("place_name", "Kurla, Mumbai, India")
    map_path = output_dir / "flood_vulnerability_map.png"
    image = (
        f'<img class="risk-map" src="{escape(map_path.name)}" '
        f'alt="Static flood vulnerability map">'
        if map_path.exists() else "<p>Static map image unavailable.</p>"
    )
    historic_section = ""
    if historic is not None:
        historic_section = (
            "<h2>Historic Data Analysis</h2>"
            f"<p>{historic['flooded_count']} of {historic['total_count']} "
            "buildings overlap a historically flooded grid cell.</p>"
            f"{_html_table(historic['comparison'])}"
            f"{_html_table(historic['stats'])}"
        )
    insights = _insights(gdf, distribution)
    source_rows = pd.DataFrame([
        {"Source": "OpenStreetMap", "Use": "Buildings and waterways"},
        {"Source": "DEM", "Use": str(results.get("dem_path", "kurla.tif"))},
        {"Source": "K-Means", "Use": "Unsupervised risk grouping"},
    ])
    if historic is not None:
        source_rows.loc[len(source_rows)] = {
            "Source": "Hugging Face historical flood dataset",
            "Use": "Historical flood, rainfall, and tide enrichment",
        }
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Flood Analysis Report</title>
<style>
body {{ font-family: Arial, sans-serif; color: #243447; margin: 40px; line-height: 1.45; }}
h1, h2 {{ color: #164a63; }} h1 {{ font-size: 30px; }}
.title {{ min-height: 420px; padding-top: 120px; border-bottom: 3px solid #2d7f9d; }}
.meta {{ color: #5b6770; }} .risk-map, .chart {{ max-width: 720px; width: 100%; margin: 8px 0 20px; }}
.data-table {{ border-collapse: collapse; margin: 12px 0 24px; width: 100%; }}
.data-table th {{ background: #164a63; color: white; }}
.data-table td, .data-table th {{ border: 1px solid #c8d2d8; padding: 7px; text-align: left; }}
li {{ margin: 6px 0; }} .page-break {{ page-break-before: always; }}
</style></head><body>
<section class="title"><h1>Flood Vulnerability Analysis</h1>
<h2>{escape(area)}</h2><p class="meta">Generated: {escape(generated_at)}<br>
Version: {VERSION}</p></section>
<h2>Executive Summary</h2>
<p>The analysis processed {len(gdf)} buildings and assigned each to a
three-cluster flood vulnerability grouping using elevation, distance,
terrain, and hydrology features. The findings below are calculated from
the current pipeline run.</p>
<h2>Key Findings</h2><ul>{''.join(f'<li>{escape(item)}</li>' for item in findings)}</ul>
<h2>Study Area</h2><p>The study area is defined by the OSM building extent for
{escape(area)} and the associated DEM coverage. Distances are calculated in
projected metric coordinate systems, while map outputs use EPSG:4326.</p>
<h2>Data Sources</h2>{_html_table(source_rows)}
<h2>Feature Summary Statistics</h2>{_html_table(summary)}
<h2>Risk Distribution</h2>{_html_table(distribution)}
{f'<img class="chart" src="{escape(charts["distribution"].name)}" alt="Risk distribution chart">' if "distribution" in charts else ""}
<h2>Risk Comparison</h2>{_html_table(comparison)}
<h2>Model Interpretation</h2><p>K-Means is an unsupervised model. It groups
buildings by similarity across the engineered features; the High, Medium, and
Low labels describe relative vulnerability within this study area, not official
flood warnings. The principal inputs are elevation, river and drainage
distance, slope, local relief, major-waterway distance, and waterway density.</p>
<h2>Cluster Profiles</h2>{_html_table(profile)}
<h2>Model Evaluation Metrics</h2>{_html_table(pd.DataFrame(
    [{"Metric": key, "Value": value} for key, value in metrics.items()]))}
<h2>Static Risk Map</h2>{image}
<h2>Spatial Analysis</h2>{_html_table(spatial)}
{f'<img class="chart" src="{escape(charts["spatial"].name)}" alt="Spatial distance chart">' if "spatial" in charts else ""}
<h2>Priority Areas</h2>{_html_table(priorities)}
<h2>Recommended Actions</h2><ul>{''.join(f'<li>{escape(item)}</li>' for item in recommendations)}</ul>
<h2>Insights</h2><ul>{''.join(f'<li>{escape(item)}</li>' for item in insights)}</ul>
{historic_section}
<h2>Limitations and Future Work</h2><ul>
<li>K-Means is unsupervised and risk labels are assigned by mean elevation.</li>
<li>OSM coverage, DEM resolution, and historical grid resolution affect results.</li>
<li>Future work may add validated flood observations and supervised models.</li>
</ul>
<h2>Appendix</h2><p>Features: {escape(', '.join(features))}</p>
<p>Parameters: K-Means clusters=3, random_state=42, n_init=10;
median imputation; standard scaling.</p>
</body></html>"""


def _pdf_table(frame: pd.DataFrame, styles: Any) -> Table:
    if frame.empty:
        return Table([["No data available."]])
    display = frame.copy()
    data = [list(display.columns)]
    data.extend([
        [_format_value(value) for value in row]
        for row in display.itertuples(index=False, name=None)
    ])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#164a63")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d2d8")),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _build_pdf(results: dict[str, Any], output_dir: Path, path: Path) -> None:
    gdf = results["buildings_with_features"]
    features = results.get("available_features", results.get("feature_columns", []))
    distribution = _risk_distribution(gdf)
    historic = _historic_summary(gdf)
    comparison = _risk_comparison(gdf)
    spatial = _spatial_analysis(gdf)
    priorities = _priority_areas(gdf)
    findings = _key_findings(gdf, distribution, historic)
    recommendations = _recommendations(gdf)
    charts = _create_charts(gdf, distribution, output_dir)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Flood Vulnerability Analysis", styles["Title"]),
        Paragraph(str(results.get("place_name", "Kurla, Mumbai, India")),
                  styles["Heading2"]),
        Paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S} | Version: {VERSION}",
                  styles["Normal"]),
        Spacer(1, 0.3 * inch),
        Paragraph("Executive Summary", styles["Heading1"]),
        Paragraph(
            f"The current run processed {len(gdf)} buildings and generated "
            "dynamic vulnerability classifications.", styles["BodyText"]),
        Paragraph("Key Findings", styles["Heading1"]),
        *[Paragraph(f"- {item}", styles["BodyText"]) for item in findings],
        Paragraph("Study Area", styles["Heading1"]),
        Paragraph(
            "The study area is defined by the OSM building extent and the "
            "associated DEM coverage. Distances use projected metric CRSs; "
            "map outputs use EPSG:4326.",
            styles["BodyText"]),
        Paragraph("Data Sources", styles["Heading1"]),
        _pdf_table(pd.DataFrame([
            ["OpenStreetMap", "Buildings and waterways"],
            ["DEM", str(results.get("dem_path", "kurla.tif"))],
            ["K-Means", "Unsupervised risk grouping"],
            *(
                [["Hugging Face historical flood dataset",
                  "Historical flood, rainfall, and tide enrichment"]]
                if historic is not None else []
            ),
        ], columns=["Source", "Use"]), styles),
        Paragraph("Feature Summary Statistics", styles["Heading1"]),
        _pdf_table(_feature_summary(gdf, features), styles),
        Paragraph("Risk Distribution", styles["Heading1"]),
        _pdf_table(distribution, styles),
        Paragraph("Risk Comparison", styles["Heading1"]),
        _pdf_table(comparison, styles),
        Paragraph("Model Interpretation", styles["Heading1"]),
        Paragraph(
            "K-Means is unsupervised: the risk labels are relative groups "
            "within this study area, not official flood warnings. Inputs include "
            "elevation, river and drainage distance, slope, local relief, "
            "major-waterway distance, and waterway density.",
            styles["BodyText"]),
        Paragraph("Cluster Profiles", styles["Heading1"]),
        _pdf_table(_cluster_profile(results), styles),
        Paragraph("Model Evaluation Metrics", styles["Heading1"]),
        _pdf_table(pd.DataFrame([
            {"Metric": key, "Value": value}
            for key, value in results.get("evaluation_metrics", {}).items()
        ]), styles),
    ]
    map_path = output_dir / "flood_vulnerability_map.png"
    if map_path.exists():
        story.extend([
            PageBreak(),
            Paragraph("Static Risk Map", styles["Heading1"]),
            Image(str(map_path), width=6.5 * inch, height=6.5 * inch),
        ])
    for chart_path in charts.values():
        story.extend([
            Paragraph("Data Visualization", styles["Heading1"]),
            Image(str(chart_path), width=6.2 * inch, height=3.2 * inch),
        ])
    story.extend([
        Paragraph("Spatial Analysis", styles["Heading1"]),
        _pdf_table(spatial, styles),
        Paragraph("Priority Areas", styles["Heading1"]),
        _pdf_table(priorities, styles),
        Paragraph("Recommended Actions", styles["Heading1"]),
        *[Paragraph(f"- {item}", styles["BodyText"]) for item in recommendations],
    ])
    story.extend([
        Paragraph("Insights", styles["Heading1"]),
        *[Paragraph(f"- {item}", styles["BodyText"])
          for item in _insights(gdf, distribution)],
    ])
    if historic is not None:
        story.extend([
            Paragraph("Historic Data Analysis", styles["Heading1"]),
            Paragraph(
                f"{historic['flooded_count']} of {historic['total_count']} "
                "buildings overlap a historically flooded grid cell.",
                styles["BodyText"]),
            _pdf_table(historic["comparison"], styles),
            _pdf_table(historic["stats"], styles),
        ])
    story.extend([
        Paragraph("Limitations and Future Work", styles["Heading1"]),
        Paragraph(
            "K-Means is unsupervised and labels are assigned by mean elevation. "
            "OSM, DEM, and historical-grid coverage and resolution limit interpretation. "
            "Validated observations and supervised models are future improvements.",
            styles["BodyText"]),
        Paragraph("Appendix", styles["Heading1"]),
        Paragraph(f"Features: {', '.join(features)}", styles["BodyText"]),
        Paragraph(
            "Parameters: K-Means clusters=3, random_state=42, n_init=10; "
            "median imputation; standard scaling.",
            styles["BodyText"]),
    ])
    SimpleDocTemplate(str(path), pagesize=A4, rightMargin=36, leftMargin=36).build(story)


def generate_report(results: dict[str, Any], output_dir: str | Path) -> dict[str, Path]:
    """Generate dynamic HTML and PDF reports from a completed pipeline run."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_path = output_dir / REPORT_HTML_NAME
    pdf_path = output_dir / REPORT_PDF_NAME
    html_path.write_text(
        _build_html(results, output_dir, generated_at),
        encoding="utf-8",
    )
    _build_pdf(results, output_dir, pdf_path)
    return {"html": html_path, "pdf": pdf_path}
