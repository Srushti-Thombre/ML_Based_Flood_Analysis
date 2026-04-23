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

### **Cell 8: K-Means Clustering – Risk Classification**

- **Purpose:** Clusters buildings into 3 flood risk categories using elevation and distance to river
- **Key Operations:**
  1. Selects features: `['elevation', 'dist_to_river']`
  2. Scales features using `StandardScaler` (critical for K-Means)
  3. Runs K-Means with k=3 clusters
  4. Analyzes cluster centers to determine which cluster = High/Medium/Low risk
  5. Maps cluster IDs to risk labels based on elevation averages
- **Expected Output:**
  - "Clustering complete."
  - **Cluster Analysis table** showing mean elevation and distance for each cluster
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

## **🔑 KEY INSIGHT: Where Do Hydrology & Drainage Features Appear?**

### The Answer (Addressing Your Confusion)

You're confused because **the hydrology and drainage features DON'T create separate visible map layers** — instead, they are:

#### **1. Used in Data Computation (Behind the Scenes)**

- **Cell 20** adds `dist_to_major_waterway` and `waterway_density_300m` to every building record
- **Cell 24** adds `dist_to_drainage_m` to every building record
- These features are stored in the dataframe but don't appear as separate visual elements on the map

#### **2. Displayed in Tooltips (When You Hover Over Buildings)**

The **interactive_flood_map_enhanced.html** map shows these features **in the hover tooltip**:

- Hover over any building polygon
- A small popup appears showing the building's properties
- **You will see fields like:**
  - `dist_to_major_waterway: 450.25` meters
  - `waterway_density_300m: 0.00156` m/m²
  - `dist_to_drainage_m: 320.15` meters

**These tooltips are generated by Cell 22** in this section:

```python
tooltip_fields = [
    "risk_level", "elevation", "dist_to_river",
    "dist_to_drainage_m", "slope_deg", "local_relief_m",
    "dist_to_major_waterway", "waterway_density_300m"
]
```

#### **3. Technically Used in Risk Classification (Indirectly)**

While the basic K-Means clustering (**Cell 8**) only uses `elevation` and `dist_to_river`, the advanced features are:

- Computed and stored for analysis and export
- Available in the CSV report and GeoPackage for further analysis in QGIS/Python
- Visible in the tooltips so analysts can inspect local hydrology conditions

### Mapping: Which Cells Contribute to What in the HTML

| HTML Output Component               | Source Cells                            | What It Shows                                  |
| ----------------------------------- | --------------------------------------- | ---------------------------------------------- |
| **Map Center & Zoom**               | Cell 10 (basic), Cell 22 (enhanced)     | Center calculated from building bounds         |
| **Red Buildings (High Risk)**       | Cell 8 (clustering), Cell 22 (grouping) | Buildings with low elevation + close to rivers |
| **Orange Buildings (Medium Risk)**  | Cell 8, Cell 22                         | Intermediate elevation/distance properties     |
| **Green Buildings (Low Risk)**      | Cell 8, Cell 22                         | High elevation + far from rivers               |
| **Tooltip: risk_level**             | Cell 8 (assignment)                     | Risk classification from K-Means               |
| **Tooltip: elevation**              | Cell 7 (raster sampling)                | Mean DEM elevation for building                |
| **Tooltip: dist_to_river**          | Cell 7 (distance calc)                  | Distance to any waterway                       |
| **Tooltip: slope_deg**              | Cell 19 (terrain)                       | Slope steepness from DEM gradient              |
| **Tooltip: local_relief_m**         | Cell 19 (terrain)                       | Local elevation variation (3×3 window)         |
| **Tooltip: dist_to_major_waterway** | **Cell 20 (hydrology)** ✓               | **Distance to 75th percentile longest rivers** |
| **Tooltip: waterway_density_300m**  | **Cell 20 (hydrology)** ✓               | **Waterway length per area in 300m buffer**    |
| **Tooltip: dist_to_drainage_m**     | **Cell 24 (drainage)** ✓                | **Distance to dedicated drains/ditches**       |
| **Layer Control Panel**             | Cell 22                                 | Checkboxes to toggle High/Medium/Low layers    |
| **CSV Export**                      | Cell 22                                 | All features in tabular format                 |
| **GeoPackage Export**               | Cell 22                                 | All features + geometry for GIS software       |

---

## Summary

**The confusion is resolved:** Your hydrology and drainage features **ARE being used** — they're just not creating separate visual layers. Instead:

1. ✅ **They're computed and stored** in each building's record (Cells 20, 24)
2. ✅ **They're visible in tooltips** when you hover over buildings on the map (Cell 22)
3. ✅ **They're exported to CSV and GeoPackage** for further analysis (Cell 22)
4. ✅ **They contribute to a more complete data profile** for each building

If you want to see them as **separate visual layers** (e.g., colored by waterway density), you would need to add a step that colors buildings by these attributes or draws additional map features (rivers, drainage networks) — but the current approach shows them as queryable properties in the tooltips.

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

Good luck with your presentation! 🚀
