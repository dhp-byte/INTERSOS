"""Page Cartographie — choroplèthe, marqueurs et heatmap avec Folium."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from folium import Choropleth, CircleMarker, Map
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

import config
from utils.data_loader import get_region_centroids, load_all_sheets, load_geojson
from utils.filters import apply_filters, render_sidebar_filters

st.set_page_config(page_title="Cartographie — INTERSOS Tchad", page_icon="🗺️", layout="wide")

st.title("🗺️ Cartographie des interventions")
st.caption("Source géographique : `chad_admin1.geojson` (23 provinces, projection CRS84/WGS84)")

sheets = load_all_sheets()
selections = render_sidebar_filters(sheets)
geojson = load_geojson()
centroids = get_region_centroids()

if geojson is None:
    st.error("Fichier GeoJSON indisponible — la cartographie ne peut pas être affichée.")
    st.stop()

beneficiaries = apply_filters(sheets.get(config.SHEET_BENEFICIARIES, pd.DataFrame()), selections)

map_mode = st.radio(
    "Mode d'affichage",
    options=["Choroplèthe (bénéficiaires par province)", "Marqueurs groupés (clusters)", "Carte de chaleur"],
    horizontal=True,
)

CHAD_CENTER = [15.4542, 18.7322]

if beneficiaries.empty or not {"GPS_Lat", "GPS_Lon"}.issubset(beneficiaries.columns):
    st.warning("Aucune donnée géolocalisée ne correspond aux filtres sélectionnés.")
    st.stop()

if map_mode.startswith("Choroplèthe"):
    counts = beneficiaries["Province"].value_counts().reset_index()
    counts.columns = ["Province", "Beneficiaires"]

    m = Map(location=CHAD_CENTER, zoom_start=6, tiles="cartodbpositron")
    Choropleth(
        geo_data=geojson,
        data=counts,
        columns=["Province", "Beneficiaires"],
        key_on="feature.properties.name",
        fill_color="Oranges",
        fill_opacity=0.8,
        line_opacity=0.4,
        nan_fill_color="#EFEFEF",
        legend_name="Nombre de bénéficiaires enregistrés",
    ).add_to(m)

    for _, row in counts.iterrows():
        c = centroids.get(row["Province"])
        if c:
            CircleMarker(
                location=[c["lat"], c["lon"]],
                radius=4,
                color=config.COLOR_SECONDARY,
                fill=True,
                fill_opacity=0.9,
                tooltip=f"{row['Province']} : {row['Beneficiaires']} bénéficiaires",
            ).add_to(m)

    st_folium(m, use_container_width=True, height=560)

elif map_mode.startswith("Marqueurs"):
    m = Map(location=CHAD_CENTER, zoom_start=6, tiles="cartodbpositron")
    cluster = MarkerCluster().add_to(m)
    for _, row in beneficiaries.dropna(subset=["GPS_Lat", "GPS_Lon"]).iterrows():
        CircleMarker(
            location=[row["GPS_Lat"], row["GPS_Lon"]],
            radius=5,
            color=config.COLOR_PRIMARY,
            fill=True,
            fill_opacity=0.8,
            tooltip=(
                f"{row.get('Beneficiary_ID', '')} | {row.get('Sector', '')} | "
                f"{row.get('Village_Camp', row.get('Locality', ''))}"
            ),
        ).add_to(cluster)
    st_folium(m, use_container_width=True, height=560)

else:  # Heatmap
    m = Map(location=CHAD_CENTER, zoom_start=6, tiles="cartodbpositron")
    heat_data = beneficiaries.dropna(subset=["GPS_Lat", "GPS_Lon"])[["GPS_Lat", "GPS_Lon"]].values.tolist()
    HeatMap(heat_data, radius=18, blur=14).add_to(m)
    st_folium(m, use_container_width=True, height=560)

st.divider()
st.markdown("#### Bénéficiaires par province (données affichées)")
counts_table = beneficiaries["Province"].value_counts().reset_index()
counts_table.columns = ["Province", "Bénéficiaires"]
st.dataframe(counts_table, use_container_width=True)
