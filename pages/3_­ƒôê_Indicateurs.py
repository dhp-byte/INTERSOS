"""Page Indicateurs — suivi de la feuille Indicator_Tracker."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config
from utils.data_loader import load_all_sheets
from utils.filters import apply_filters, render_sidebar_filters
from utils.kpi import indicator_summary

st.set_page_config(page_title="Indicateurs — INTERSOS Tchad", page_icon="📈", layout="wide")

st.title("📈 Suivi des indicateurs (Indicator Tracker)")

sheets = load_all_sheets()
selections = render_sidebar_filters(sheets)
df = apply_filters(sheets.get(config.SHEET_INDICATORS, pd.DataFrame()), selections)

if df.empty:
    st.warning("Aucun indicateur ne correspond aux filtres sélectionnés.")
    st.stop()

summary = indicator_summary(df)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Indicateurs suivis", summary["n_indicators"])
c2.metric("Taux d'atteinte moyen", f"{summary['avg_achievement']:.1f} %")
c3.metric("En bonne voie (≥90%)", summary["on_track"])
c4.metric("En retard (<90%)", summary["off_track"])

st.divider()

sectors = sorted(df["Sector"].dropna().unique()) if "Sector" in df.columns else []
sector_filter = st.selectbox("Filtrer par secteur (page uniquement)", options=["Tous"] + sectors)
view = df if sector_filter == "Tous" else df[df["Sector"] == sector_filter]

st.markdown("#### Taux d'atteinte par indicateur")
if "Achievement_%" in view.columns:
    chart_df = view.sort_values("Achievement_%")
    colors = [config.COLOR_SUCCESS if v >= 90 else (config.COLOR_WARNING if v >= 70 else config.COLOR_DANGER)
              for v in chart_df["Achievement_%"]]
    fig = go.Figure(go.Bar(
        x=chart_df["Achievement_%"], y=chart_df["Indicator"], orientation="h",
        marker_color=colors, text=chart_df["Achievement_%"].round(1).astype(str) + " %",
        textposition="outside",
    ))
    fig.add_vline(x=100, line_dash="dash", line_color=config.COLOR_NEUTRAL)
    fig.update_layout(height=max(400, 28 * len(chart_df)), template=config.PLOTLY_TEMPLATE,
                       xaxis_title="Taux d'atteinte (%)", margin=dict(l=10, r=40, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.markdown("#### Progression trimestrielle cumulée (T1 → T4)")
quarter_cols = [c for c in ("T1", "T2", "T3", "T4") if c in view.columns]
if quarter_cols and "Indicator" in view.columns:
    pick = st.multiselect("Indicateurs à afficher", options=view["Indicator"].tolist(),
                           default=view["Indicator"].tolist()[: min(5, len(view))])
    subset = view[view["Indicator"].isin(pick)]
    long_df = subset.melt(id_vars=["Indicator"], value_vars=quarter_cols, var_name="Trimestre", value_name="Valeur")
    fig2 = px.line(long_df, x="Trimestre", y="Valeur", color="Indicator", markers=True,
                    template=config.PLOTLY_TEMPLATE)
    fig2.update_layout(height=420)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.markdown("#### Table complète des indicateurs")
st.dataframe(view, use_container_width=True, height=350)
