"""Page Analyse sectorielle — explore chaque feuille d'activité (Protection,
Santé, Nutrition, WASH, Sécurité Alimentaire, Abri/NFI) de façon générique."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import config
from utils.data_loader import get_sector_sheets, load_all_sheets
from utils.filters import apply_filters, render_sidebar_filters
from utils.kpi import sector_activity_kpis

st.set_page_config(page_title="Analyse sectorielle — INTERSOS Tchad", page_icon="🎯", layout="wide")

st.title("🎯 Analyse des activités sectorielles")

sheets = load_all_sheets()
selections = render_sidebar_filters(sheets)
sector_sheets = get_sector_sheets(sheets)

if not sector_sheets:
    st.error("Aucune feuille d'activité sectorielle détectée dans le classeur.")
    st.stop()

sector = st.selectbox("Secteur", options=list(sector_sheets.keys()))
df = apply_filters(sector_sheets[sector], selections)

if df.empty:
    st.warning("Aucune activité ne correspond aux filtres sélectionnés pour ce secteur.")
    st.stop()

kpi = sector_activity_kpis(df)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Activités", f"{kpi['n_activities']:,}".replace(",", " "))
c2.metric("Personnes atteintes", f"{kpi['total_reached']:,}".replace(",", " "))
c3.metric("Cible cumulée", f"{kpi['total_target']:,}".replace(",", " "))
c4.metric("Taux de couverture", f"{kpi['coverage_rate']:.1f} %")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Répartition par type d'activité")
    if "Activity_Type" in df.columns:
        act = df["Activity_Type"].value_counts().reset_index()
        act.columns = ["Type d'activité", "Nombre"]
        fig = px.bar(
            act.sort_values("Nombre"), x="Nombre", y="Type d'activité", orientation="h",
            template=config.PLOTLY_TEMPLATE, color_discrete_sequence=[config.COLOR_PRIMARY],
        )
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Statut des activités")
    if "Status" in df.columns:
        status = df["Status"].value_counts().reset_index()
        status.columns = ["Statut", "Nombre"]
        fig2 = px.pie(
            status, names="Statut", values="Nombre", hole=0.45,
            template=config.PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig2.update_layout(height=380)
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

col3, col4 = st.columns(2)
with col3:
    st.markdown("#### Activités par province")
    if "Province" in df.columns:
        prov = df["Province"].value_counts().reset_index()
        prov.columns = ["Province", "Nombre"]
        fig3 = px.bar(
            prov, x="Province", y="Nombre", text="Nombre",
            template=config.PLOTLY_TEMPLATE, color_discrete_sequence=[config.COLOR_SECONDARY],
        )
        fig3.update_layout(height=360)
        st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("#### Répartition par bailleur")
    if "Donor" in df.columns:
        donor = df["Donor"].value_counts().reset_index()
        donor.columns = ["Bailleur", "Nombre"]
        fig4 = px.pie(
            donor, names="Bailleur", values="Nombre", hole=0.4,
            template=config.PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig4.update_layout(height=360)
        st.plotly_chart(fig4, use_container_width=True)

# --- Indicateurs spécifiques au secteur (colonnes numériques métier) -------
st.divider()
st.markdown("#### Indicateurs numériques spécifiques au secteur")
numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in ("Notes",)]
if numeric_cols:
    stats = df[numeric_cols].agg(["sum", "mean", "min", "max"]).T.round(1)
    stats.columns = ["Somme", "Moyenne", "Min", "Max"]
    st.dataframe(stats, use_container_width=True)

st.divider()
st.markdown("#### Table détaillée (filtrée)")
st.dataframe(df, use_container_width=True, height=350)
