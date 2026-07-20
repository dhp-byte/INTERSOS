"""
utils/export.py
=================
Fonctions d'export des données et graphiques.

Portée MVP : Excel (.xlsx), CSV, et images PNG des graphiques Plotly.
Les exports Word/PDF/Parquet/SVG/HTML avancés (rapport complet multi-pages)
sont hors périmètre de cette itération et pourront être ajoutés en
s'appuyant sur les mêmes DataFrames filtrés (voir README, section
"Prochaines itérations").
"""

from __future__ import annotations

import io

import pandas as pd
import plotly.graph_objects as go


def dataframe_to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    """Convertit un ensemble de DataFrames en un classeur Excel en mémoire.

    Args:
        sheets: Dictionnaire {nom_feuille: DataFrame} à exporter.

    Returns:
        Contenu binaire du fichier .xlsx, prêt pour st.download_button.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe_name = name[:31] if name else "Feuille"
            df.to_excel(writer, sheet_name=safe_name, index=False)
    return buffer.getvalue()


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convertit un DataFrame en CSV (UTF-8 avec BOM pour compatibilité Excel).

    Args:
        df: DataFrame à exporter.

    Returns:
        Contenu binaire du fichier .csv.
    """
    return df.to_csv(index=False).encode("utf-8-sig")


def figure_to_png_bytes(fig: go.Figure, width: int = 1200, height: int = 700, scale: int = 2) -> bytes | None:
    """Exporte une figure Plotly en image PNG.

    Nécessite le paquet `kaleido`. En cas d'échec (moteur non disponible),
    retourne None plutôt que de lever une exception, pour ne jamais casser
    l'affichage du dashboard.

    Args:
        fig: Figure Plotly à exporter.
        width: Largeur de l'image en pixels.
        height: Hauteur de l'image en pixels.
        scale: Facteur d'échelle (résolution).

    Returns:
        Contenu binaire PNG, ou None si l'export a échoué.
    """
    try:
        return fig.to_image(format="png", width=width, height=height, scale=scale)
    except Exception:
        return None
