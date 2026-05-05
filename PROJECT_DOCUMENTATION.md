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
