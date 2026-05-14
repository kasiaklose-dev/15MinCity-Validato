import streamlit as st
import osmnx as ox
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point

# Konfiguracja strony dla maksymalnej wydajności
st.set_page_config(layout="wide", page_title="15MinCity Validator")

# 1. INICJALIZACJA PAMIĘCI SESJI
if 'selected_geom' not in st.session_state:
    st.session_state.selected_geom = None

# 2. ZOPTYMALIZOWANE POBIERANIE DANYCH
@st.cache_data(show_spinner=False)
def load_data(place):
    try:
        # Pobieranie budynków i aptek z OSM
        b = ox.features_from_place(place, {"building": True}).reset_index(drop=True).to_crs(epsg=2180)
        p = ox.features_from_place(place, {"amenity": "pharmacy"}).reset_index(drop=True).to_crs(epsg=2180)
        
        # AGRESYWNE UPROSZCZENIE (Klucz do szybkości!)
        # Redukujemy liczbę punktów w obrysach budynków (tolerancja 1 metr)
        b['geometry'] = b.geometry.simplify(1.0)
        
        # Pozostawiamy tylko niezbędne kolumny, by nie obciążać transferu
        b = b[['geometry']]
        
        if 'name' not in p.columns: p['name'] = 'Apteka'
        p['name'] = p['name'].fillna('Apteka bez nazwy')
        
        return b, p[['geometry', 'name']]
    except Exception:
        return None, None

# --- INTERFEJS UŻYTKOWNIKA (SIDEBAR) ---
st.sidebar.title("⚙️ Ustawienia analizy")
area = st.sidebar.text_input("Lokalizacja (np. dzielnica, miasto):", "Żoliborz, Warszawa, Poland")
dist = st.sidebar.slider("Zasięg analizy (metry):", 100, 2000, 500, step=50)

if st.sidebar.button("Usuń zaznaczenie"):
    st.session_state.selected_geom = None
    st.rerun()

st.title("🏙️ 15MinCity-Validator")
st.markdown("_Kliknij budynek na mapie, aby sprawdzić dostępność aptek w zadanym zasięgu._")

# --- GŁÓWNA LOGIKA ---
gdf_b, gdf_p = load_data(area)

if gdf_b is not None and not gdf_b.empty:
    # Obliczanie środka mapy
    c_4326 = gdf_b.to_crs(epsg=4326).geometry.centroid
    m = folium.Map(
        location=[c_4326.y.mean(), c_4326.x.mean()], 
        zoom_start=15, 
        tiles="cartodbpositron",
        zoom_control=True
    )

    # 1. WARSTWA BUDYNKÓW (Zoptymalizowana)
    folium.GeoJson(
        gdf_b.to_crs(epsg=4326),
        style_function=lambda x: {'color': '#3186cc', 'fillOpacity': 0.1, 'weight': 1},
        smooth_factor=2.0 # Dodatkowe wygładzenie po stronie przeglądarki
    ).add_to(m)

    # 2. LOGIKA BUFORA
    active_buffer = None
    if st.session_state.selected_geom is not None:
        active_buffer = st.session_state.selected_geom.buffer(dist)
        
        # Rysowanie bufora (pomarańczowy)
        folium.GeoJson(
            gpd.GeoSeries([active_buffer], crs="EPSG:2180").to_crs(epsg=4326),
            style_function=lambda x: {'color': '#FF8C00', 'fillColor': '#FFA500', 'fillOpacity': 0.2, 'weight': 1}
        ).add_to(m)
        
        # Wyróżnienie wybranego budynku
        folium.GeoJson(
            gpd.GeoSeries([st.session_state.selected_geom], crs="EPSG:2180").to_crs(epsg=4326),
            style_function=lambda x: {'color': 'red', 'fillColor': 'red', 'fillOpacity': 0.7, 'weight': 2}
        ).add_to(m)

    # 3. WARSTWA APTEK (CircleMarker jest szybszy niż Icon Marker)
    gdf_p_4326 = gdf_p.to_crs(epsg=4326)
    for idx, row in gdf_p.iterrows():
        # Sprawdzenie kolizji w metrach
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

    # 4. LEGENDA (Kompaktowa)
    legend_html = '''
     <div style="position: fixed; bottom: 50px; left: 50px; width: 140px; height: 75px; 
     background-color: rgba(255, 255, 255, 0.9); border:1px solid grey; z-index:9999; font-size:11px;
     padding: 8px; border-radius: 5px; pointer-events: none;">
     <b>Legenda:</b><br>
     <i style="background: #3186cc; width: 10px; height: 10px; display: inline-block;"></i> Budynki<br>
     <i style="background: #FF0000; border-radius: 50%; width: 10px; height: 10px; display: inline-block;"></i> Apteka (poza)<br>
     <i style="background: #228B22; border-radius: 50%; width: 10px; height: 10px; display: inline-block;"></i> Apteka (w zasięgu)
     </div>
     '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # 5. WYŚWIETLENIE MAPY (Kluczowe parametry dla wydajności)
    st_data = st_folium(
        m, 
        use_container_width=True, 
        height=600, 
        key="v_final_optimized",
        returned_objects=["last_clicked"] # NIE pobieraj danych o widoku mapy, tylko kliknięcie!
    )

    # 6. OBSŁUGA KLIKNIĘCIA
    if st_data and st_data.get("last_clicked"):
        lat, lon = st_data["last_clicked"]["lat"], st_data["last_clicked"]["lng"]
        click_pt = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=2180).iloc[0]
        
        # Bufor 10m dla punktu kliknięcia, by łatwiej trafić w budynek
        target = gdf_b[gdf_b.intersects(click_pt.buffer(10))]
        if not target.empty:
            new_selection = target.iloc[0].geometry
            if st.session_state.selected_geom is None or not st.session_state.selected_geom.equals(new_selection):
                st.session_state.selected_geom = new_selection
                st.rerun()

else:
    st.warning("Nie znaleziono danych dla podanej lokalizacji. Spróbuj doprecyzować nazwę (np. 'Żoliborz, Warszawa').")
