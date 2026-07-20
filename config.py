"""
config.py
=========
Configuration centrale du dashboard MEAL/IM INTERSOS Tchad.

Toutes les valeurs "en dur" strictement nécessaires (chemins, palette,
mise en page) sont regroupées ici. Aucune valeur métier (secteurs, régions,
bailleurs, partenaires) n'est codée ici : elles sont toutes dérivées
automatiquement des fichiers de données par utils/data_loader.py, afin que
l'application reste réutilisable pour une autre mission INTERSOS en ne
changeant que les fichiers dans data/.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
EXPORTS_DIR = BASE_DIR / "exports"
LOGS_DIR = BASE_DIR / "logs"

EXCEL_PATH = DATA_DIR / "INTERSOS_Chad_Program_Database.xlsx"
GEOJSON_PATH = DATA_DIR / "chad_admin1.geojson"

for _d in (EXPORTS_DIR, LOGS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Identité de la mission (lue depuis la feuille Cover à l'exécution, ces
# valeurs ne servent que de repli si la feuille Cover est absente)
# ---------------------------------------------------------------------------
APP_TITLE = "INTERSOS Tchad — Dashboard MEAL / IM"
APP_ICON = "🟠"
ORGANIZATION = "INTERSOS"
COUNTRY = "Tchad"
MAIN_CITY = "N'Djamena"

# ---------------------------------------------------------------------------
# Identité visuelle
# INTERSOS utilise un orange vif comme couleur de marque (logo / signature
# institutionnelle). Faute d'accès à la charte graphique officielle exacte,
# une palette professionnelle cohérente avec cette identité a été retenue,
# complétée par une palette catégorielle distincte par secteur pour la
# lisibilité des graphiques (usage courant dans les dashboards humanitaires).
# ---------------------------------------------------------------------------
COLOR_PRIMARY = "#E4610F"      # Orange INTERSOS
COLOR_SECONDARY = "#1B2A4A"    # Bleu nuit institutionnel
COLOR_TERTIARY = "#F2A65A"     # Orange clair / accent
COLOR_BACKGROUND_LIGHT = "#FAFAFA"
COLOR_BACKGROUND_DARK = "#0E1117"
COLOR_SUCCESS = "#2E8B57"
COLOR_WARNING = "#E4B21B"
COLOR_DANGER = "#C0392B"
COLOR_NEUTRAL = "#6B7280"

FONT_FAMILY = "Inter, 'Segoe UI', Arial, sans-serif"

# Palette catégorielle stable, associée aux secteurs (ordre = ordre des
# feuilles Excel). Utilisée pour que chaque secteur garde toujours la même
# couleur sur tous les graphiques et cartes de l'application.
SECTOR_COLOR_SEQUENCE = [
    "#E4610F",  # Protection
    "#1B2A4A",  # Sante
    "#2E8B57",  # Nutrition
    "#2E86AB",  # WASH
    "#E4B21B",  # Securite_Alimentaire
    "#8E44AD",  # Abri_NFI
]

PLOTLY_TEMPLATE = "plotly_white"

# ---------------------------------------------------------------------------
# Feuilles Excel connues (utilisées uniquement pour piloter l'ordre
# d'affichage ; le chargement reste 100% dynamique et s'adapte si une
# feuille est absente ou si de nouvelles feuilles sont ajoutées)
# ---------------------------------------------------------------------------
SHEET_COVER = "Cover"
SHEET_BENEFICIARIES = "Beneficiary_Registration"
SHEET_INDICATORS = "Indicator_Tracker"
SECTOR_SHEETS_ORDER = [
    "Protection",
    "Sante",
    "Nutrition",
    "WASH",
    "Securite_Alimentaire",
    "Abri_NFI",
]

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
CACHE_TTL_SECONDS = 3600
