"""Tests unitaires pour utils/data_loader.py."""

import pandas as pd

from config import EXCEL_PATH, GEOJSON_PATH
from utils.data_loader import (
    get_reference_values,
    get_region_centroids,
    list_sheets,
    load_all_sheets,
    load_geojson,
    profile_sheet,
)


def test_excel_file_exists():
    assert EXCEL_PATH.exists(), "Le fichier Excel de référence doit exister dans data/"


def test_geojson_file_exists():
    assert GEOJSON_PATH.exists(), "Le fichier GeoJSON de référence doit exister dans data/"


def test_list_sheets_returns_expected_names():
    sheets = list_sheets()
    assert "Beneficiary_Registration" in sheets
    assert "Indicator_Tracker" in sheets
    assert len(sheets) >= 6


def test_load_all_sheets_returns_dataframes():
    sheets = load_all_sheets()
    assert isinstance(sheets, dict)
    assert all(isinstance(df, pd.DataFrame) for df in sheets.values())
    assert len(sheets["Beneficiary_Registration"]) > 0


def test_load_geojson_returns_feature_collection():
    gj = load_geojson()
    assert gj is not None
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) > 0


def test_region_centroids_cover_all_features():
    centroids = get_region_centroids()
    gj = load_geojson()
    assert len(centroids) == len(gj["features"])
    for c in centroids.values():
        assert -90 <= c["lat"] <= 90
        assert -180 <= c["lon"] <= 180


def test_get_reference_values_returns_sorted_unique_list():
    sheets = load_all_sheets()
    provinces = get_reference_values(sheets, "Province")
    assert provinces == sorted(set(provinces))
    assert len(provinces) > 0


def test_profile_sheet_structure():
    sheets = load_all_sheets()
    profile = profile_sheet(sheets["Beneficiary_Registration"])
    assert profile["n_rows"] == len(sheets["Beneficiary_Registration"])
    assert "Age" in profile["columns"]
    assert profile["columns"]["Age"]["kind"] == "numeric"
