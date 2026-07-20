# INTERSOS Tchad — Dashboard MEAL / Information Management

Plateforme Streamlit d'analyse programmatique, cartographique et de suivi des
indicateurs pour la mission INTERSOS au Tchad. Entièrement pilotée par les
données : `data/INTERSOS_Chad_Program_Database.xlsx` et
`data/chad_admin1.geojson`.

> **Version 1.0 — MVP.** Ce livrable couvre l'analyse, la visualisation, la
> cartographie et les exports Excel/CSV/PNG. Le périmètre étendu du cahier
> des charges d'origine (rapports Word/PDF, connecteur KoBo actif,
> authentification, Docker, dark mode) est documenté dans
> [`docs/roadmap.md`](docs/roadmap.md) et peut être ajouté par itération.

---

## 1. Installation

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

Compatible Python 3.12+, Windows / Linux / macOS.

## 2. Lancement

```bash
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`.

## 3. Structure du projet

```text
INTERSOS_MEAL_Dashboard/
├── app.py                      # Page d'accueil (Vue d'ensemble)
├── config.py                   # Chemins, couleurs, constantes de mise en page
├── requirements.txt
├── README.md
├── .streamlit/
│   ├── config.toml             # Thème (couleurs INTERSOS)
│   └── secrets.toml.example    # Modèle pour les identifiants KoBo
├── data/
│   ├── INTERSOS_Chad_Program_Database.xlsx   # Donnée de référence (non modifiée)
│   └── chad_admin1.geojson                   # Donnée de référence (non modifiée)
├── utils/
│   ├── data_loader.py          # Chargement + profilage Excel/GeoJSON
│   ├── filters.py               # Filtres globaux dynamiques
│   ├── kpi.py                   # Calcul des indicateurs clés
│   ├── export.py                # Export Excel/CSV/PNG
│   └── kobo.py                  # Connecteur KoBo (structure, inactif sans clé)
├── pages/
│   ├── 1_👥_Beneficiaires.py
│   ├── 2_🎯_Activites_Sectorielles.py
│   ├── 3_📈_Indicateurs.py
│   ├── 4_🗺️_Cartographie.py
│   ├── 5_💰_Bailleurs_Partenaires.py
│   ├── 6_📤_Exports.py
│   └── 7_🧪_Qualite_Donnees.py
├── assets/style.css
├── tests/                       # pytest
├── exports/                     # Fichiers générés par l'utilisateur (vide au départ)
└── logs/
```

## 4. Pages

| Page | Contenu |
|---|---|
| **Vue d'ensemble** | KPI globaux, répartition sectorielle, tendance temporelle, top provinces |
| **Bénéficiaires** | Pyramide des âges, vulnérabilité, statut de déplacement par province |
| **Activités sectorielles** | Analyse générique par secteur (détecte automatiquement les feuilles) |
| **Indicateurs** | Suivi Indicator_Tracker, taux d'atteinte, progression trimestrielle |
| **Cartographie** | Choroplèthe, marqueurs groupés, carte de chaleur (Folium) |
| **Bailleurs & Partenaires** | Répartition, matrice croisée, diagramme de Sankey des financements |
| **Exports** | Excel complet filtré, CSV par feuille, PNG de graphique |
| **Qualité des données** | Profilage automatique (ÉTAPE 0) : types, valeurs manquantes, aberrantes |

Tous les filtres (Province, Secteur, Bailleur, Partenaire, Sexe, Statut de
déplacement, Statut d'activité, Période) sont dans la barre latérale et
s'appliquent à toutes les pages.

## 5. Principes de conception

- **Aucune valeur métier codée en dur** : secteurs, régions, bailleurs,
  partenaires sont déduits dynamiquement du contenu des fichiers
  (`utils.data_loader.get_reference_values`).
- **Le code s'adapte aux données**, jamais l'inverse : les noms de feuilles,
  colonnes et types du fichier Excel ne sont jamais modifiés.
- **Cache** : `@st.cache_data` sur tous les chargements (Excel, GeoJSON,
  centroïdes) pour la performance.
- **Robustesse** : chaque accès fichier est encadré par `try/except` avec
  message explicite ; une feuille ou colonne manquante ne fait jamais
  planter l'application (dégradation silencieuse + message d'information).
- **Réutilisabilité** : pour une autre mission INTERSOS, il suffit de
  remplacer les deux fichiers dans `data/` et d'ajuster `config.py`
  (titre, ville principale) — aucune autre modification n'est requise.

## 6. Tests

```bash
pytest tests/ -v
```

Couvre le chargement des données, le profilage, le calcul des centroïdes et
l'ensemble des fonctions KPI.

## 7. Module KoBoToolbox

`utils/kobo.py` fournit la structure d'un client KoBo (`KoboClient`) mais ne
contient **aucun identifiant réel** et n'effectue aucun appel réseau tant
que `kobo_base_url` et `kobo_api_token` ne sont pas renseignés dans
`.streamlit/secrets.toml` (copier `secrets.toml.example`). Sans ces
identifiants, ce module reste inactif et n'affecte pas le reste de
l'application.

## 8. Limites connues de cette version

- Les exports Word / PDF / rapport de mission complet ne sont pas encore
  implémentés (formats disponibles actuellement : Excel, CSV, PNG).
- Pas d'authentification (login) — à ajouter si l'application est déployée
  au-delà d'un usage interne à l'équipe IM.
- Pas de conteneurisation Docker fournie dans cette itération.

Voir [`docs/roadmap.md`](docs/roadmap.md) pour le détail de ces prochaines
étapes.
