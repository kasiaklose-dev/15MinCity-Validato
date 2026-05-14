import streamlit as st
import osmnx as ox
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point

st.set_page_config(layout="wide", page_title="Pharmacy GIS Pro")

# --- PAMIĘĆ SESJI ---
if 'selected_geom' not in st.session_state:
    st.session_state.selected_geom = None

@st.cache_data(show_spinner=False)
def load_data(place):
    # Pobieramy budynki i apteki
    b = ox.features_from_place(place, {"building": True}).reset_index(drop=True).to_crs(epsg=2180)
    p = ox.features_from_place(place, {"amenity": "pharmacy"}).reset_index(drop=True).to_crs(epsg=2180)
    
    # Optymalizacja geometrii budynków (brak tooltipów = brak zbędnych danych tekstowych)
    b['geometry'] = b.geometry.simplify(0.5) 
    
    if 'name' not in p.columns: p['name'] = 'Apteka'
    p['name'] = p['name'].fillna('Apteka bez nazwy')
    return b[['geometry']], p[['geometry', 'name']]

# --- UI ---
st.title("🏥 Analiza Dostępności Aptek")

area = st.sidebar.text_input("Lokalizacja:", "Żoliborz, Warszawa, Poland")
dist = st.sidebar.slider("Zasięg (metry):", 100, 2000, 500)

if st.sidebar.button("Usuń zaznaczenie"):
    st.session_state.selected_geom = None
    st.rerun()

try:
    gdf_b, gdf_p = load_data(area)
    
    # Środek mapy
    c = gdf_b.to_crs(epsg=4326).geometry.centroid
    m = folium.Map(location=[c.y.mean(), c.x.mean()], zoom_start=15, tiles="cartodbpositron")

    # 1. Budynki (USUNIĘTY TOOLTIP - etykieta "Budynek" nie będzie się już pojawiać)
    folium.GeoJson(
        gdf_b.to_crs(epsg=4326),
        style_function=lambda x: {'color': '#3186cc', 'fillOpacity': 0.1, 'weight': 1}
    ).add_to(m)

    # 2. Bufor i Podświetlanie
    active_buffer = None
    if st.session_state.selected_geom is not None:
        active_buffer = st.session_state.selected_geom.buffer(dist)
        
        # Rysowanie pomarańczowego bufora
        folium.GeoJson(
            gpd.GeoSeries([active_buffer], crs="EPSG:2180").to_crs(epsg=4326),
            style_function=lambda x: {'color': '#FF8C00', 'fillColor': '#FFA500', 'fillOpacity': 0.2, 'weight': 1}
        ).add_to(m)
        
        # Wybrany budynek (czerwony obrys)
        folium.GeoJson(
            gpd.GeoSeries([st.session_state.selected_geom], crs="EPSG:2180").to_crs(epsg=4326),
            style_function=lambda x: {'color': 'red', 'fillColor': 'red', 'fillOpacity': 0.7, 'weight': 2}
        ).add_to(m)

    # 3. Apteki
    gdf_p_4326 = gdf_p.to_crs(epsg=4326)
    for idx, row in gdf_p.iterrows():
        is_in_range = active_buffer is not None and active_buffer.intersects(row.geometry)
        color = '#228B22' if is_in_range else '#FF0000'
        
        geom_view = gdf_p_4326.loc[idx].geometry.centroid
        folium.Circle(
            location=[geom_view.y, geom_view.x],
            radius=12,
            color=color,
            fill=True,
            fill_opacity=0.9,
            popup=row['name']
        ).add_to(m)

    # 4. LEGENDA (ZAKTUALIZOWANA - usunięty "Zasięg")
    legend_html = f'''
     <div style="position: fixed; bottom: 30px; left: 30px; width: 150px; height: 80px; 
     background-color: white; border:2px solid grey; z-index:9999; font-size:12px;
     padding: 10px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">
     <b>Legenda:</b><br>
     <i style="background: #3186cc; width: 10px; height: 10px; display: inline-block;"></i> Budynki<br>
     <i style="background: #FF0000; border-radius: 50%; width: 10px; height: 10px; display: inline-block;"></i> Apteka (poza)<br>
     <i style="background: #228B22; border-radius: 50%; width: 10px; height: 10px; display: inline-block;"></i> Apteka (w zasięgu)
     </div>
     '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Renderowanie (szybkie)
    st_data = st_folium(m, width="100%", height=600, key="v_final_clean", returned_objects=["last_clicked"])

    # Obsługa kliknięcia
    if st_data and st_data.get("last_clicked"):
        lat, lon = st_data["last_clicked"]["lat"], st_data["last_clicked"]["lng"]
        click_pt = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=2180).iloc[0]
        
        target = gdf_b[gdf_b.intersects(click_pt.buffer(10))]
        if not target.empty:
            new_selection = target.iloc[0].geometry
            if st.session_state.selected_geom is None or not st.session_state.selected_geom.equals(new_selection):
                st.session_state.selected_geom = new_selection
                st.rerun()

except Exception as e:
    st.info("Pobieranie danych OSM...")
