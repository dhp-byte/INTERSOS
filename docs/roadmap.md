# Feuille de route — extensions possibles

Ce document liste les éléments du cahier des charges d'origine qui ne sont
**pas** inclus dans le MVP livré, avec une estimation de la manière de les
aborder. Chacun peut être ajouté indépendamment, sans modifier l'architecture
existante (`utils/`, `pages/`, `config.py`).

## Rapports automatisés (Word / PDF)
- S'appuyer sur `python-docx` et `reportlab` (ou `fpdf2`).
- Réutiliser les DataFrames déjà filtrés par `utils/filters.py` et les
  figures Plotly déjà construites dans chaque page (export via
  `utils/export.figure_to_png_bytes`, puis insertion dans le document).
- Structure suggérée : `utils/report_word.py`, `utils/report_pdf.py`,
  déclenchés depuis une nouvelle section de `pages/6_📤_Exports.py`.

## Connecteur KoBoToolbox actif
- La structure existe déjà (`utils/kobo.py`, `KoboClient`).
- Reste à faire : renseigner `secrets.toml`, ajouter une page
  `pages/8_🔄_Synchronisation_KoBo.py` qui appelle
  `get_configured_client()` et fusionne les nouvelles soumissions dans les
  DataFrames existants (avec détection de doublons sur l'ID).

## Authentification (login / permissions)
- `streamlit-authenticator` est une option légère compatible avec la
  structure actuelle (pas de base de données requise).
- Prévoir des rôles simples : Admin / Lecture seule, en cohérence avec la
  liste des profils cités dans le cahier des charges (Head of Mission,
  MEAL Manager, etc.).

## Docker
- Un `Dockerfile` minimal type `python:3.12-slim` + `pip install -r
  requirements.txt` + `CMD ["streamlit", "run", "app.py"]` suffit ; aucune
  adaptation du code n'est nécessaire, l'app est déjà sans état persistant
  côté serveur.

## Dark mode
- `st.theme` / bascule dans `.streamlit/config.toml` gérée par un sélecteur
  dans la sidebar ; nécessite de dupliquer la palette de `config.py` pour un
  jeu de couleurs sombres.

## Exports additionnels (Parquet, SVG, HTML)
- Extensions directes de `utils/export.py` (`df.to_parquet`,
  `fig.to_html`, `fig.to_image(format="svg")`), même schéma que les
  fonctions existantes.

## Tests étendus
- Les tests actuels couvrent `data_loader` et `kpi`. Une extension
  naturelle ajouterait `tests/test_filters.py` et des tests d'intégration
  Streamlit avec `streamlit.testing.v1.AppTest`.
