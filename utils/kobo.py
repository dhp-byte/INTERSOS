"""
utils/kobo.py
==============
Module de connexion à KoBoToolbox — STRUCTURE UNIQUEMENT.

Ce module ne contient aucune clé API réelle et n'effectue aucun appel
réseau tant que les identifiants n'ont pas été renseignés dans
`.streamlit/secrets.toml` (voir secrets.toml.example). Il est fourni pour
que l'équipe IM puisse brancher une synchronisation KoBo ultérieurement
sans modifier la structure de l'application.

Utilisation prévue une fois les identifiants disponibles :

    from utils.kobo import KoboClient
    client = KoboClient(base_url=..., api_token=...)
    df = client.fetch_submissions(form_uid="a1b2c3")
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import requests
import streamlit as st


@dataclass
class KoboClient:
    """Client minimal pour l'API KoBoToolbox (v2).

    Attributes:
        base_url: URL de base de l'instance KoBo (ex. https://kf.kobotoolbox.org).
        api_token: Jeton d'API personnel KoBo.
    """

    base_url: str
    api_token: str

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Token {self.api_token}"}

    def is_configured(self) -> bool:
        """Indique si des identifiants non vides ont été fournis."""
        return bool(self.base_url) and bool(self.api_token)

    def list_forms(self) -> list[dict]:
        """Liste les formulaires (assets) disponibles sur le compte KoBo.

        Returns:
            Liste de dictionnaires décrivant chaque formulaire. Liste vide
            si le client n'est pas configuré ou en cas d'erreur réseau.
        """
        if not self.is_configured():
            return []
        try:
            resp = requests.get(f"{self.base_url}/api/v2/assets.json", headers=self._headers(), timeout=15)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except requests.RequestException as exc:
            st.warning(f"Connexion KoBo indisponible : {exc}")
            return []

    def fetch_submissions(self, form_uid: str) -> pd.DataFrame:
        """Récupère les soumissions d'un formulaire KoBo sous forme de DataFrame.

        Args:
            form_uid: Identifiant unique du formulaire (asset uid).

        Returns:
            DataFrame des soumissions, vide si le client n'est pas
            configuré ou en cas d'erreur.
        """
        if not self.is_configured():
            return pd.DataFrame()
        try:
            resp = requests.get(
                f"{self.base_url}/api/v2/assets/{form_uid}/data.json",
                headers=self._headers(),
                timeout=30,
            )
            resp.raise_for_status()
            return pd.DataFrame(resp.json().get("results", []))
        except requests.RequestException as exc:
            st.warning(f"Échec de synchronisation KoBo : {exc}")
            return pd.DataFrame()


def get_configured_client() -> KoboClient | None:
    """Construit un KoboClient à partir de st.secrets, si disponible.

    Returns:
        Instance de KoboClient si `kobo_base_url` et `kobo_api_token` sont
        présents dans les secrets Streamlit, sinon None.
    """
    try:
        base_url = st.secrets.get("kobo_base_url", "")
        api_token = st.secrets.get("kobo_api_token", "")
    except Exception:
        return None
    if not base_url or not api_token:
        return None
    return KoboClient(base_url=base_url, api_token=api_token)
