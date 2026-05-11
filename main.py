import osmnx as ox
import folium
import math
import json

class GISAutomationTool:
    def __init__(self, city_name):
        self.city_name = city_name
        self.gdf_now = None
        self.gdf_pharm = None

    def fetch_current_buildings(self):
        """Pobieranie aktualnych danych budynków z OpenStreetMap."""
        print(f"--- Pobieranie aktualnych budynków dla: {self.city_name} ---")
        self.gdf_now = ox.features_from_place(self.city_name, {"building": True})
        self.gdf_now = self.gdf_now.reset_index()

    def fetch_pharmacies(self):
        """Pobieranie aptek z OpenStreetMap."""
        print(f"--- Pobieranie aptek dla: {self.city_name} ---")
        self.gdf_pharm = ox.features_from_place(self.city_name, {"amenity": "pharmacy"})
        self.gdf_pharm = self.gdf_pharm.reset_index()

    def compute_pharmacy_access(self, distance=800):
        """Oznaczamy budynki dostępem do aptek i przygotowujemy dane do mapy."""
        if self.gdf_now is None:
            return
        if self.gdf_pharm is None:
            self.fetch_pharmacies()
        buildings = self.gdf_now.to_crs(epsg=2180).copy()
        pharmacies = self.gdf_pharm.to_crs(epsg=2180).copy()
        pharmacies = pharmacies.set_geometry('geometry')
        pharmacies['pharmacy_id'] = pharmacies.index.astype(str)
        pharmacy_index = pharmacies.sindex

        buildings['pharmacy_count'] = 0
        buildings['nearest_pharmacy'] = None
        buildings['nearest_distance'] = None
        buildings['pharmacy_access'] = 'NIE'

        for i, row in buildings.iterrows():
            buffer_geom = row.geometry.buffer(distance)
            possible = list(pharmacy_index.intersection(buffer_geom.bounds))
            candidates = pharmacies.iloc[possible] if possible else pharmacies.iloc[[]]
            nearby = candidates[candidates.intersects(buffer_geom)]
            count = len(nearby)
            buildings.at[i, 'pharmacy_count'] = int(count)
            if count:
                center = row.geometry.centroid
                distances = nearby.geometry.distance(center)
                nearest_idx = distances.idxmin()
                nearest = nearby.loc[nearest_idx]
                buildings.at[i, 'nearest_pharmacy'] = nearest.get('name', 'Brak nazwy')
                buildings.at[i, 'nearest_distance'] = int(distances.min())
            else:
                buildings.at[i, 'nearest_pharmacy'] = 'Brak apteki w zasięgu'
                buildings.at[i, 'nearest_distance'] = None
            buildings.at[i, 'pharmacy_access'] = 'TAK' if count else 'NIE'

        self.gdf_now = buildings
        self.gdf_pharm = pharmacies
        print(f"--- Obliczono dostęp do aptek w zasięgu {distance} m dla {len(buildings)} budynków ---")

    def save_results(self, filename="budynki_zoliborz.gpkg"):
        """Eksport do GeoPackage z budynkami i aptekami."""
        if self.gdf_now is not None:
            df = self.gdf_now[["geometry", "pharmacy_access", "pharmacy_count", "nearest_pharmacy", "nearest_distance"]].copy()
            df.to_file(filename, layer="buildings", driver="GPKG")
            print(f"--- Budynki zapisane do {filename} (warstwa: buildings) ---")
        if self.gdf_pharm is not None:
            df_pharm = self.gdf_pharm[["geometry", "name", "pharmacy_id"]].copy()
            df_pharm.to_file(filename, layer="pharmacies", driver="GPKG")
            print(f"--- Apteki zapisane do {filename} (warstwa: pharmacies) ---")

    def create_map(self, filename="mapa_budynkow_zoliborz.html"):
        """Tworzenie interaktywnej mapy najbliższych aptek i bufora z suwakiem."""
        if self.gdf_now is None or self.gdf_pharm is None:
            return

        buildings = self.gdf_now.to_crs(epsg=4326)
        pharmacies = self.gdf_pharm.to_crs(epsg=4326)
        center_lat = buildings.geometry.centroid.y.mean()
        center_lon = buildings.geometry.centroid.x.mean()

        m = folium.Map(location=[center_lat, center_lon], zoom_start=15)

        buildings_layer = folium.GeoJson(
            buildings,
            name="Budynek",
            style_function=lambda feature: {
                'color': 'blue',
                'weight': 1,
                'opacity': 0.8,
                'fillColor': 'blue',
                'fillOpacity': 0.1
            }
        ).add_to(m)

        pharmacy_points = []
        for _, row in pharmacies.iterrows():
            name = row.get('name', 'Apteka')
            if name is None or (isinstance(name, float) and math.isnan(name)):
                name = 'Apteka'
            pharmacy_points.append({
                'id': str(row['pharmacy_id']),
                'name': str(name),
                'lat': row.geometry.y,
                'lon': row.geometry.x
            })

        m.get_root().html.add_child(folium.Element(
            '<script src="https://cdn.jsdelivr.net/npm/@turf/turf@6/turf.min.js"></script>'
        ))

        controls_html = '''
            <div id="slider-box" style="position: absolute; top: 10px; right: 10px; z-index:9999; background: white; padding: 10px; border: 1px solid #888; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.25); width: 250px;">
                <div style="font-weight:bold; margin-bottom:5px;">Zasięg apteki</div>
                <input id="rangeSlider" type="range" min="100" max="2000" step="100" value="800" style="width:100%;">
                <div style="margin-top:6px;">Zasięg: <span id="rangeValue">800</span> m</div>
                <div style="margin-top:4px;">Wyniki: <span id="countValue">0</span> aptek</div>
            </div>
        '''
        m.get_root().html.add_child(folium.Element(controls_html))

        legend_html = '''
            <div id="map-legend" style="position: absolute; bottom: 10px; right: 10px; z-index:9999; background: white; padding: 10px; border: 1px solid #888; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.25); width: 200px; font-size: 14px;">
                <div style="font-weight:bold; margin-bottom:5px;">Legenda</div>
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                    <div style="width:20px; height:20px; border-radius:50%; background:white; border:2px solid black; display:flex; align-items:center; justify-content:center; font-size:16px; color:red;">✚</div>
                    <div>Apteka (domyślna)</div>
                </div>
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                    <div style="width:20px; height:20px; border-radius:50%; background:white; border:2px solid black; display:flex; align-items:center; justify-content:center; font-size:16px; color:green;">✚</div>
                    <div>Apteka w zasięgu</div>
                </div>
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                    <div style="width:20px; height:20px; border-radius:50%; background:white; border:2px solid black; display:flex; align-items:center; justify-content:center; font-size:16px; color:gray;">✚</div>
                    <div>Apteka poza zasięgiem</div>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="width:20px; height:20px; border:2px solid orange; background: rgba(255,165,0,0.2);"></div>
                    <div>Zasięg apteki</div>
                </div>
            </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        script = """
        <script>
        window.addEventListener('load', function() {
            var pharmacyData = """ + json.dumps(pharmacy_points) + """;
            var selectedBuilding = null;
            var selectedLayer = null;
            var radiusMeters = 800;
            var pharmacyMarkers = {};
            var pharmacyLayer = L.layerGroup().addTo(""" + m.get_name() + """);
            var pharmacyRedIcon = L.divIcon({
                className: 'pharmacy-cross-icon pharmacy-red',
                html: '<div style="font-size:30px; color:red; line-height:1; background:white; border:2px solid black; border-radius:50%; width:36px; height:36px; display:flex; align-items:center; justify-content:center;">✚</div>',
                iconSize: [36, 36],
                iconAnchor: [18, 18]
            });
            var pharmacyGreenIcon = L.divIcon({
                className: 'pharmacy-cross-icon pharmacy-green',
                html: '<div style="font-size:30px; color:green; line-height:1; background:white; border:2px solid black; border-radius:50%; width:36px; height:36px; display:flex; align-items:center; justify-content:center;">✚</div>',
                iconSize: [36, 36],
                iconAnchor: [18, 18]
            });
            var pharmacyGrayIcon = L.divIcon({
                className: 'pharmacy-cross-icon pharmacy-gray',
                html: '<div style="font-size:30px; color:gray; line-height:1; background:white; border:2px solid black; border-radius:50%; width:36px; height:36px; display:flex; align-items:center; justify-content:center;">✚</div>',
                iconSize: [36, 36],
                iconAnchor: [18, 18]
            });
            pharmacyData.forEach(function(ph) {
                var marker = L.marker([ph.lat, ph.lon], {icon: pharmacyRedIcon});
                marker.pharmacy_id = ph.id;
                marker.addTo(pharmacyLayer);
                pharmacyMarkers[ph.id] = marker;
            });

            var bufferLayer = L.geoJSON(null, {style: {color: 'orange', fillColor: 'orange', weight: 2, fillOpacity: 0.2}}).addTo(""" + m.get_name() + """);
            var buildingLayer = """ + buildings_layer.get_name() + """;

            function updateHighlights() {
                if (!selectedBuilding) {
                    document.getElementById('countValue').innerText = 0;
                    return;
                }
                bufferLayer.clearLayers();
                var buff = turf.buffer(selectedBuilding.feature, radiusMeters / 1000, {units: 'kilometers'});
                bufferLayer.addData(buff);

                var count = 0;
                for (var id in pharmacyMarkers) {
                    var marker = pharmacyMarkers[id];
                    var point = turf.point([marker.getLatLng().lng, marker.getLatLng().lat]);
                    if (turf.booleanPointInPolygon(point, buff)) {
                        marker.setIcon(pharmacyGreenIcon);
                        count += 1;
                    } else {
                        marker.setIcon(pharmacyGrayIcon);
                    }
                }
                document.getElementById('countValue').innerText = count;
            }

            function selectBuilding(layer) {
                if (selectedLayer) {
                    selectedLayer.setStyle({fillOpacity: 0.1, color: 'blue', fillColor: 'blue'});
                }
                selectedLayer = layer;
                selectedBuilding = layer;
                layer.setStyle({fillOpacity: 0.4, color: 'yellow', fillColor: 'yellow'});
                updateHighlights();
            }

            document.getElementById('rangeSlider').addEventListener('input', function(e) {
                radiusMeters = parseInt(e.target.value, 10);
                document.getElementById('rangeValue').innerText = radiusMeters;
                updateHighlights();
            });

            if (typeof buildingLayer !== 'undefined' && buildingLayer.eachLayer) {
                buildingLayer.eachLayer(function(layer) {
                    layer.on('click', function(e) {
                        selectBuilding(layer);
                    });
                });
            } else {
                console.error('buildingLayer is not available yet');
            }
        });
        </script>
        """
        m.get_root().html.add_child(folium.Element(script))

        folium.LayerControl().add_to(m)
        m.save(filename)
        print(f"--- Mapa zapisana do {filename} ---")
        print(f"Otwórz plik {filename} w przeglądarce, aby zobaczyć suwak i apteki w zasięgu.")

# --- URUCHOMIENIE SKRYPTU ---
if __name__ == "__main__":
    tool = GISAutomationTool("Żoliborz, Warszawa, Poland")
    tool.fetch_current_buildings()
    tool.compute_pharmacy_access(distance=800)
    tool.save_results("budynki_zoliborz.gpkg")
    tool.create_map("mapa_budynkow_zoliborz.html")