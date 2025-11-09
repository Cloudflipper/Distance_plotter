# 🚗 Shanghai OSRM Travel Time Visualization

This project generates a high-resolution travel time heatmap from a given origin point in Shanghai using a locally deployed **OSRM (Open Source Routing Machine)** backend.  
It builds a uniform grid of latitude-longitude coordinates, queries OSRM for estimated driving times, filters out water regions, and visualizes the results on an OpenStreetMap base map.

## ⚙️ Parameters

At the top of `runpic.py`, you can adjust the following parameters to control the experiment:

| Parameter | Description | Default |
|------------|-------------|----------|
| `OSRM_URL` | URL of the local OSRM server | `"http://localhost:5000"` |
| `PROFILE` | OSRM routing profile (`driving`, `walking`, `cycling`) | `"driving"` |
| `ORIGIN_LAT` | Latitude of the origin point (e.g., SJTU dormitory) | `31.198606` |
| `ORIGIN_LON` | Longitude of the origin point | `121.432725` |
| `LAT_MIN`, `LAT_MAX` | Latitude bounds for the analysis region | `30.7`, `31.35` |
| `LON_MIN`, `LON_MAX` | Longitude bounds for the analysis region | `121.18`, `121.86` |
| `STEP` | Grid step in degrees (smaller = denser grid, slower runtime) | `0.001` |
| `output_csv` | Path to save raw travel-time data | `"osrm_times.csv"` |
| `output_png` | Path to save the final visualization | `"osrm_times_map_shanghai.png"` |

## 🧭 How to Use

### 1. **Prepare Environment**

Install required dependencies (Python ≥3.10):

```bash
conda create -n osrm python=3.10
conda activate osrm
pip install -r requirements.txt
```

### 2. **Start Local OSRM Server**

Download Shanghai OSM data and build the routing graph:

```bash
wget https://download.geofabrik.de/asia/china/shanghai-latest.osm.pbf  
docker pull osrm/osrm-backend
docker run -t -i -p 5000:5000 -v $PWD:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/shanghai-latest.osm.pbf
docker run -t -i -p 5000:5000 -v $PWD:/data osrm/osrm-backend osrm-partition /data/shanghai-latest.osrm
docker run -t -i -p 5000:5000 -v $PWD:/data osrm/osrm-backend osrm-customize /data/shanghai-latest.osrm
docker run -t -i -p 5000:5000 -v $PWD:/data osrm/osrm-backend osrm-routed --algorithm mld /data/shanghai-latest.osrm
```

Leave the OSRM server running on port `5000`.

### 3. **Run the Script**

In another terminal:

```bash
python runpic.py
```

The script will:
1. Generate a uniform geographic grid across Shanghai.  
2. Query OSRM in batches for travel times from the origin point.  
3. Remove grid points falling inside Shanghai’s rivers and coastal waters.  
4. Render and save a colored travel-time map.

### 4. **Outputs**

- **Map image:**  
  `osrm_times_map_shanghai.png` — A heatmap of travel times:
  - Blue → fast / close
  - Yellow → medium
  - Red → slow / distant  
  (Capped at 3600 s; all values above appear as red)

### 5. **Notes**

- The base map tiles are fetched from **OpenStreetMap Mapnik**.  
- OSMnx is used to retrieve Shanghai’s administrative boundary and water polygons.  
- You can adjust `cmap`, `vmin`, `vmax`, and `alpha` to tune visualization style.  
- Increasing grid resolution (`STEP`) will produce finer results but may increase runtime.

