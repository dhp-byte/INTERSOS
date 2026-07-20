"""Page Exports — Excel, CSV et export d'un graphique en PNG."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

import config
from utils.data_loader import load_all_sheets
from utils.export import dataframe_to_csv_bytes, dataframe_to_excel_bytes, figure_to_png_bytes
from utils.filters import apply_filters, render_sidebar_filters

st.set_page_config(page_title="Exports — INTERSOS Tchad", page_icon="📤", layout="wide")

st.title("📤 Exports de données et de graphiques")

sheets = load_all_sheets()
selections = render_sidebar_filters(sheets)
filtered_sheets = {name: apply_filters(df, selections) for name, df in sheets.items()}

timestamp = datetime.now().strftime("%Y%m%d_%H%M")

st.markdown("### 📗 Export Excel complet (toutes les feuilles filtrées)")
excel_bytes = dataframe_to_excel_bytes(filtered_sheets)
st.download_button(
    "⬇️ Télécharger le classeur Excel filtré",
    data=excel_bytes,
    file_name=f"INTERSOS_Tchad_export_{timestamp}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

st.divider()

st.markdown("### 📄 Export CSV par feuille")
sheet_choice = st.selectbox("Feuille à exporter", options=list(filtered_sheets.keys()))
csv_bytes = dataframe_to_csv_bytes(filtered_sheets[sheet_choice])
st.download_button(
    f"⬇️ Télécharger {sheet_choice}.csv",
    data=csv_bytes,
    file_name=f"{sheet_choice}_{timestamp}.csv",
    mime="text/csv",
    use_container_width=True,
)
st.dataframe(filtered_sheets[sheet_choice].head(50), use_container_width=True, height=280)

st.divider()

st.markdown("### 🖼️ Export d'un graphique en PNG")
numeric_sheet = st.selectbox("Feuille pour le graphique", options=list(filtered_sheets.keys()), key="png_sheet")
df_chart = filtered_sheets[numeric_sheet]
cat_cols = [c for c in df_chart.columns if df_chart[c].dtype == object]
num_cols = [c for c in df_chart.columns if pd.api.types.is_numeric_dtype(df_chart[c])]

if cat_cols and num_cols and not df_chart.empty:
    cc1, cc2 = st.columns(2)
    x_col = cc1.selectbox("Axe catégoriel", options=cat_cols)
    y_col = cc2.selectbox("Axe numérique", options=num_cols)
    agg = df_chart.groupby(x_col)[y_col].sum().reset_index().sort_values(y_col, ascending=False).head(15)
    fig = px.bar(agg, x=x_col, y=y_col, template=config.PLOTLY_TEMPLATE,
                 color_discrete_sequence=[config.COLOR_PRIMARY])
    st.plotly_chart(fig, use_container_width=True)

    png = figure_to_png_bytes(fig)
    if png:
        st.download_button(
            "⬇️ Télécharger le graphique (PNG)",
            data=png,
            file_name=f"{numeric_sheet}_{x_col}_{y_col}_{timestamp}.png",
            mime="image/png",
            use_container_width=True,
        )
    else:
        st.info(
            "L'export PNG nécessite le moteur `kaleido` (inclus dans requirements.txt). "
            "Si l'erreur persiste, vérifiez son installation : `pip install -U kaleido`."
        )
else:
    st.info("Cette feuille ne contient pas de combinaison catégorie/valeur numérique exploitable pour un graphique rapide.")

st.divider()
st.markdown(
    """
    ℹ️ **Formats disponibles dans cette version (MVP)** : Excel, CSV, PNG.
    Les exports **Word / PDF / Parquet / SVG / HTML** (rapport de mission complet avec
    couverture, sommaire et annexes) sont prévus dans une itération ultérieure — voir
    `docs/roadmap.md`.
    """
)
