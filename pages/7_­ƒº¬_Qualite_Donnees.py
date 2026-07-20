"""Page Qualité des données — profilage automatique de chaque feuille Excel."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.data_loader import load_all_sheets, profile_sheet

st.set_page_config(page_title="Qualité des données — INTERSOS Tchad", page_icon="🧪", layout="wide")

st.title("🧪 Qualité et profilage des données")
st.caption(
    "Profilage automatique généré à partir du contenu réel du classeur — "
    "aucune valeur n'est codée en dur."
)

sheets = load_all_sheets()

st.markdown("### Inventaire des feuilles")
inventory = []
for name, df in sheets.items():
    p = profile_sheet(df)
    inventory.append({
        "Feuille": name,
        "Lignes": p["n_rows"],
        "Colonnes": p["n_cols"],
        "Mémoire (Ko)": p["memory_kb"],
        "Doublons": p["duplicates"],
    })
st.dataframe(pd.DataFrame(inventory), use_container_width=True)

st.divider()

sheet_choice = st.selectbox("Détail par feuille", options=list(sheets.keys()))
profile = profile_sheet(sheets[sheet_choice])

st.markdown(f"### Détail — `{sheet_choice}`")
c1, c2, c3 = st.columns(3)
c1.metric("Lignes", profile["n_rows"])
c2.metric("Colonnes", profile["n_cols"])
c3.metric("Doublons", profile["duplicates"])

rows = []
for col, info in profile["columns"].items():
    row = {
        "Colonne": col,
        "Type": info["kind"],
        "Dtype": info["dtype"],
        "Valeurs manquantes (%)": info["missing_pct"],
        "Valeurs uniques": info["n_unique"],
    }
    if info["kind"] == "numeric":
        row.update({
            "Moyenne": info["mean"], "Médiane": info["median"], "Écart-type": info["std"],
            "Min": info["min"], "Max": info["max"], "Aberrantes (IQR)": info["outliers_iqr"],
        })
    elif info["kind"] == "date":
        row.update({"Première date": info["min"], "Dernière date": info["max"]})
    rows.append(row)

st.dataframe(pd.DataFrame(rows), use_container_width=True, height=420)

st.caption(
    "Taux de valeurs manquantes de 100% attendu pour la colonne `Notes` sur les feuilles "
    "d'activité (colonne libre, non renseignée dans ce jeu de données) — signalé, non corrigé, "
    "conformément à la règle de non-modification des données de référence."
)
