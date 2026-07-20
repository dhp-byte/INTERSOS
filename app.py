"""
app.py
======
Point d'entrée de l'application — Page "Vue d'ensemble".

Dashboard MEAL / Information Management pour la mission INTERSOS Tchad.
Pilotage 100% par les données : INTERSOS_Chad_Program_Database.xlsx et
chad_admin1.geojson (voir data/).
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import config
from utils.data_loader import get_cover_info, get_sector_sheets, load_all_sheets
from utils.filters import apply_filters, render_sidebar_filters
from utils.kpi import beneficiary_kpis, indicator_summary, sector_activity_kpis

st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css() -> None:
    """Injecte la feuille de style personnalisée dans la page."""
    try:
        with open(config.ASSETS_DIR / "style.css", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def render_header(cover: dict[str, str]) -> None:
    """Affiche le bandeau d'en-tête avec les informations de mission."""
    mission = cover.get("Mission", "Mission humanitaire au Tchad")
    period = cover.get("Période de couverture", "")
    st.markdown(
        f"""
        <div class="intersos-banner">
            <h1>🟠 {config.ORGANIZATION} — Tchad</h1>
            <p>{mission}</p>
            <p>📍 Base : {config.MAIN_CITY} &nbsp;|&nbsp; 🗓️ Période : {period}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Assemble la page Vue d'ensemble."""
    load_css()

    try:
        sheets = load_all_sheets()
    except Exception as exc:
        st.error(f"Erreur critique au chargement des données : {exc}")
        st.stop()

    if not sheets:
        st.error("Aucune donnée n'a pu être chargée. Vérifiez le fichier dans `data/`.")
        st.stop()

    cover = get_cover_info(sheets)
    render_header(cover)

    selections = render_sidebar_filters(sheets)

    beneficiaries = apply_filters(sheets.get(config.SHEET_BENEFICIARIES, pd.DataFrame()), selections)
    indicators = apply_filters(sheets.get(config.SHEET_INDICATORS, pd.DataFrame()), selections)
    sector_sheets = {name: apply_filters(df, selections) for name, df in get_sector_sheets(sheets).items()}

    # --- KPI globaux ---------------------------------------------------
    bkpi = beneficiary_kpis(beneficiaries)
    ikpi = indicator_summary(indicators)
    total_reached = sum(sector_activity_kpis(df)["total_reached"] for df in sector_sheets.values())
    total_activities = sum(len(df) for df in sector_sheets.values())

    st.markdown("### 📊 Indicateurs clés de la mission")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Bénéficiaires enregistrés", f"{bkpi['total_beneficiaries']:,}".replace(",", " "))
    c2.metric("Ménages", f"{bkpi['total_households']:,}".replace(",", " "))
    c3.metric("Activités menées", f"{total_activities:,}".replace(",", " "))
    c4.metric("Personnes atteintes (activités)", f"{total_reached:,}".replace(",", " "))
    c5.metric("Taux d'atteinte moyen (indicateurs)", f"{ikpi['avg_achievement']:.1f} %" if ikpi["n_indicators"] else "N/A")

    c6, c7, c8, c9 = st.columns(4)
    c6.metric("% Femmes", f"{bkpi['pct_female']:.1f} %")
    c7.metric("% Enfants (<18 ans)", f"{bkpi['pct_children']:.1f} %")
    c8.metric("Taille moyenne du ménage", f"{bkpi['avg_household_size']:.1f}")
    c9.metric("Indicateurs en bonne voie", f"{ikpi['on_track']} / {ikpi['n_indicators']}" if ikpi["n_indicators"] else "N/A")

    st.divider()

    # --- Répartition sectorielle -----------------------------------------
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("#### Activités et bénéficiaires atteints par secteur")
        rows = []
        for name, df in sector_sheets.items():
            k = sector_activity_kpis(df)
            rows.append({"Secteur": name, "Activités": k["n_activities"], "Atteints": k["total_reached"]})
        sector_df = pd.DataFrame(rows)
        if not sector_df.empty and sector_df["Activités"].sum() > 0:
            fig = px.bar(
                sector_df.sort_values("Atteints", ascending=True),
                x="Atteints",
                y="Secteur",
                orientation="h",
                text="Atteints",
                color="Secteur",
                color_discrete_sequence=config.SECTOR_COLOR_SEQUENCE,
                template=config.PLOTLY_TEMPLATE,
            )
            fig.update_layout(showlegend=False, height=380, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune activité ne correspond aux filtres sélectionnés.")

    with col_right:
        st.markdown("#### Bénéficiaires par statut de déplacement")
        if not beneficiaries.empty and "Displacement_Status" in beneficiaries.columns:
            disp_counts = beneficiaries["Displacement_Status"].value_counts().reset_index()
            disp_counts.columns = ["Statut", "Nombre"]
            fig2 = px.pie(
                disp_counts,
                names="Statut",
                values="Nombre",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Set2,
                template=config.PLOTLY_TEMPLATE,
            )
            fig2.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Aucun bénéficiaire ne correspond aux filtres sélectionnés.")

    st.divider()

    # --- Tendance temporelle des enregistrements -------------------------
    st.markdown("#### Évolution des enregistrements de bénéficiaires")
    if not beneficiaries.empty and "Date_Registration" in beneficiaries.columns:
        trend = (
            beneficiaries.dropna(subset=["Date_Registration"])
            .assign(Mois=lambda d: d["Date_Registration"].dt.to_period("M").astype(str))
            .groupby("Mois")
            .size()
            .reset_index(name="Enregistrements")
        )
        fig3 = px.area(
            trend,
            x="Mois",
            y="Enregistrements",
            markers=True,
            template=config.PLOTLY_TEMPLATE,
            color_discrete_sequence=[config.COLOR_PRIMARY],
        )
        fig3.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Pas de données temporelles disponibles pour les filtres actuels.")

    st.divider()

    # --- Top 10 provinces --------------------------------------------------
    st.markdown("#### Top provinces par nombre de bénéficiaires")
    if not beneficiaries.empty and "Province" in beneficiaries.columns:
        top_prov = beneficiaries["Province"].value_counts().head(10).reset_index()
        top_prov.columns = ["Province", "Bénéficiaires"]
        fig4 = px.bar(
            top_prov,
            x="Province",
            y="Bénéficiaires",
            text="Bénéficiaires",
            color_discrete_sequence=[config.COLOR_SECONDARY],
            template=config.PLOTLY_TEMPLATE,
        )
        fig4.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig4, use_container_width=True)

    st.caption(
        "Naviguez via le menu latéral pour explorer les Bénéficiaires, l'Analyse sectorielle, "
        "les Indicateurs, la Cartographie, les Bailleurs/Partenaires et les Exports."
    )


if __name__ == "__main__":
    main()
