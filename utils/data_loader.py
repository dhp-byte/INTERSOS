"""
utils/data_loader.py
=====================
Chargement et profilage des données de référence (Excel + GeoJSON).

Principe directeur : aucune valeur métier (nom de secteur, région,
bailleur, partenaire...) n'est codée en dur. Tout est déduit dynamiquement
du contenu réel des fichiers, afin que l'application reste pilotée par les
données et réutilisable pour une autre mission INTERSOS.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from config import CACHE_TTL_SECONDS, EXCEL_PATH, GEOJSON_PATH, SHEET_BENEFICIARIES, SHEET_COVER, SHEET_INDICATORS

logger = logging.getLogger("intersos_dashboard")


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def list_sheets(excel_path: str | Path = EXCEL_PATH) -> list[str]:
    """Retourne la liste des feuilles du classeur Excel.

    Args:
        excel_path: Chemin vers le fichier Excel.

    Returns:
        Liste ordonnée des noms de feuilles.

    Example:
        >>> list_sheets()
        ['Cover', 'Beneficiary_Registration', 'Protection', ...]
    """
    try:
        return pd.ExcelFile(excel_path).sheet_names
    except FileNotFoundError:
        logger.error("Fichier Excel introuvable : %s", excel_path)
        return []
    except Exception as exc:  # pragma: no cover - robustesse générale
        logger.error("Erreur de lecture du classeur Excel : %s", exc)
        return []


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def load_all_sheets(excel_path: str | Path = EXCEL_PATH) -> dict[str, pd.DataFrame]:
    """Charge toutes les feuilles du classeur Excel en DataFrames.

    Les colonnes contenant "Date" dans leur nom sont automatiquement
    converties en datetime lorsque cela est possible.

    Args:
        excel_path: Chemin vers le fichier Excel.

    Returns:
        Dictionnaire {nom_de_feuille: DataFrame}.
    """
    sheets: dict[str, pd.DataFrame] = {}
    try:
        xls = pd.ExcelFile(excel_path)
    except FileNotFoundError:
        st.error(f"⚠️ Fichier de données introuvable : `{excel_path}`.")
        return sheets
    except Exception as exc:
        st.error(f"⚠️ Impossible de lire le classeur Excel : {exc}")
        return sheets

    for name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=name)
            for col in df.columns:
                if "date" in col.lower():
                    df[col] = pd.to_datetime(df[col], errors="coerce")
            sheets[name] = df
        except Exception as exc:  # pragma: no cover
            logger.error("Erreur au chargement de la feuille '%s' : %s", name, exc)
            st.warning(f"La feuille '{name}' n'a pas pu être chargée ({exc}).")
    return sheets


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def load_geojson(geojson_path: str | Path = GEOJSON_PATH) -> dict[str, Any] | None:
    """Charge le fichier GeoJSON des régions administratives.

    Args:
        geojson_path: Chemin vers le fichier GeoJSON.

    Returns:
        Dictionnaire GeoJSON (FeatureCollection) ou None si indisponible.
    """
    try:
        with open(geojson_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"⚠️ Fichier géographique introuvable : `{geojson_path}`.")
        return None
    except json.JSONDecodeError as exc:
        st.error(f"⚠️ GeoJSON invalide : {exc}")
        return None


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_region_centroids(geojson_path: str | Path = GEOJSON_PATH) -> dict[str, dict[str, float]]:
    """Calcule le centroïde (moyenne simple des sommets) de chaque région.

    Utilisé pour positionner les marqueurs Folium au centre de chaque
    province sans dépendance supplémentaire (pas de GeoPandas requis).

    Args:
        geojson_path: Chemin vers le fichier GeoJSON.

    Returns:
        Dictionnaire {nom_region: {"lat": float, "lon": float, "population_2023": int}}.
    """
    gj = load_geojson(geojson_path)
    centroids: dict[str, dict[str, float]] = {}
    if not gj:
        return centroids

    for feature in gj.get("features", []):
        props = feature.get("properties", {})
        name = props.get("name") or props.get("name_fr")
        geom = feature.get("geometry", {})
        coords = geom.get("coordinates", [])
        pts: list[tuple[float, float]] = []

        def _flatten(c: Any) -> None:
            if isinstance(c[0], (int, float)):
                pts.append((c[0], c[1]))
            else:
                for sub in c:
                    _flatten(sub)

        try:
            _flatten(coords)
        except (IndexError, TypeError):
            continue

        if not pts or not name:
            continue

        lon_avg = sum(p[0] for p in pts) / len(pts)
        lat_avg = sum(p[1] for p in pts) / len(pts)
        centroids[name] = {
            "lat": lat_avg,
            "lon": lon_avg,
            "population_2023": props.get("population_2023"),
            "admin_level": props.get("admin_level"),
        }
    return centroids


def get_cover_info(sheets: dict[str, pd.DataFrame]) -> dict[str, str]:
    """Extrait les métadonnées de mission depuis la feuille Cover.

    Args:
        sheets: Dictionnaire des feuilles chargées.

    Returns:
        Dictionnaire {champ: valeur}. Vide si la feuille Cover est absente.
    """
    if SHEET_COVER not in sheets:
        return {}
    df = sheets[SHEET_COVER]
    if not {"Champ", "Valeur"}.issubset(df.columns):
        return {}
    return dict(zip(df["Champ"], df["Valeur"].astype(str)))


def get_sector_sheets(sheets: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Retourne uniquement les feuilles d'activités sectorielles.

    Une feuille est considérée "sectorielle" si elle n'est ni Cover, ni
    Beneficiary_Registration, ni Indicator_Tracker — ce qui permet à de
    nouvelles feuilles sectorielles d'être détectées automatiquement.

    Args:
        sheets: Dictionnaire de toutes les feuilles chargées.

    Returns:
        Sous-dictionnaire des feuilles sectorielles.
    """
    excluded = {SHEET_COVER, SHEET_BENEFICIARIES, SHEET_INDICATORS}
    return {name: df for name, df in sheets.items() if name not in excluded}


def get_reference_values(sheets: dict[str, pd.DataFrame], column: str) -> list[str]:
    """Agrège les valeurs uniques d'une colonne à travers toutes les feuilles.

    Permet de construire dynamiquement les listes de filtres (Province,
    Donor, Partner, Displacement_Status...) sans jamais les coder en dur.

    Args:
        sheets: Dictionnaire des feuilles chargées.
        column: Nom de la colonne à agréger (ex. "Province", "Donor").

    Returns:
        Liste triée des valeurs uniques rencontrées.
    """
    values: set[str] = set()
    for df in sheets.values():
        if column in df.columns:
            values.update(df[column].dropna().astype(str).unique().tolist())
    return sorted(values)


def profile_sheet(df: pd.DataFrame) -> dict[str, Any]:
    """Produit un profil statistique complet d'une feuille (ÉTAPE 0/3).

    Args:
        df: DataFrame à profiler.

    Returns:
        Dictionnaire structuré : dimensions, types, valeurs manquantes,
        doublons, et statistiques par colonne (numérique / catégorielle /
        date).
    """
    profile: dict[str, Any] = {
        "n_rows": len(df),
        "n_cols": df.shape[1],
        "memory_kb": round(df.memory_usage(deep=True).sum() / 1024, 1),
        "duplicates": int(df.duplicated().sum()),
        "columns": {},
    }

    for col in df.columns:
        series = df[col]
        col_info: dict[str, Any] = {
            "dtype": str(series.dtype),
            "missing": int(series.isna().sum()),
            "missing_pct": round(100 * series.isna().mean(), 1),
            "n_unique": int(series.nunique(dropna=True)),
        }

        if pd.api.types.is_datetime64_any_dtype(series):
            valid = series.dropna()
            col_info.update(
                {
                    "kind": "date",
                    "min": str(valid.min().date()) if not valid.empty else None,
                    "max": str(valid.max().date()) if not valid.empty else None,
                }
            )
        elif pd.api.types.is_numeric_dtype(series):
            desc = series.describe()
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            outliers = int(((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum())
            col_info.update(
                {
                    "kind": "numeric",
                    "mean": round(float(desc.get("mean", 0)), 2),
                    "median": round(float(series.median()), 2),
                    "std": round(float(desc.get("std", 0)), 2),
                    "min": float(desc.get("min", 0)),
                    "max": float(desc.get("max", 0)),
                    "outliers_iqr": outliers,
                }
            )
        else:
            top = series.value_counts(dropna=True).head(5)
            col_info.update(
                {
                    "kind": "categorical",
                    "top_values": {str(k): int(v) for k, v in top.items()},
                }
            )
        profile["columns"][col] = col_info

    return profile
