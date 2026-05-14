import streamlit as st
import osmnx as ox
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point

# Page configuration
st.set_page_config(layout="wide", page_title="15MinCity Validator")

if 'selected_geom' not in st.session_state:
    st.session_state.selected_geom = None

@st.cache_data(show_spinner=False)
def load_data(place_name):
    # Automatyczne doprecyzowanie, że szukamy w Warszawie, jeśli użytkownik wpisze tylko dzielnicę
    full_query = place_name if "Warsaw" in place_name else f"{place_name}, Warsaw, Poland"
    
    try:
        # Pobieranie budynków i aptek dla dowolnego obszaru
        b = ox.features_from_place(full_query, {"building": True}).reset_index(drop=True).to_crs(epsg=2180)
        p = ox.features_from_place(full_query, {"amenity": "pharmacy"}).reset_index(drop=True).to_crs(epsg=2180)
        
        # Optymalizacja
        b['geometry'] = b.geometry.simplify(1.0)
        b = b[['geometry']]
        
        if 'name' not in p.columns: p['name'] = 'Pharmacy'
        p['name'] = p['name'].fillna('Unnamed Pharmacy')
        
        return b, p[['geometry', 'name']]
    except Exception as e:
        # Zwracamy None, jeśli np. nazwa dzielnicy jest błędna lub nie ma tam danych
        return None, None

# --- SIDEBAR ---
st.sidebar.title("⚙️ Analysis Settings")

# Instrukcja dla użytkownika
st.sidebar.info("Type any Warsaw district (e.g., Mokotów, Ursynów, Wola) or a specific address.")
user_input = st.sidebar.text_input("Enter District/Location:", "Żoliborz")

dist = st.sidebar.slider("Analysis Range (meters):", 100, 2000, 500, step=50)

if st.sidebar.button("Clear Selection"):
    st.session_state.selected_geom = None
    st.rerun()

# --- MAIN UI ---
st.title("🏙️ 15MinCity-Validator")

# Uruchomienie ładowania danych
gdf_b, gdf_p = load_data(user_input)

if gdf_b is not None and not gdf_b.empty:
    st.markdown(f"_Current location: **{user_input}**. Click a building to start._")
    
    # Obliczanie środka dla nowej lokalizacji
    c_4326 = gdf_b.to_crs(epsg=4326).geometry.centroid
    m = folium.Map(
        location=[c_4326.y.mean(), c_4326.x.mean()], 
        zoom_start=14, # Trochę mniejszy zoom na start, żeby widzieć dzielnicę
        tiles="cartodbpositron"
    )

    # 1. Budynki
    folium.GeoJson(
        gdf_b.to_crs(epsg=4326),
        style_function=lambda x: {'color': '#3186cc', 'fillOpacity': 0.1, 'weight': 1}
    ).add_to(m)

    # 2. Logika bufora (zaznaczenie)
    active_buffer = None
    if st.session_state.selected_geom is not None:
        active_buffer = st.session_state.selected_geom.buffer(dist)
        folium.GeoJson(
            gpd.GeoSeries([active_buffer], crs="EPSG:2180").to_crs(epsg=4326),
            style_function=lambda x: {'color': '#FF8C00', 'fillColor': '#FFA500', 'fillOpacity': 0.2, 'weight': 1}
        ).add_to(m)
        folium.GeoJson(
            gpd.GeoSeries([st.session_state.selected_geom], crs="EPSG:2180").to_crs(epsg=4326),
            style_function=lambda x: {'color': 'red', 'fillColor': 'red', 'fillOpacity': 0.7, 'weight': 2}
        ).add_to(m)

    # 3. Apteki
    gdf_p_4326 = gdf_p.to_crs(epsg=4326)
    for idx, row in gdf_p.iterrows():
        is_in_range = active_buffer is not None and active_buffer.intersects(row.geometry)
        p_color = '#228B22' if is_in_range else '#FF0000'
        point_4326 = gdf_p_4326.loc[idx].geometry.centroid
        folium.CircleMarker(
            location=[point_4326.y, point_4326.x],
            radius=6, color=p_color, fill=True, fill_opacity=0.8, popup=row['name']
        ).add_to(m)

    # 4. Legenda
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; width: 155px; height: 80px; 
    background-color: white; border:1px solid grey; z-index:9999; font-size:11px;
    padding: 8px; border-radius: 5px; opacity: 0.9;">
    <b>Legend:</b><br>
    <i style="background: #3186cc; width: 10px; height: 10px; display: inline-block;"></i> Buildings<br>
    <i style="background: #FF0000; border-radius: 50%; width: 10px; height: 10px; display: inline-block;"></i> Pharmacy (Out)<br>
    <i style="background: #228B22; border-radius: 50%; width: 10px; height: 10px; display: inline-block;"></i> Pharmacy (In Range)
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # 5. Mapa i Kliknięcia
    st_data = st_folium(m, use_container_width=True, height=600, key=f"map_{user_input}", returned_objects=["last_clicked"])

    if st_data and st_data.get("last_clicked"):
        lat, lon = st_data["last_clicked"]["lat"], st_data["last_clicked"]["lng"]
        click_pt = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=2180).iloc[0]
        target = gdf_b[gdf_b.intersects(click_pt.buffer(10))]
        if not target.empty:
            st.session_state.selected_geom = target.iloc[0].geometry
            st.rerun()
else:
    st.error(f"Could not find data for '{user_input}'. Please check the name or try adding 'Warszawa' (e.g., 'Białołęka, Warszawa').")
