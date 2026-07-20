"""Page Bailleurs & Partenaires — agrège Donor/Partner sur toutes les feuilles."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config
from utils.data_loader import get_sector_sheets, load_all_sheets
from utils.filters import apply_filters, render_sidebar_filters

st.set_page_config(page_title="Bailleurs & Partenaires — INTERSOS Tchad", page_icon="💰", layout="wide")

st.title("💰 Bailleurs & Partenaires")

sheets = load_all_sheets()
selections = render_sidebar_filters(sheets)
sector_sheets = get_sector_sheets(sheets)

frames = []
for name, df in sector_sheets.items():
    fdf = apply_filters(df, selections)
    if {"Donor", "Partner"}.issubset(fdf.columns):
        tmp = fdf[["Donor", "Partner"]].copy()
        tmp["Secteur"] = name
        frames.append(tmp)

if not frames:
    st.warning("Aucune donnée bailleur/partenaire disponible pour les filtres sélectionnés.")
    st.stop()

combined = pd.concat(frames, ignore_index=True)

c1, c2 = st.columns(2)
c1.metric("Bailleurs actifs", combined["Donor"].nunique())
c2.metric("Partenaires actifs", combined["Partner"].nunique())

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Activités financées par bailleur")
    donor_counts = combined["Donor"].value_counts().reset_index()
    donor_counts.columns = ["Bailleur", "Activités"]
    fig = px.bar(
        donor_counts.sort_values("Activités"), x="Activités", y="Bailleur", orientation="h",
        template=config.PLOTLY_TEMPLATE, color_discrete_sequence=[config.COLOR_PRIMARY],
    )
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Activités mises en œuvre par partenaire")
    partner_counts = combined["Partner"].value_counts().reset_index()
    partner_counts.columns = ["Partenaire", "Activités"]
    fig2 = px.bar(
        partner_counts.sort_values("Activités"), x="Activités", y="Partenaire", orientation="h",
        template=config.PLOTLY_TEMPLATE, color_discrete_sequence=[config.COLOR_SECONDARY],
    )
    fig2.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

st.markdown("#### Matrice Bailleur × Secteur (nombre d'activités)")
matrix = combined.pivot_table(index="Donor", columns="Secteur", values="Partner", aggfunc="count", fill_value=0)
fig3 = px.imshow(
    matrix, text_auto=True, aspect="auto", color_continuous_scale="Oranges",
    labels=dict(x="Secteur", y="Bailleur", color="Activités"),
)
fig3.update_layout(height=420)
st.plotly_chart(fig3, use_container_width=True)

st.divider()
st.markdown("#### Matrice Bailleur × Partenaire (Sankey des financements)")
sankey_df = combined.groupby(["Donor", "Partner"]).size().reset_index(name="Activités")
donors_list = sankey_df["Donor"].unique().tolist()
partners_list = sankey_df["Partner"].unique().tolist()
labels = donors_list + partners_list

sankey = go.Figure(go.Sankey(
    node=dict(
        label=labels,
        pad=12,
        thickness=14,
        color=[config.COLOR_PRIMARY] * len(donors_list) + [config.COLOR_SECONDARY] * len(partners_list),
    ),
    link=dict(
        source=[donors_list.index(d) for d in sankey_df["Donor"]],
        target=[len(donors_list) + partners_list.index(p) for p in sankey_df["Partner"]],
        value=sankey_df["Activités"],
    ),
))
sankey.update_layout(height=500, font_size=11)
st.plotly_chart(sankey, use_container_width=True)
