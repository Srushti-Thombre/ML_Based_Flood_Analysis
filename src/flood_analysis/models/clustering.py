"""K-Means clustering and risk-label mapping."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = [
    "elevation", "dist_to_river", "slope_deg", "local_relief_m",
    "dist_to_major_waterway", "waterway_density_300m", "dist_to_drainage_m",
]


def run_clustering(
    buildings_with_features: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str], list[str], SimpleImputer, StandardScaler, np.ndarray, KMeans, pd.DataFrame, dict[int, str]]:
    """Run the notebook's median-imputed, standardized three-cluster model."""
    available_features = [
        col for col in FEATURE_COLUMNS if col in buildings_with_features.columns]
    if not available_features:
        raise RuntimeError("No clustering features found.")
    X = buildings_with_features[available_features].copy()
    imputer = SimpleImputer(strategy="median", missing_values=np.nan)
    X_imputed = imputer.fit_transform(X)
    X_clean = pd.DataFrame(X_imputed, columns=available_features, index=X.index)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_clean)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    buildings_subset = buildings_with_features[available_features].copy()
    buildings_subset["cluster"] = cluster_labels
    cluster_analysis = buildings_subset.groupby("cluster")[available_features].mean()
    sorted_clusters = cluster_analysis["elevation"].sort_values().index.tolist()
    risk_mapping = {
        sorted_clusters[0]: "High Risk",
        sorted_clusters[1]: "Medium Risk",
        sorted_clusters[2]: "Low Risk",
    }
    buildings_with_features["cluster"] = cluster_labels
    buildings_with_features["risk_level"] = buildings_with_features.index.map(
        lambda idx: risk_mapping.get(
            cluster_labels[buildings_with_features.index.get_loc(idx)], "Unknown")
    )
    return (
        buildings_with_features, available_features, FEATURE_COLUMNS, imputer,
        scaler, cluster_labels, kmeans, cluster_analysis, risk_mapping,
    )
