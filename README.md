# 🏙️ 15MinCity-Validator

### 🌐 [CLICK HERE TO OPEN THE LIVE APP](https://15mincity.streamlit.app/)

---

## 📖 About the Project
This tool was designed to automate urban analysis by evaluating the accessibility of pharmacies for residential buildings within a specific area. Inspired by the **"15-Minute City"** urban planning concept, the application fetches real-time data from OpenStreetMap, performs advanced spatial calculations, and generates a dynamic, interactive visualization.

## 💡 Project Philosophy & Approach
As an analyst rather than a full-time software engineer, I focused on leveraging modern tools to solve complex spatial problems:

* **Problem-First Mindset:** The core of this project is urban analysis, not just code. I focused on identifying service gaps and ensuring data accuracy to provide actionable insights for urban planning.
* **AI-Assisted Development:** I utilized AI tools to bridge the gap between analytical requirements and technical implementation. This allowed for the creation of a sophisticated GIS tool that would typically require a dedicated development team.
* **Tool Synergy:** My strength lies in knowing how to integrate various technologies (OSMnx + Folium + Streamlit) to deliver a professional-grade interactive report.

## 🚀 Key Features
* **Live Data Integration:** Fetches building and pharmacy data directly from the OpenStreetMap API.
* **Interactive Analysis:** Features a real-time range slider (100m – 2000m) for instant accessibility visualization upon clicking a building.
* **Spatial Accuracy:** Utilizes projected coordinate systems (EPSG:2180) for precise metric distance measurements.
* **Dynamic Highlighting:** Pharmacies within the range automatically turn green once the buffer is generated.

## 🛠️ Tech Stack
* **Analysis:** Python (GeoPandas, OSMnx, Pandas)
* **Visualization:** Folium, Streamlit
* **Geo-Math:** Shapely, PyProj (precise metric projection)

---

### 🔗 Application Link: 
[https://15mincity.streamlit.app/](https://15mincity.streamlit.app/)

*This project was created for analytical and educational purposes.*
