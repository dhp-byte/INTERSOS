"""Page Bénéficiaires — analyse démographique et de vulnérabilité."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import config
from utils.data_loader import load_all_sheets
from utils.filters import apply_filters, render_sidebar_filters
from utils.kpi import beneficiary_kpis

st.set_page_config(page_title="Bénéficiaires — INTERSOS Tchad", page_icon="👥", layout="wide")

st.title("👥 Analyse des bénéficiaires")
st.caption("Source : feuille `Beneficiary_Registration`")

sheets = load_all_sheets()
selections = render_sidebar_filters(sheets)
df = apply_filters(sheets.get(config.SHEET_BENEFICIARIES, pd.DataFrame()), selections)

if df.empty:
    st.warning("Aucun bénéficiaire ne correspond aux filtres sélectionnés.")
    st.stop()

kpi = beneficiary_kpis(df)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Bénéficiaires", f"{kpi['total_beneficiaries']:,}".replace(",", " "))
c2.metric("Ménages", f"{kpi['total_households']:,}".replace(",", " "))
c3.metric("% Femmes", f"{kpi['pct_female']:.1f} %")
c4.metric("% Enregistrements complets", f"{kpi['pct_complete_registration']:.1f} %")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Pyramide des âges par sexe")
    if {"Age", "Sex"}.issubset(df.columns):
        bins = [0, 5, 12, 18, 30, 45, 60, 120]
        labels = ["0-4", "5-11", "12-17", "18-29", "30-44", "45-59", "60+"]
        tmp = df.copy()
        tmp["Tranche_age"] = pd.cut(tmp["Age"], bins=bins, labels=labels, right=False)
        pyramid = tmp.groupby(["Tranche_age", "Sex"], observed=True).size().reset_index(name="Nombre")
        pyramid["Nombre_signe"] = pyramid.apply(
            lambda r: -r["Nombre"] if r["Sex"] == "M" else r["Nombre"], axis=1
        )
        fig = px.bar(
            pyramid,
            x="Nombre_signe",
            y="Tranche_age",
            color="Sex",
            orientation="h",
            template=config.PLOTLY_TEMPLATE,
            color_discrete_map={"F": config.COLOR_PRIMARY, "M": config.COLOR_SECONDARY},
        )
        fig.update_layout(height=400, xaxis_title="Nombre de personnes (H à gauche / F à droite)")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Répartition par vulnérabilité")
    if "Vulnerability" in df.columns:
        vuln = df["Vulnerability"].value_counts().reset_index()
        vuln.columns = ["Vulnérabilité", "Nombre"]
        fig2 = px.treemap(
            vuln,
            path=["Vulnérabilité"],
            values="Nombre",
            color="Nombre",
            color_continuous_scale=["#F2A65A", "#E4610F", "#1B2A4A"],
        )
        fig2.update_layout(height=400, margin=dict(l=5, r=5, t=5, b=5))
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

col3, col4 = st.columns(2)
with col3:
    st.markdown("#### Bénéficiaires par secteur d'assistance")
    if "Sector" in df.columns:
        sec = df["Sector"].value_counts().reset_index()
        sec.columns = ["Secteur", "Nombre"]
        fig3 = px.pie(
            sec, names="Secteur", values="Nombre", hole=0.4,
            color_discrete_sequence=config.SECTOR_COLOR_SEQUENCE, template=config.PLOTLY_TEMPLATE,
        )
        fig3.update_layout(height=380)
        st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("#### Statut de déplacement par province")
    if {"Province", "Displacement_Status"}.issubset(df.columns):
        cross = df.groupby(["Province", "Displacement_Status"]).size().reset_index(name="Nombre")
        fig4 = px.bar(
            cross, x="Province", y="Nombre", color="Displacement_Status",
            template=config.PLOTLY_TEMPLATE, color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig4.update_layout(height=380, barmode="stack")
        st.plotly_chart(fig4, use_container_width=True)

st.divider()
st.markdown("#### Table détaillée (filtrée)")
st.dataframe(df, use_container_width=True, height=350)
