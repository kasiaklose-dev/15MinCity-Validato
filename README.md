🏙️ 15MinCity-Validator

This tool is designed to automate urban analysis by evaluating the accessibility of pharmacies for residential buildings within a given area. Inspired by the "15-Minute City" urban planning concept, the application fetches real-time data from OpenStreetMap, performs advanced spatial calculations, and generates a dynamic interactive visualization.
💡 Project Philosophy & Approach

As an analyst rather than a full-time software engineer, my approach to this project was focused on leveraging modern tools to solve complex spatial problems.

    Problem-First Mindset: The core of this project is urban analysis, not just code. I focused on identifying service gaps and data accuracy to provide actionable insights for urban planning.

    AI-Assisted Development: I utilized AI tools to bridge the gap between my analytical requirements and the technical implementation. This allowed me to build a sophisticated GIS tool that would typically require a dedicated development team.

    Tool Synergy: My strength lies in knowing which tools to combine (OSMnx + Folium + Turf.js) to deliver a professional-grade interactive report.

🚀 Key Features

    Live Data Integration: Fetches building and pharmacy data directly from the OpenStreetMap API.

    Interactive Analysis: Includes a real-time range slider (100m - 2000m) to visualize accessibility on the fly.

    Spatial Accuracy: Uses projected coordinate systems (EPSG:2180) for precise metric distance measurements.

    Data Portability: Exports results to GeoPackage (.gpkg) format, compatible with QGIS and ArcGIS.

🛠️ Tech Stack

    Analysis: Python (GeoPandas, OSMnx, Pandas)

    Visualization: Folium, Leaflet.js

    Geo-Math: Turf.js (for client-side dynamic buffering)
