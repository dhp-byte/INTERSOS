"""
utils/filters.py
=================
Filtres globaux réutilisables sur toutes les pages du dashboard.

Les filtres sont construits dynamiquement à partir des valeurs réellement
présentes dans les données (aucune liste codée en dur) et stockés dans
``st.session_state`` afin de rester cohérents lors de la navigation entre
pages.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from utils.data_loader import get_reference_values

FILTERABLE_COLUMNS = [
    ("Province", "Province"),
    ("Department", "Département"),
    ("Sector", "Secteur (bénéficiaires)"),
    ("Donor", "Bailleur"),
    ("Partner", "Partenaire"),
    ("Sex", "Sexe"),
    ("Displacement_Status", "Statut de déplacement"),
    ("Status", "Statut d'activité"),
]


def render_sidebar_filters(sheets: dict[str, pd.DataFrame]) -> dict[str, list[str]]:
    """Affiche les filtres globaux dans la barre latérale.

    Args:
        sheets: Dictionnaire de toutes les feuilles chargées, utilisé pour
            déterminer dynamiquement les modalités disponibles.

    Returns:
        Dictionnaire {nom_colonne: valeurs_sélectionnées} à appliquer via
        :func:`apply_filters`. Une liste vide signifie "toutes les valeurs".
    """
    st.sidebar.markdown("### 🔎 Filtres globaux")
    selections: dict[str, list[str]] = {}

    for column, label in FILTERABLE_COLUMNS:
        options = get_reference_values(sheets, column)
        if not options:
            continue
        key = f"filter_{column}"
        selections[column] = st.sidebar.multiselect(label, options=options, default=[], key=key)

    # Filtre de période, basé sur toutes les colonnes de date détectées
    all_dates: list[pd.Timestamp] = []
    for df in sheets.values():
        for col in df.columns:
            if "date" in col.lower() and pd.api.types.is_datetime64_any_dtype(df[col]):
                all_dates.extend(df[col].dropna().tolist())

    if all_dates:
        min_d, max_d = min(all_dates).date(), max(all_dates).date()
        st.sidebar.markdown("### 📅 Période")
        period = st.sidebar.date_input(
            "Intervalle",
            value=(min_d, max_d),
            min_value=min_d,
            max_value=max_d,
            key="filter_period",
        )
        if isinstance(period, tuple) and len(period) == 2:
            selections["__period__"] = list(period)  # type: ignore[assignment]

    if st.sidebar.button("↺ Réinitialiser les filtres", use_container_width=True):
        for column, _ in FILTERABLE_COLUMNS:
            st.session_state.pop(f"filter_{column}", None)
        st.session_state.pop("filter_period", None)
        st.rerun()

    return selections


def apply_filters(df: pd.DataFrame, selections: dict[str, list[str]]) -> pd.DataFrame:
    """Applique les filtres globaux à un DataFrame, colonne par colonne.

    Les filtres portant sur une colonne absente du DataFrame sont ignorés
    silencieusement, ce qui permet d'utiliser le même jeu de filtres sur des
    feuilles ayant des schémas différents (ex. WASH n'a pas de colonne
    "Sex" directe mais Reached_Male/Reached_Female).

    Args:
        df: DataFrame à filtrer.
        selections: Sorties de :func:`render_sidebar_filters`.

    Returns:
        DataFrame filtré (copie).
    """
    if df.empty:
        return df

    filtered = df
    for column, values in selections.items():
        if column == "__period__":
            continue
        if values and column in filtered.columns:
            filtered = filtered[filtered[column].astype(str).isin(values)]

    period = selections.get("__period__")
    if period and len(period) == 2:
        start, end = period
        date_cols = [c for c in filtered.columns if "date" in c.lower() and pd.api.types.is_datetime64_any_dtype(filtered[c])]
        if date_cols:
            ref_col = date_cols[0]
            mask = filtered[ref_col].dt.date.between(start, end) | filtered[ref_col].isna()
            filtered = filtered[mask]

    return filtered
