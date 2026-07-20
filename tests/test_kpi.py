"""Tests unitaires pour utils/kpi.py."""

import pandas as pd

from utils.kpi import beneficiary_kpis, coverage_rate, indicator_summary, safe_sum, sector_activity_kpis


def test_safe_sum_missing_column_returns_zero():
    df = pd.DataFrame({"A": [1, 2, 3]})
    assert safe_sum(df, "B") == 0.0


def test_safe_sum_existing_column():
    df = pd.DataFrame({"A": [1, 2, 3]})
    assert safe_sum(df, "A") == 6.0


def test_coverage_rate_zero_target():
    df = pd.DataFrame({"Target": [0, 0], "Reached": [5, 5]})
    assert coverage_rate(df, "Reached", "Target") == 0.0


def test_coverage_rate_normal_case():
    df = pd.DataFrame({"Target": [100, 100], "Reached": [50, 50]})
    assert coverage_rate(df, "Reached", "Target") == 50.0


def test_beneficiary_kpis_empty_df():
    kpi = beneficiary_kpis(pd.DataFrame())
    assert kpi["total_beneficiaries"] == 0


def test_beneficiary_kpis_basic():
    df = pd.DataFrame({
        "Household_ID": ["H1", "H1", "H2"],
        "Sex": ["F", "M", "F"],
        "Age": [10, 40, 5],
        "Household_Size": [4, 4, 3],
        "Registration_Status": ["Complete", "Complete", "Incomplete"],
    })
    kpi = beneficiary_kpis(df)
    assert kpi["total_beneficiaries"] == 3
    assert kpi["total_households"] == 2
    assert round(kpi["pct_female"], 1) == round(100 * 2 / 3, 1)
    assert round(kpi["pct_children"], 1) == round(100 * 2 / 3, 1)


def test_sector_activity_kpis_detects_reached_target():
    df = pd.DataFrame({
        "Target_Beneficiaries": [100, 200],
        "Reached_Beneficiaries": [80, 150],
        "Reached_Male": [40, 70],
        "Reached_Female": [40, 80],
    })
    kpi = sector_activity_kpis(df)
    assert kpi["n_activities"] == 2
    assert kpi["total_reached"] == 230
    assert kpi["total_target"] == 300
    assert kpi["coverage_rate"] == round(100 * 230 / 300, 1)


def test_indicator_summary_on_track_off_track():
    df = pd.DataFrame({"Achievement_%": [95.0, 60.0, 100.0]})
    summary = indicator_summary(df)
    assert summary["n_indicators"] == 3
    assert summary["on_track"] == 2
    assert summary["off_track"] == 1
