# 🏙️ 15MinCity-Validator

### 🌐 [KLIKNIJ TUTAJ, ABY OTWORZYĆ APLIKACJĘ LIVE](https://15mincity-validato-f4nrx8mof4rqudbxlpabal.streamlit.app/)

---

## 📖 O projekcie
Ten instrument został zaprojektowany w celu automatyzacji analizy urbanistycznej poprzez ocenę dostępności aptek dla budynków mieszkalnych na danym obszarze. Zainspirowana koncepcją urbanistyczną **"15-Minute City"**, aplikacja pobiera dane w czasie rzeczywistym z OpenStreetMap, wykonuje zaawansowane obliczenia przestrzenne i generuje dynamiczną, interaktywną wizualizację.

## 💡 Filozofia projektu i podejście
Jako analityk, a nie programista pełnoetatowy, skupiłam się na wykorzystaniu nowoczesnych narzędzi do rozwiązywania złożonych problemów przestrzennych:

* **Problem-First Mindset:** Rdzeniem projektu jest analiza miejska, a nie tylko kod. Skupiłam się na identyfikacji luk w usługach i dokładności danych, aby zapewnić przydatne informacje dla planowania przestrzennego.
* **AI-Assisted Development:** Wykorzystałam narzędzia AI, aby połączyć wymagania analityczne z implementacją techniczną. Pozwoliło to na zbudowanie zaawansowanego narzędzia GIS, które zazwyczaj wymagałoby dedykowanego zespołu deweloperskiego.
* **Synergia Narzędzi:** Moją siłą jest wiedza, które narzędzia połączyć (OSMnx + Folium + Streamlit), aby dostarczyć profesjonalny interaktywny raport.

## 🚀 Kluczowe Funkcje
* **Integracja Danych Live:** Pobiera dane o budynkach i aptekach bezpośrednio z API OpenStreetMap.
* **Interaktywna Analiza:** Zawiera suwak zasięgu w czasie rzeczywistym (100m - 2000m) do błyskawicznej wizualizacji dostępności po kliknięciu w budynek.
* **Dokładność Przestrzenna:** Wykorzystuje układy współrzędnych (EPSG:2180) dla precyzyjnych pomiarów odległości w metrach.
* **Dynamiczne Podświetlanie:** Apteki w zasięgu automatycznie zmieniają kolor na zielony po wygenerowaniu bufora.

## 🛠️ Stack Techniczny
* **Analiza:** Python (GeoPandas, OSMnx, Pandas)
* **Wizualizacja:** Folium, Streamlit
* **Geo-Math:** Shapely, PyProj (precyzyjne rzutowanie metryczne)

---

### 🔗 Link do aplikacji: 
[https://15mincity-validato-f4nrx8mof4rqudbxlpabal.streamlit.app/](https://15mincity-validato-f4nrx8mof4rqudbxlpabal.streamlit.app/)

*Projekt stworzony w celach analitycznych i edukacyjnych.*
