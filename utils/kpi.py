"""
utils/kpi.py
=============
Calcul des indicateurs clés (KPI) à partir des données filtrées.

Chaque fonction est pure (n'accède pas à st.session_state directement) afin
de rester testable indépendamment de Streamlit.
"""

from __future__ import annotations

import pandas as pd


def safe_sum(df: pd.DataFrame, column: str) -> float:
    """Somme une colonne si elle existe, sinon retourne 0.

    Args:
        df: DataFrame source.
        column: Nom de colonne à sommer.

    Returns:
        Somme des valeurs, ou 0.0 si la colonne est absente ou le
        DataFrame est vide.
    """
    if df.empty or column not in df.columns:
        return 0.0
    return float(df[column].sum())


def coverage_rate(df: pd.DataFrame, reached_col: str, target_col: str) -> float:
    """Calcule un taux de couverture (Reached / Target) en pourcentage.

    Args:
        df: DataFrame source.
        reached_col: Colonne des valeurs atteintes.
        target_col: Colonne des valeurs cibles.

    Returns:
        Taux de couverture en pourcentage (0-100+), ou 0.0 si non calculable.
    """
    target = safe_sum(df, target_col)
    if target == 0:
        return 0.0
    return round(100 * safe_sum(df, reached_col) / target, 1)


def beneficiary_kpis(df_beneficiaries: pd.DataFrame) -> dict[str, float | int]:
    """Calcule les KPI globaux relatifs aux bénéficiaires enregistrés.

    Args:
        df_beneficiaries: Feuille Beneficiary_Registration (filtrée).

    Returns:
        Dictionnaire de KPI : total, ménages, femmes, enfants, taille
        moyenne du ménage, part des cas complets.
    """
    if df_beneficiaries.empty:
        return {
            "total_beneficiaries": 0,
            "total_households": 0,
            "pct_female": 0.0,
            "pct_children": 0.0,
            "avg_household_size": 0.0,
            "pct_complete_registration": 0.0,
        }

    df = df_beneficiaries
    total = len(df)
    n_households = df["Household_ID"].nunique() if "Household_ID" in df.columns else 0
    pct_female = round(100 * (df["Sex"] == "F").mean(), 1) if "Sex" in df.columns else 0.0
    pct_children = round(100 * (df["Age"] < 18).mean(), 1) if "Age" in df.columns else 0.0
    avg_hh_size = round(df["Household_Size"].mean(), 1) if "Household_Size" in df.columns else 0.0
    pct_complete = (
        round(100 * (df["Registration_Status"] == "Complete").mean(), 1)
        if "Registration_Status" in df.columns
        else 0.0
    )

    return {
        "total_beneficiaries": total,
        "total_households": n_households,
        "pct_female": pct_female,
        "pct_children": pct_children,
        "avg_household_size": avg_hh_size,
        "pct_complete_registration": pct_complete,
    }


def sector_activity_kpis(df: pd.DataFrame) -> dict[str, float | int]:
    """Calcule les KPI génériques d'une feuille d'activité sectorielle.

    Détecte automatiquement les colonnes Target_*/Reached_* présentes,
    quel que soit le secteur (Protection, Santé, Nutrition, WASH...).

    Args:
        df: Feuille d'activité sectorielle (filtrée).

    Returns:
        Dictionnaire : nombre d'activités, total atteint, total cible,
        taux de couverture global, répartition par statut.
    """
    if df.empty:
        return {"n_activities": 0, "total_reached": 0, "total_target": 0, "coverage_rate": 0.0}

    reached_cols = [c for c in df.columns if c.lower().startswith("reached") and pd.api.types.is_numeric_dtype(df[c])]
    target_cols = [c for c in df.columns if c.lower().startswith("target") and pd.api.types.is_numeric_dtype(df[c])]

    # On privilégie la colonne "globale" (ex. Reached, Reached_Beneficiaries,
    # Reached_Consultations) plutôt que les sous-catégories (Reached_Male...)
    main_reached = next((c for c in reached_cols if "male" not in c.lower() and "female" not in c.lower()
                          and "children" not in c.lower() and "adult" not in c.lower()
                          and "under5" not in c.lower() and "over5" not in c.lower()
                          and "pregnant" not in c.lower()), reached_cols[0] if reached_cols else None)
    main_target = next((c for c in target_cols), None)

    total_reached = safe_sum(df, main_reached) if main_reached else 0.0
    total_target = safe_sum(df, main_target) if main_target else 0.0
    cov = round(100 * total_reached / total_target, 1) if total_target else 0.0

    return {
        "n_activities": len(df),
        "total_reached": int(total_reached),
        "total_target": int(total_target),
        "coverage_rate": cov,
    }


def indicator_summary(df_indicators: pd.DataFrame) -> dict[str, float | int]:
    """Résume l'état d'avancement global des indicateurs de suivi.

    Args:
        df_indicators: Feuille Indicator_Tracker (filtrée).

    Returns:
        Dictionnaire : nombre d'indicateurs, taux d'atteinte moyen,
        nombre en bonne voie / en retard.
    """
    if df_indicators.empty or "Achievement_%" not in df_indicators.columns:
        return {"n_indicators": 0, "avg_achievement": 0.0, "on_track": 0, "off_track": 0}

    avg = round(df_indicators["Achievement_%"].mean(), 1)
    on_track = int((df_indicators["Achievement_%"] >= 90).sum())
    off_track = int((df_indicators["Achievement_%"] < 90).sum())

    return {
        "n_indicators": len(df_indicators),
        "avg_achievement": avg,
        "on_track": on_track,
        "off_track": off_track,
    }
