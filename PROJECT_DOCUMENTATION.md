# Clustering-Based Flood Analysis Project Documentation

## Project Overview

**Project Name:** Clustering-Based Flood Analysis  
**Location:** `clustering-based-flood-analysis/` folder  
**Primary Deliverable:** Interactive flood vulnerability map for Kurla, Mumbai, India  
**Technology Stack:** Python, Geopandas, OSMnx, Rasterio, K-Means Clustering, Folium

---

## Project Synopsis

This project analyzes flood vulnerability by combining:

- **OpenStreetMap (OSM) Vector Data**: Building footprints and waterway networks
- **Digital Elevation Model (DEM)**: Raster data (`kurla.tif`) for terrain analysis
- **Machine Learning**: K-Means clustering to categorize buildings into flood risk levels
- **Geospatial Analysis**: Multi-feature engineering including elevation, distance metrics, slope, and waterway density

**Key Outputs:**

1. `interactive_flood_map_enhanced.html` – Zoomable web map with toggleable risk layers and rich tooltips
2. `flood_vulnerability_data_enhanced.gpkg` – GeoPackage with all features (for QGIS/ArcGIS)
3. `flood_vulnerability_feature_report.csv` – Tabular export of all computed features

---

## Project File Structure

```
clustering-based-flood-analysis/
├── Project_Files/
│   ├── flood.ipynb                              # Main Jupyter notebook
│   ├── kurla.tif                               # DEM raster file
│   ├── interactive_flood_map_enhanced.html     # Final interactive map output
│   ├── interactive_flood_map.html              # Basic interactive map
│   ├── flood_vulnerability_data_enhanced.gpkg  # Enhanced GeoPackage export
│   ├── flood_vulnerability_data.gpkg           # Basic GeoPackage export
│   ├── flood_vulnerability_feature_report.csv  # Feature table report
│   ├── flood_vulnerability_map.png             # Static PNG visualization
│   ├── README.md                               # Project readme
│   └── cache/                                  # Temporary file cache
└── [other supporting files]
```

---

## Notebook Cell Breakdown: `flood.ipynb`

### **Cell 1: Install rasterstats Package**

- **Purpose:** Ensures the `rasterstats` library is installed and up-to-date
- **Code:** Uses `pip install --upgrade rasterstats` to install the package needed for zonal statistics
- **Expected Output:** Console message confirming installation and path to the package

---

### **Cell 2: Import Libraries**

- **Purpose:** Loads all required geospatial and ML libraries
- **Libraries Imported:**
  - `geopandas` – vector data (buildings, waterways)
  - `osmnx` – OpenStreetMap data fetching
  - `rasterio` – DEM/raster file handling
  - `rasterstats` – zonal statistics (map raster pixels to polygons)
  - `pandas` – data manipulation
  - `sklearn` – K-Means clustering & scaling
  - `matplotlib` – visualization
- **Expected Output:** No console output; libraries are loaded silently

---

### **Cell 3: Load OSM Vector Data (Place-Based Approach - Alternative)**

- **Purpose:** Attempt to load buildings and waterways using place boundary (fallback if point-based search fails)
- **Key Operations:**
  - Uses `ox.features_from_place()` to fetch buildings and rivers for Kurla, Mumbai
  - Tries multiple waterway tags: `{'waterway': ['river', 'stream', 'canal', 'drain']}`
  - Falls back to 5km and 10km radius searches if place boundary yields no results
- **Expected Output:**
  - "Found X buildings."
  - "Found X waterway features from place boundary." (or fallback radius messages)

---

### **Cell 4: Load OSM Vector Data (Point-Based Approach - MAIN METHOD)**

- **Purpose:** Geocode a place name and fetch vector features within a 2.5km radius
- **Key Operations:**
  - Geocodes "Kurla, Mumbai, India" to lat/lon coordinates
  - Fetches buildings within 2,500m radius
  - Fetches waterways, expanding to 5km and 10km if needed
- **Expected Output:**
  - "Geocoding 'Kurla, Mumbai, India' to a point..."
  - "Found X buildings."
  - "Found X waterway features within Xm." (for each radius tried)

---

### **Cell 5: Load Raster DEM File**

- **Purpose:** Opens and reads the Digital Elevation Model (`kurla.tif`)
- **Key Operations:**
  - Uses `rasterio.open()` to load the DEM
  - Extracts the first band (elevation data), transformation matrix, and CRS
- **Expected Output:**
  - "DEM loaded successfully. CRS: EPSG:XXXX"
  - Error message if file not found

---

### **Cell 6: Debugging Script – Validate Spatial Overlap**

- **Purpose:** Checks if building and river data overlap with the DEM file (critical for feature engineering)
- **Key Operations:**
  - Prints counts of buildings and rivers found
  - Compares bounds and CRS of vector data vs. DEM
  - Creates bounding box and checks intersection
- **Expected Output:**
  - "Buildings Found: X"
  - "Rivers Found: X"
  - "Do buildings and DEM overlap? True/False"
  - Warnings if overlap is missing

---

### **Cell 7: Feature Engineering – Elevation & Distance to River**

- **Purpose:** Extract the first two key features by mapping raster data to building polygons
- **Key Operations:**
  1. **Elevation Feature:**
     - Reprojects buildings to DEM's CRS
     - Uses `rasterstats.zonal_stats()` to calculate mean elevation for each building
  2. **Distance to River Feature:**
     - Projects buildings and rivers to local UTM for accurate distance measurement
     - Unions all river segments into single geometry
     - Calculates distance from each building centroid to nearest river
  3. **Data Cleaning:**
     - Drops buildings with missing elevation or distance values
     - Joins features back to GeoDataFrame
- **Expected Output:**
  - "Feature engineering complete. X buildings processed."
  - Sample data showing `elevation` and `dist_to_river` columns with numerical values

---

### **Cell 8: Comprehensive Feature Engineering + K-Means Clustering**

- **Purpose:** Computes ALL features (terrain, hydrology, drainage) and uses them for clustering into 3 flood risk categories
- **Key Operations:**
  1. **Inline Feature Engineering:**
     - Terrain features: `slope_deg` (from DEM gradient), `local_relief_m` (elevation variation)
     - Hydrology features: `dist_to_major_waterway` (75th percentile longest rivers), `waterway_density_300m` (waterway density)
     - Drainage features: `dist_to_drainage_m` (distance to drains/ditches/canals)
  2. **Feature Selection:** Uses ALL 7 features: `['elevation', 'dist_to_river', 'slope_deg', 'local_relief_m', 'dist_to_major_waterway', 'waterway_density_300m', 'dist_to_drainage_m']`
  3. **Data Cleaning:** Removes buildings with missing values (NaN) for any feature
  4. **Scaling:** Normalizes features using `StandardScaler` (critical for equal weight)
  5. **K-Means Clustering:** Runs with k=3 clusters, n_init=10
  6. **Cluster Analysis:** Shows mean values across ALL features for each cluster
  7. **Risk Mapping:** Assigns High/Medium/Low based on elevation ranking
- **Expected Output:**
  - Feature computation confirmations ("✓ Terrain features added...", "✓ Hydrology features added...", etc.)
  - "Using 7 features for clustering: [...all features...]"
  - "Buildings with complete data: X / Y"
  - **Comprehensive Cluster Analysis table** showing means for all 7 features
  - "Risk mapping applied: {0: 'High Risk', 1: 'Medium Risk', 2: 'Low Risk'}" (or similar)

---

### **Cell 9: Static Matplotlib Visualization**

- **Purpose:** Creates a static PNG visualization of flood vulnerability
- **Key Operations:**
  - Plots building polygons colored by risk level (red=High, orange=Medium, green=Low)
  - Overlays river lines in blue
  - Saves as `flood_vulnerability_map.png`
- **Expected Output:**
  - "Map saved as 'flood_vulnerability_map.png'"
  - PNG image displayed in notebook showing colored buildings and blue rivers

---

### **Cell 10: Create Basic Interactive Map with Folium**

- **Purpose:** Creates the first interactive HTML map (`interactive_flood_map.html`)
- **Key Operations:**
  1. Reprojects buildings to EPSG:4326 (web standard)
  2. Calculates map center from building union
  3. Creates Folium map with OpenStreetMap tiles
  4. Defines color mapping for risk levels
  5. Adds buildings as GeoJson layer with:
     - Color-coded fill based on risk level
     - Tooltips showing: risk_level, elevation, dist_to_river
  6. Adds LayerControl for interactivity
- **Expected Output:**
  - "SUCCESS! Interactive map saved to: interactive_flood_map.html"
  - HTML file created with toggleable layers

---

### **Cell 11: Export Data to GeoPackage**

- **Purpose:** Exports the buildings with basic features to GeoPackage format (for QGIS/ArcGIS)
- **Key Operations:**
  - Converts GeoDataFrame to `.gpkg` format (GeoPackage driver)
- **Expected Output:**
  - "SUCCESS! Data exported to: flood_vulnerability_data.gpkg"
  - GeoPackage file created

---

### **Cell 12: Silhouette Score Analysis**

- **Purpose:** Tests different numbers of clusters (k=2 to 7) to find optimal clustering
- **Key Operations:**
  - Runs K-Means for each k value
  - Calculates silhouette score (measures cluster quality)
- **Expected Output:**
  - Table showing silhouette scores for each k value
  - Example: "k=3, silhouette=0.4521"

---

### **Cell 13: Empty Cell**

- **Purpose:** Placeholder (no operations)
- **Expected Output:** None

---

### **Cells 14-17: DEM Inspection & Analysis (Debugging/Exploration)**

- **Purpose:** Understand the DEM file coverage, resolution, elevation range, and geographic location
- **Cell 14 Output:** DEM metadata (CRS, dimensions, bands, bounds, resolution, statistics)
- **Cell 15 Output:** DEM converted to DataFrame showing pixel elevation values
- **Cell 16 Output:** Geographic coverage by reverse-geocoding (suburbs/areas covered)
- **Cell 17 Output:** Elevation statistics by named area (average elevation per suburb)
- **Note:** These cells are primarily for understanding/debugging; not critical for final output

---

### **Cell 18 (Markdown):** Section Header

- **Content:** "Step 8: Add More Features (Terrain + Hydrology)"
- Explains that new features are added without modifying earlier steps

---

### **Cell 19: Add Terrain Features**

- **Purpose:** Extracts slope and local relief from DEM using raster analysis
- **Key Operations:**
  1. **Slope Calculation:**
     - Computes gradient (derivative) of DEM using `np.gradient()`
     - Converts to degrees: `np.degrees(np.arctan(...))`
     - Samples slope at each building centroid
  2. **Local Relief Calculation:**
     - For each building, looks at 3×3 pixel window around centroid
     - Calculates max elevation - min elevation in that window
- **Added Columns:**
  - `slope_deg` – slope steepness in degrees
  - `local_relief_m` – local elevation variation in meters
- **Expected Output:**
  - "Terrain features added: slope_deg, local_relief_m"
  - Summary statistics for both new columns

---

### **Cell 20: Add Hydrology Features**

- **Purpose:** Computes distance to major waterways and local waterway density
- **Key Operations:**
  1. **Distance to Major Waterway:**
     - Filters rivers by length (keeps 75th percentile longest rivers)
     - Calculates distance from each building to nearest major river
  2. **Waterway Density (300m radius):**
     - Creates 300m circular buffer around each building
     - Counts total length of waterways within buffer
     - Calculates density: total_waterway_length / buffer_area
- **Added Columns:**
  - `dist_to_major_waterway` – distance in meters to nearest major river
  - `waterway_density_300m` – waterway length per unit area (m/m²)
- **Expected Output:**
  - "Hydrology features added: dist_to_major_waterway, waterway_density_300m"
  - Summary statistics for both new columns

---

### **Cell 21 (Markdown):** Section Header

- **Content:** "Step 9: Product Enhancements (Feature 7)"
- Describes filtered risk layers and enhanced tooltips

---

### **Cell 22: Create Enhanced Interactive Map**

- **Purpose:** Creates the final enhanced HTML map (`interactive_flood_map_enhanced.html`) with all features visible
- **Key Operations:**
  1. Gathers all available feature columns
  2. Exports feature table to CSV: `flood_vulnerability_feature_report.csv`
  3. Creates separate **FeatureGroup for each risk level** (High/Medium/Low):
     - Each risk group is a toggleable layer
     - Users can click checkboxes to show/hide each risk category
  4. Adds GeoJson layers to each feature group with:
     - Color-coded buildings (red/orange/green)
     - **Rich tooltips showing ALL computed features:**
       - `risk_level`
       - `elevation`
       - `dist_to_river`
       - `dist_to_drainage_m`
       - `slope_deg`
       - `local_relief_m`
       - `dist_to_major_waterway`
       - `waterway_density_300m`
  5. Exports enhanced GeoPackage: `flood_vulnerability_data_enhanced.gpkg`
- **Expected Output:**
  - "Enhanced outputs created successfully:"
  - "1) interactive_flood_map_enhanced.html"
  - "2) flood_vulnerability_feature_report.csv"
  - "3) flood_vulnerability_data_enhanced.gpkg"

---

### **Cell 23 (Markdown):** Section Header

- **Content:** "Step 10: Nearest Drainage Feature"
- Introduces dedicated drainage distance feature

---

### **Cell 24: Add Drainage Features**

- **Purpose:** Computes distance to dedicated drainage features (drains, ditches, canals)
- **Key Operations:**
  1. Attempts to fetch drainage-specific OSM tags: `{'waterway': ['drain', 'ditch', 'canal']}`
  2. Falls back to filtering already-loaded rivers if OSM fetch fails
  3. Calculates distance from each building to nearest drainage feature
- **Added Column:**
  - `dist_to_drainage_m` – distance in meters to nearest drain/ditch/canal
- **Expected Output:**
  - "Feature added: dist_to_drainage_m"
  - Summary statistics for the new column

---

---

## Interactive HTML Map: `interactive_flood_map_enhanced.html`

### Map Components

**Base Layer:**

- OpenStreetMap tile layer (standard web map background)

**Data Layers (Toggleable):**
The map has **three separate feature layers** that can be toggled on/off via the layer control panel:

1. **High Risk Layer** (Red buildings)
   - Buildings classified as high flood risk
   - Visible in left sidebar as checkbox

2. **Medium Risk Layer** (Orange buildings)
   - Buildings classified as medium flood risk

3. **Low Risk Layer** (Green buildings)
   - Buildings classified as low flood risk

**Interactive Features:**

- **Zoom & Pan:** Use mouse wheel or controls to navigate
- **Hover Tooltips:** When you hover over a building, a tooltip appears showing:
  ```
  risk_level: [High/Medium/Low]
  elevation: [meters]
  dist_to_river: [meters]
  dist_to_drainage_m: [meters]
  slope_deg: [degrees]
  local_relief_m: [meters]
  dist_to_major_waterway: [meters]
  waterway_density_300m: [m/m²]
  ```
- **Layer Toggle:** Click checkboxes in the layer control to show/hide each risk category

---

## **🔑 KEY INSIGHT: All Features Now Part of Risk Calculation!**

### The Answer (Complete Update)

**The advanced features (terrain, hydrology, drainage) ARE NOW FULLY INTEGRATED** into the K-Means clustering:

#### **1. Used in K-Means Classification (PRIMARY IMPACT)**

- **Cell 8** computes ALL 7 features and uses them for clustering
- Each building's risk level is determined by ALL factors working together
- Features are equally weighted after StandardScaler normalization
- This is the **main way** these features influence your results

#### **2. Displayed in Tooltips (EXPLORATORY USE)**

The **interactive_flood_map_enhanced.html** shows all features in hover tooltips:

- Hover over any building polygon
- A popup shows the building's properties including all 7 features
- Useful for analysts to understand **why** a building is classified as High/Medium/Low risk

#### **3. Exported for Further Analysis (POST-HOC USE)**

- Available in CSV report and GeoPackage for GIS analysis
- Can be used for custom visualizations, statistical analysis
- Enables refinement of model if needed

### Mapping: Which Cells Contribute to What

| HTML Output Component               | Source Cells    | How It Uses Features            |
| ----------------------------------- | --------------- | ------------------------------- |
| **Red Buildings (High Risk)**       | Cell 8          | Uses ALL 7 features to classify |
| **Orange Buildings (Medium Risk)**  | Cell 8          | Uses ALL 7 features to classify |
| **Green Buildings (Low Risk)**      | Cell 8          | Uses ALL 7 features to classify |
| **Tooltip: elevation**              | Cell 7 + Cell 8 | Part of clustering (primary)    |
| **Tooltip: dist_to_river**          | Cell 7 + Cell 8 | Part of clustering (primary)    |
| **Tooltip: slope_deg**              | Cell 8 (inline) | Part of clustering (major)      |
| **Tooltip: local_relief_m**         | Cell 8 (inline) | Part of clustering (secondary)  |
| **Tooltip: dist_to_major_waterway** | Cell 8 (inline) | Part of clustering (major)      |
| **Tooltip: waterway_density_300m**  | Cell 8 (inline) | Part of clustering (secondary)  |
| **Tooltip: dist_to_drainage_m**     | Cell 8 (inline) | Part of clustering (context)    |
| **Layer Control Panel**             | Cell 22         | Toggles risk categories         |
| **CSV Export**                      | Cell 22         | All features for analysis       |
| **GeoPackage Export**               | Cell 22         | All features + geometry         |

---

## Summary

**What Changed:** Your hydrology, drainage, and terrain features **ARE NOW DIRECTLY PART** of the K-Means risk classification:

1. ✅ **They're computed inline** in Cell 8 (not separate cells)
2. ✅ **They're used in clustering** to determine risk labels (not just tooltips)
3. ✅ **They're weighted equally** after scaling (no feature dominates)
4. ✅ **They're visible in tooltips** when you hover over buildings
5. ✅ **They're exported** to CSV and GeoPackage for further analysis

The clustering is now **truly multi-dimensional**, considering:

- Physical terrain characteristics (slope, relief)
- Water proximity (rivers, major waterways, drainage)
- Elevation (primary risk indicator)

This produces **more nuanced and realistic risk classifications** than using just 2 features.

---

## Project Data Flow Diagram

```
Step 1: OSMnx Downloads         → Buildings + Waterways (Vector)
         Rasterio Loads         → DEM (Raster)

Step 2: Feature Engineering
         Cell 7                 → elevation, dist_to_river
         Cell 19                → slope_deg, local_relief_m
         Cell 20                → dist_to_major_waterway, waterway_density_300m
         Cell 24                → dist_to_drainage_m

Step 3: K-Means Clustering      → risk_level (High/Medium/Low)
        (Cell 8)

Step 4: Visualization & Export
         Cell 22                → interactive_flood_map_enhanced.html
                               → flood_vulnerability_data_enhanced.gpkg
                               → flood_vulnerability_feature_report.csv
```

---

## How to Present This

1. **Show the interactive map** – Open `interactive_flood_map_enhanced.html` in a browser
2. **Demonstrate tooltips** – Hover over buildings to show hydrology data
3. **Toggle layers** – Click checkboxes to filter by risk level
4. **Explain the pipeline** – Walk through Cells 1-7 (basic analysis), then Cells 19-24 (advanced features)
5. **Clarify the insight** – "Hydrology features enhance the data but work behind the scenes in the tooltips, not as separate map layers"

---

---

# PROBLEM STATEMENT & INTRODUCTION SCRIPT

## Problem Statement

**Title:** Data-Driven Flood Vulnerability Assessment for Urban Areas Using Clustering-Based Spatial Analysis

### Problem Definition

Urban flooding poses significant risks to infrastructure and populations, particularly in low-lying coastal and riverine areas like Kurla, Mumbai. Traditional flood risk assessments rely on historical flood data or simple proximity metrics, which may not capture the spatial heterogeneity of buildings and their unique vulnerability profiles.

**Key Challenges:**

1. **Complex Risk Factors** – Flood vulnerability depends on multiple interrelated factors (elevation, proximity to waterways, slope, terrain variability, and drainage patterns), not just single indicators
2. **Data Integration** – Combining vector data (buildings, waterway networks) with raster data (terrain/elevation models) requires sophisticated geospatial processing
3. **Scalability** – Manual flood risk assessment is impractical for large urban areas; automation is needed
4. **Actionability** – Decision-makers require both visual (map-based) and tabular (feature-based) outputs for urban planning

### Objectives

This project develops a **data-driven, unsupervised learning approach** to:

1. **Automatically classify buildings** into flood risk categories (High/Medium/Low) using multi-feature spatial analysis
2. **Integrate multi-source geospatial data** – combining OpenStreetMap building/waterway data with digital elevation models
3. **Engineer meaningful features** that capture terrain complexity (slope, local relief) and hydrology (distance to waterways, drainage density)
4. **Create interactive, actionable outputs** (web maps, GIS-compatible datasets) for urban planners and disaster management agencies
5. **Provide transparency** in the clustering process by mapping features to risk classifications

### Solution Approach

The project uses **K-Means unsupervised clustering** to partition buildings into flood risk tiers based on engineered features, then visualizes results in an interactive web map with rich feature tooltips for exploratory analysis.

---

## Introduction Script for Presentation

### Opening Hook

_"Urban flooding is increasingly common in Indian cities. When it rains, some buildings flood and others don't—not randomly, but due to **geography**. This project answers: Can we predict which buildings are at risk by analyzing terrain, elevation, and proximity to water? And can we do it automatically?"_

---

### Part 1: The Complete Feature Suite

This project computes **8 engineered features** for every building in the study area:

#### **Hydro-Terrain Features**

| Feature          | Description                                  | Data Source           | Unit    | Why It Matters                           |
| ---------------- | -------------------------------------------- | --------------------- | ------- | ---------------------------------------- |
| `elevation`      | Mean elevation of building location from DEM | Rasterio (kurla.tif)  | meters  | Higher buildings are safer from floods   |
| `slope_deg`      | Ground steepness around building             | DEM gradient analysis | degrees | Steeper slopes drain water faster        |
| `local_relief_m` | Local elevation variation (3×3 pixel window) | DEM analysis          | meters  | Rougher terrain holds flood water longer |

#### **Proximity to Water Features**

| Feature                  | Description                                             | Data Source            | Unit   | Why It Matters                             |
| ------------------------ | ------------------------------------------------------- | ---------------------- | ------ | ------------------------------------------ |
| `dist_to_river`          | Distance to ANY waterway (rivers, streams)              | OSM waterway tags      | meters | Closer to rivers = higher flood risk       |
| `dist_to_major_waterway` | Distance to longest/major rivers only (75th percentile) | Filtered OSM waterways | meters | Major rivers are primary flood sources     |
| `dist_to_drainage_m`     | Distance to drainage features (drains, ditches, canals) | OSM drain/ditch tags   | meters | Drainage infrastructure may fail in floods |

#### **Hydrology & Density Features**

| Feature                 | Description                                        | Data Source          | Unit | Why It Matters                                  |
| ----------------------- | -------------------------------------------------- | -------------------- | ---- | ----------------------------------------------- |
| `waterway_density_300m` | Total waterway length per unit area in 300m radius | Spatial buffer + OSM | m/m² | High density = complex hydrology, slow drainage |

---

### Part 2: The K-Means Clustering Model

#### What is K-Means?

K-Means is an **unsupervised machine learning algorithm** that groups similar data points into clusters. It works by:

1. **Randomly placing 3 cluster centers** (for our case: k=3)
2. **Assigning each building** to the nearest cluster center
3. **Recalculating cluster centers** based on member averages
4. **Repeating** until centers stabilize

#### Why K-Means for Flood Risk?

- ✅ **No labeled training data needed** – We don't have historical "flooded vs. non-flooded" labels
- ✅ **Automatic categorization** – Naturally groups buildings into risk tiers
- ✅ **Interpretable results** – Cluster centers show average feature values, revealing what defines each risk level
- ✅ **Scalable** – Works efficiently on thousands of buildings

#### Data Computation & Scaling

**Input Features to K-Means (Cell 8):**

```
ALL 7 Features Used (Computed Inline in Cell 8):
  1. elevation               - Mean elevation from DEM
  2. dist_to_river           - Distance to any waterway
  3. slope_deg               - Slope steepness (degrees)
  4. local_relief_m          - Local elevation variation (meters)
  5. dist_to_major_waterway  - Distance to major rivers (75th percentile)
  6. waterway_density_300m   - Waterway density in 300m radius (m/m²)
  7. dist_to_drainage_m      - Distance to drainage features (drains/ditches)
```

**Critical Step – StandardScaler:**

```python
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
```

**Why scaling matters:**

- Elevation ranges ~0–50 meters
- Distance metrics range ~0–5000 meters
- Waterway density ranges ~0–0.01 m/m²
- Without scaling, larger-magnitude features dominate (5000 >> 50 >> 0.01)
- Scaling transforms all to mean=0, std=1, giving EQUAL WEIGHT to all factors
- This ensures terrain, hydrology, and drainage factors contribute equally

**K-Means Parameters:**

```python
kmeans = KMeans(
    n_clusters=3,      # 3 risk categories (Low/Med/High)
    random_state=42,   # Reproducible results
    n_init=10          # Try 10 random starts, pick best
)
```

#### How Clustering Produces Risk Labels

After clustering, the algorithm produces **cluster IDs (0, 1, 2)**, but these are arbitrary. We **map them to risk labels** by analyzing cluster statistics across ALL 7 features:

**Example Output from Clustering:**

```
Cluster 0 (HIGH RISK):
  - avg_elevation=12m, avg_slope=15°, avg_local_relief=2m
  - avg_dist_to_river=200m, avg_waterway_density=0.008
  - avg_dist_to_major_waterway=300m, avg_dist_to_drainage=250m
  → LOWEST elevation + STEEPER slopes + CLOSEST to all water sources

Cluster 1 (MEDIUM RISK):
  - avg_elevation=25m, avg_slope=8°, avg_local_relief=1m
  - avg_dist_to_river=1200m, avg_waterway_density=0.002
  - avg_dist_to_major_waterway=1500m, avg_dist_to_drainage=1000m
  → MEDIUM elevation + slopes + distances

Cluster 2 (LOW RISK):
  - avg_elevation=40m, avg_slope=3°, avg_local_relief=0.5m
  - avg_dist_to_river=3000m, avg_waterway_density=0.0001
  - avg_dist_to_major_waterway=4000m, avg_dist_to_drainage=3500m
  → HIGHEST elevation + FLATTEST terrain + FARTHEST from all water sources
```

This mapping is done in **Cell 8**, sorting clusters by elevation and assigning risk labels accordingly.

---

### Part 3: Advanced Features – NOW INTEGRATED INTO CLUSTERING!

#### What Changed?

**Before:** Only `elevation` and `dist_to_river` used in K-Means (terrain, hydrology, drainage computed separately)

**NOW (Updated):** ALL 7 features computed inline in **Cell 8** and used together in K-Means clustering:

- ✅ Terrain features (`slope_deg`, `local_relief_m`) → **Part of clustering**
- ✅ Hydrology features (`dist_to_major_waterway`, `waterway_density_300m`) → **Part of clustering**
- ✅ Drainage features (`dist_to_drainage_m`) → **Part of clustering**

#### The Advanced Feature Pipeline (ALL Integrated in Cell 8)

```
1. Check if terrain features exist → if not, compute from DEM
   - slope_deg: Ground steepness (degrees)
   - local_relief_m: Local elevation variation in 3×3 pixel window

2. Check if hydrology features exist → if not, compute from waterways
   - dist_to_major_waterway: Distance to 75th percentile longest rivers
   - waterway_density_300m: Total waterway length per m² in 300m buffer

3. Check if drainage features exist → if not, compute from drainage tags
   - dist_to_drainage_m: Distance to drains, ditches, canals

4. Gather all 7 features + remove buildings with missing values

5. Scale all features to equal weight using StandardScaler

6. Run K-Means clustering with ALL 7 features

7. Analyze cluster means across ALL features

8. Assign risk labels based on elevation ranking
```

#### How These Features NOW Contribute to Risk Classification

| Feature                  | K-Means Impact | Risk Indication                            | Impact         |
| ------------------------ | -------------- | ------------------------------------------ | -------------- |
| `elevation`              | ⭐⭐⭐⭐⭐     | Lower elevation = Higher risk              | Primary factor |
| `slope_deg`              | ⭐⭐⭐⭐       | Steeper = Slower drainage = Higher risk    | Major factor   |
| `local_relief_m`         | ⭐⭐⭐         | Rougher = Water accumulation = Higher risk | Secondary      |
| `dist_to_river`          | ⭐⭐⭐⭐⭐     | Closer to rivers = Higher risk             | Primary factor |
| `dist_to_major_waterway` | ⭐⭐⭐⭐       | Closer to major rivers = Higher risk       | Major factor   |
| `waterway_density_300m`  | ⭐⭐⭐         | Higher density = Higher risk               | Secondary      |
| `dist_to_drainage_m`     | ⭐⭐           | Infrastructure context                     | Context        |

#### Where These Features Display (Updated)

| Feature                        | Where It Shows                                | Effect                     |
| ------------------------------ | --------------------------------------------- | -------------------------- |
| **In K-Means Clustering**      | Cell 8 (directly affects risk classification) | ✅ **NOW ACTIVE**          |
| **In Cluster Analysis Output** | Cell 8 (shows mean values for each cluster)   | ✅ **Comprehensive table** |
| **In Interactive Map Tooltip** | Cell 22 (hover over buildings)                | ✅ Shows all values        |
| **In CSV Report**              | Cell 22 (all features exported)               | ✅ Available               |
| **In GeoPackage**              | Cell 22 (all features + geometry)             | ✅ Available               |

#### Why This Integrated Approach is Better

✅ **More nuanced risk classification** – considers ALL physical factors, not just 2
✅ **Balanced factors** – all features equally weighted after StandardScaler
✅ **Captures drainage patterns** – steep slopes drain faster, rough terrain holds water
✅ **Identifies hydrology hotspots** – high waterway density areas flagged
✅ **Comprehensive** – model now considers terrain complexity, water proximity, drainage infrastructure
✅ **Interpretable** – cluster analysis table shows exactly how each factor contributes

#### Example: How Different Scenarios Are Classified

Building A: elevation=15m, slope=2°, relief=0.2m, dist_to_river=500m, density=0.006 → **HIGH RISK**

- Low elevation + flat terrain + close to water

Building B: elevation=35m, slope=8°, relief=1.5m, dist_to_river=1500m, density=0.002 → **MEDIUM RISK**

- Medium elevation + moderate slope + medium distance

Building C: elevation=45m, slope=12°, relief=3m, dist_to_river=4000m, density=0.0001 → **LOW RISK**

- High elevation + steep slope + far from water

Each building's class is determined by **the combination of all factors**, creating more realistic and nuanced risk profiles.

---

### Part 4: Output Overview

#### Four Outputs Delivered

**1. Interactive Web Map** (`interactive_flood_map_enhanced.html`)

- 🗺️ **Base:** OpenStreetMap tiles
- 🏢 **Data:** Buildings colored by risk (Red=High, Orange=Medium, Green=Low)
- 📍 **Interactivity:**
  - Hover to see all 8 features in tooltip
  - Zoom/pan to explore
  - Toggle risk layers on/off via checkboxes
- 👥 **Audience:** Urban planners, disaster management, general public

**2. GeoPackage Export** (`flood_vulnerability_data_enhanced.gpkg`)

- 📊 **Content:** Building geometries + all 8 computed features
- 🔌 **Compatible:** Opens in QGIS, ArcGIS, PostGIS
- 👥 **Audience:** GIS professionals, technical analysts

**3. CSV Feature Report** (`flood_vulnerability_feature_report.csv`)

- 📋 **Content:** Tabular data (no geometry) with all 8 features per building
- 📈 **Uses:** Further statistical analysis, custom visualizations, Excel/Python workflows
- 👥 **Audience:** Data scientists, researchers

**4. Static PNG Map** (`flood_vulnerability_map.png`)

- 🖼️ **Content:** Matplotlib visualization of buildings + rivers
- 📄 **Uses:** Presentations, reports, posters
- 👥 **Audience:** Decision-makers, presentations

---

#### Data Flow Summary

```
INPUT DATA
├─ OpenStreetMap (OSM)
│  ├─ Buildings (footprints)
│  └─ Waterways (rivers, streams, drains, canals)
└─ Digital Elevation Model (kurla.tif)

PROCESSING PIPELINE
├─ Cell 7: Extract elevation + dist_to_river
├─ Cell 8: K-Means clustering → risk_level
├─ Cell 19: Terrain analysis → slope + local_relief
├─ Cell 20: Hydrology analysis → major waterway distance + density
└─ Cell 24: Drainage analysis → drain distance

OUTPUT DATA
├─ 1,500+ buildings with 8 computed features
├─ Risk labels (High/Medium/Low)
└─ All exported to Map + GeoPackage + CSV
```

---

### Part 5: Key Takeaways for Decision-Makers

**What This Analysis Tells You:**

1. ✅ **Which buildings are at highest risk** – Colored on the map in real-time
2. ✅ **Why each building is at that risk level** – Hover to see elevation, waterway distances, terrain
3. ✅ **Which areas need priority** – High-risk clusters visible at a glance
4. ✅ **Data for detailed studies** – Export to GIS for neighborhood-level planning

**Limitations to Communicate:**

- ⚠️ Model is based on **current terrain & waterway data** (may not reflect future infrastructure changes)
- ⚠️ Does **not account for flood history** (because historical data wasn't available)
- ⚠️ **K-Means assumes buildings cluster naturally** (might not perfectly reflect reality)
- ⚠️ Uses **elevation above sea level**, not storm surge/monsoon-specific modeling

---

### Presentation Checklist

- [ ] **Show the map** → Open `interactive_flood_map_enhanced.html` in browser
- [ ] **Demonstrate hover tooltips** → Show at least 3 buildings with different risk levels
- [ ] **Toggle layers** → Hide/show each risk category
- [ ] **Explain K-Means** → Show cluster statistics and mapping logic
- [ ] **Highlight feature engineering** → Explain why each feature matters
- [ ] **Show outputs** → Brief walk-through of CSV, GeoPackage, PNG
- [ ] **State limitations** → Acknowledge uncertainty and future improvements
- [ ] **Call to action** → Suggest next steps (e.g., validate against historical floods, refine model)

---
