import streamlit as st
import osmnx as ox
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point

# Page configuration for maximum performance
st.set_page_config(layout="wide", page_title="15MinCity Validator")

# 1. SESSION STATE INITIALIZATION
if 'selected_geom' not in st.session_state:
    st.session_state.selected_geom = None

# 2. OPTIMIZED DATA LOADING
@st.cache_data(show_spinner=False)
def load_data(place):
    try:
        # Fetch buildings and pharmacies from OSM
        b = ox.features_from_place(place, {"building": True}).reset_index(drop=True).to_crs(epsg=2180)
        p = ox.features_from_place(place, {"amenity": "pharmacy"}).reset_index(drop=True).to_crs(epsg=2180)
        
        # AGGRESSIVE SIMPLIFICATION
        b['geometry'] = b.geometry.simplify(1.0)
        b = b[['geometry']]
        
        if 'name' not in p.columns: p['name'] = 'Pharmacy'
        p['name'] = p['name'].fillna('Unnamed Pharmacy')
        
        return b, p[['geometry', 'name']]
    except Exception:
        return None, None

# --- USER INTERFACE (SIDEBAR) ---
st.sidebar.title("⚙️ Analysis Settings")
area = st.sidebar.text_input("Location:", "Zoliborz, Warsaw, Poland")
dist = st.sidebar.slider("Analysis Range (meters):", 100, 2000, 500, step=50)

if st.sidebar.button("Clear Selection"):
    st.session_state.selected_geom = None
    st.rerun()

st.title("🏙️ 15MinCity-Validator")
st.markdown("_Click on a building to check pharmacy accessibility within the given range._")

# --- MAIN LOGIC ---
gdf_b, gdf_p = load_data(area)

if gdf_b is not None and not gdf_b.empty:
    # Calculate map center
    c_4326 = gdf_b.to_crs(epsg=4326).geometry.centroid
    m = folium.Map(
        location=[c_4326.y.mean(), c_4326.x.mean()], 
        zoom_start=15, 
        tiles="cartodbpositron"
    )

    # 1. BUILDINGS LAYER
    folium.GeoJson(
        gdf_b.to_crs(epsg=4326),
        style_function=lambda x: {'color': '#3186cc', 'fillOpacity': 0.1, 'weight': 1}
    ).add_to(m)

    # 2. BUFFER LOGIC
    active_buffer = None
    if st.session_state.selected_geom is not None:
        active_buffer = st.session_state.selected_geom.buffer(dist)
        
        # Draw buffer
        folium.GeoJson(
            gpd.GeoSeries([active_buffer], crs="EPSG:2180").to_crs(epsg=4326),
            style_function=lambda x: {'color': '#FF8C00', 'fillColor': '#FFA500', 'fillOpacity': 0.2, 'weight': 1}
        ).add_to(m)
        
        # Highlight selected building
        folium.GeoJson(
            gpd.GeoSeries([st.session_state.selected_geom], crs="EPSG:2180").to_crs(epsg=4326),
            style_function=lambda x: {'color': 'red', 'fillColor': 'red', 'fillOpacity': 0.7, 'weight': 2}
        ).add_to(m)

    # 3. PHARMACIES LAYER
    gdf_p_4326 = gdf_p.to_crs(epsg=4326)
    for idx, row in gdf_p.iterrows():
        is_in_range = active_buffer is not None and active_buffer.intersects(row.geometry)
        p_color = '#228B22' if is_in_range else '#FF0000'
        
        point_4326 = gdf_p_4326.loc[idx].geometry.centroid
        folium.CircleMarker(
            location=[point_4326.y, point_4326.x],
            radius=6,
            color=p_color,
            fill=True,
            fill_opacity=0.8,
            popup=row['name']
        ).add_to(m)

    # 4. LEGEND (HTML)
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; width: 150px; height: 80px; 
    background-color: white; border:1px solid grey; z-index:9999; font-size:11px;
    padding: 8px; border-radius: 5px; opacity: 0.9;">
    <b>Legend:</b><br>
    <i style="background: #3186cc; width: 10px; height: 10px; display: inline-block;"></i> Buildings<br>
    <i style="background: #FF0000; border-radius: 50%; width: 10px; height: 10px; display: inline-block;"></i> Pharmacy (Out)<br>
    <i style="background: #228B22; border-radius: 50%; width: 10px; height: 10px; display: inline-block;"></i> Pharmacy (In Range)
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # 5. DISPLAY
    st_data = st_folium(m, use_container_width=True, height=600, returned_objects=["last_clicked"])

    # 6. CLICK HANDLING
    if st_data and st_data.get("last_clicked"):
        lat, lon = st_data["last_clicked"]["lat"], st_data["last_clicked"]["lng"]
        click_pt = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=2180).iloc[0]
        target = gdf_b[gdf_b.intersects(click_pt.buffer(10))]
        if not target.empty:
            st.session_state.selected_geom = target.iloc[0].geometry
            st.rerun()
else:
    st.info("Loading or no data found...")
