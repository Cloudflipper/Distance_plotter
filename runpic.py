import requests
import numpy as np
import geopandas as gpd
import osmnx as ox
from shapely.geometry import Point
from shapely.prepared import prep
from tqdm import tqdm
import matplotlib.pyplot as plt
import contextily as cx


OSRM_URL = "http://localhost:5000"
PROFILE = "driving"              
# ORIGIN_LAT = 31.0265             # 纬度
# ORIGIN_LON = 121.4330            # 经度
ORIGIN_LAT = 31.198606             
ORIGIN_LON = 121.432725 

TITLE = "Travel Time from SJTU Xuhui Dorm"

max_points_per_batch = 99        
output_csv = "osrm_times.csv"
output_png = "osrm_times_map_xuhui.png"
ox.settings.use_cache = True
ox.settings.cache_folder = "./osm_cache"

# 经纬度范围（上海）
LAT_MIN, LAT_MAX = 30.7, 31.35
LON_MIN, LON_MAX = 121.18, 121.86
STEP = 0.001  # 网格步长


def make_fixed_grid(lat_min, lat_max, lon_min, lon_max, step):
    lats = np.arange(lat_min, lat_max + step, step)
    lons = np.arange(lon_min, lon_max + step, step)
    points = [Point(lon, lat) for lat in lats for lon in lons]
    gdf = gpd.GeoDataFrame(geometry=points, crs="EPSG:4326")
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y
    return gdf


def osrm_table_times(origins, destinations):
    o = origins[0]
    coords = [f"{o[0]},{o[1]}"] + [f"{d[0]},{d[1]}" for d in destinations]
    url = f"{OSRM_URL}/table/v1/{PROFILE}/" + ";".join(coords)
    params = {"sources": "0", "annotations": "duration"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data["durations"][0][1:]


grid = make_fixed_grid(LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, STEP)
print(f"Number of Grid points: {len(grid)}")

origin = (ORIGIN_LON, ORIGIN_LAT)
dest_points = list(zip(grid["lon"], grid["lat"]))
times = np.zeros(len(dest_points))

print("查询中")
for i in tqdm(range(0, len(dest_points), max_points_per_batch)):
    batch = dest_points[i:i + max_points_per_batch]
    t = osrm_table_times([origin], batch)
    times[i:i + len(batch)] = np.array(t)

grid["time_sec"] = times
grid.to_csv(output_csv, index=False)
print(f"格点信息已保存到 {output_csv}")

# Remove water

sh_boundary = ox.geocode_to_gdf("Shanghai, China")

tags = {
    "natural": ["water", "bay"],
    "waterway": ["riverbank", "river"]
}
water = ox.features_from_place("Shanghai, China", tags=tags)

water = water[water.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()

water = gpd.overlay(water, sh_boundary, how="intersection")

water_union = water.unary_union
prep_water = prep(water_union)

grid["on_land"] = ~grid.geometry.apply(lambda p: prep_water.intersects(p))
land_grid = grid[grid["on_land"]].copy()



valid = land_grid[np.isfinite(land_grid["time_sec"])]
valid = valid[valid["time_sec"] < 9000]
gdf_3857 = valid.to_crs(epsg=3857)

minx, miny, maxx, maxy = gdf_3857.total_bounds
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_title(TITLE, fontsize=13, pad=15)

scatter = gdf_3857.plot(
    ax=ax,
    column="time_sec",
    cmap="turbo",
    markersize=10,
    alpha=0.1,
    legend=True,
    linewidth=0,
    edgecolor="none",
    vmin=0,
    vmax=3600
)

cx.add_basemap(ax, crs=gdf_3857.crs.to_string(), source=cx.providers.OpenStreetMap.Mapnik)
ax.set_xlim(minx, maxx)
ax.set_ylim(miny, maxy)
ax.set_axis_off()
plt.tight_layout()
plt.savefig(output_png, dpi=250, bbox_inches="tight")
plt.close()

print(f"图片保存到{output_png}")
