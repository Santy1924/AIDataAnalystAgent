"""
Integration tests for POST /analyze endpoint.

Purpose: act as a safety shield during all future architecture phases.
If these tests pass, the HTTP contract (response shape + status codes)
is intact regardless of internal refactoring.

Uses FastAPI TestClient (backed by httpx) to send real HTTP requests
against the mounted application without starting a server process.

Coverage:
  1. Happy path  - valid CSV, full response shape verified.
  2. Inconsistencies - age with "unknown" detected and represented correctly.
  3. Nulls in response - null cells not confused with invalid values.
  4. Empty CSV file  - returns HTTP 400.
  5. Non-CSV file    - returns HTTP 400.
  6. No file field   - returns HTTP 422 (FastAPI validation).
  7. Numeric summary - correct stats present for numeric columns.
  8. No numeric cols - numeric_summary is empty dict, no crash.
"""

import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def upload_csv(content: str, filename: str = "test.csv"):
    """POST /analyze with an in-memory CSV file."""
    csv_bytes = content.strip().encode("utf-8")
    return client.post(
        "/analyze",
        files={"file": (filename, io.BytesIO(csv_bytes), "text/csv")},
    )


def find_column(body: dict, name: str) -> dict:
    """Return the column report dict for the given column name."""
    for col in body["columns"]:
        if col["name"] == name:
            return col
    raise KeyError(f"Column '{name}' not found in response.")


# ---------------------------------------------------------------------------
# Test 1: happy path — full response shape
# ---------------------------------------------------------------------------

def test_analyze_valid_csv_returns_200_and_full_shape():
    """
    A clean CSV returns HTTP 200 and a response body that:
    - Contains all top-level DatasetReport keys.
    - Contains all ColumnReport keys for every column.
    """
    csv = (
        "name,age,salary\n"
        "Ana,25,2500\n"
        "Luis,30,3200\n"
        "Carlos,29,2800\n"
        "Maria,28,3500\n"
    )
    resp = upload_csv(csv)
    assert resp.status_code == 200, resp.text

    body = resp.json()

    # Top-level keys
    for key in ["rows", "columns_count", "columns",
                "duplicated_rows", "duplicated_percentage", "numeric_summary"]:
        assert key in body, f"Missing top-level key: '{key}'"

    assert body["rows"] == 4
    assert body["columns_count"] == 3

    # Per-column keys
    required_col_keys = [
        "name", "data_type", "missing_values", "missing_percentage",
        "unique_values", "unique_percentage", "is_unique",
        "has_numeric_inconsistencies", "invalid_numeric_values",
        "invalid_numeric_examples",
    ]
    for col in body["columns"]:
        for k in required_col_keys:
            assert k in col, f"Missing key '{k}' in column '{col.get('name')}'"

    print("[PASS] Test 1: valid CSV returns 200 with full response shape.")


# ---------------------------------------------------------------------------
# Test 2: numeric inconsistency represented in JSON
# ---------------------------------------------------------------------------

def test_analyze_csv_with_unknown_reports_inconsistency():
    """
    'age' column with 'unknown' text value:
    - has_numeric_inconsistencies must be true.
    - invalid_numeric_values must be 1.
    - invalid_numeric_examples must contain 'unknown'.
    """
    csv = (
        "name,age,salary\n"
        "Ana,25,2500\n"
        "Luis,30,3200\n"
        "Carlos,unknown,2800\n"
        "Maria,28,3500\n"
    )
    resp = upload_csv(csv)
    assert resp.status_code == 200, resp.text

    age = find_column(resp.json(), "age")
    assert age["has_numeric_inconsistencies"] is True
    assert age["invalid_numeric_values"] == 1
    assert "unknown" in age["invalid_numeric_examples"]

    print("[PASS] Test 2: 'unknown' in 'age' correctly reflected in JSON.")


# ---------------------------------------------------------------------------
# Test 3: text column has no false positive in JSON
# ---------------------------------------------------------------------------

def test_text_column_has_no_numeric_inconsistency():
    """
    'name' column contains only text.
    The JSON response must show has_numeric_inconsistencies=false.
    """
    csv = (
        "name,age,salary\n"
        "Ana,25,2500\n"
        "Luis,30,3200\n"
    )
    resp = upload_csv(csv)
    assert resp.status_code == 200, resp.text

    name_col = find_column(resp.json(), "name")
    assert name_col["has_numeric_inconsistencies"] is False
    assert name_col["invalid_numeric_values"] == 0
    assert name_col["invalid_numeric_examples"] == []

    print("[PASS] Test 3: 'name' column has no false positive in JSON.")


# ---------------------------------------------------------------------------
# Test 4: null values are NOT counted as invalid in JSON
# ---------------------------------------------------------------------------

def test_null_values_appear_as_missing_not_invalid():
    """
    A blank cell in 'age' must appear as missing_values=1, invalid=0.
    """
    csv = (
        "name,age,salary\n"
        "Ana,25,2500\n"
        "Luis,,3200\n"
        "Carlos,29,2800\n"
    )
    resp = upload_csv(csv)
    assert resp.status_code == 200, resp.text

    age = find_column(resp.json(), "age")
    assert age["missing_values"] == 1
    assert age["has_numeric_inconsistencies"] is False
    assert age["invalid_numeric_values"] == 0

    print("[PASS] Test 4: null cell counted as missing, not as invalid.")


# ---------------------------------------------------------------------------
# Test 5: empty CSV returns 400
# ---------------------------------------------------------------------------

def test_empty_csv_returns_400():
    """An empty file body must return HTTP 400."""
    resp = client.post(
        "/analyze",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()

    print("[PASS] Test 5: empty CSV returns 400.")


# ---------------------------------------------------------------------------
# Test 6: non-CSV filename returns 400
# ---------------------------------------------------------------------------

def test_non_csv_file_returns_400():
    """Uploading a .txt file must return HTTP 400."""
    resp = client.post(
        "/analyze",
        files={"file": ("data.txt", io.BytesIO(b"some text"), "text/plain")},
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"].lower()
    assert "csv" in detail

    print("[PASS] Test 6: non-CSV file returns 400.")


# ---------------------------------------------------------------------------
# Test 7: no file field returns 422 (FastAPI validation)
# ---------------------------------------------------------------------------

def test_missing_file_field_returns_422():
    """A request without the 'file' field must return HTTP 422."""
    resp = client.post("/analyze")
    assert resp.status_code == 422

    print("[PASS] Test 7: missing file field returns 422.")


# ---------------------------------------------------------------------------
# Test 8: numeric_summary contains expected stats
# ---------------------------------------------------------------------------

def test_numeric_summary_contains_expected_stats():
    """
    numeric_summary must include 'count', 'mean', 'std', 'min',
    '25%', '50%', '75%', 'max' for each numeric column.
    """
    csv = (
        "name,age,salary\n"
        "Ana,25,2500\n"
        "Luis,30,3200\n"
        "Carlos,29,2800\n"
    )
    resp = upload_csv(csv)
    assert resp.status_code == 200, resp.text

    summary = resp.json()["numeric_summary"]
    assert "age" in summary
    assert "salary" in summary

    expected_stats = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
    for stat in expected_stats:
        assert stat in summary["age"], f"Missing stat '{stat}' in age summary"

    print("[PASS] Test 8: numeric_summary has all expected stat keys.")


# ---------------------------------------------------------------------------
# Test 9: no numeric columns — numeric_summary is empty dict
# ---------------------------------------------------------------------------

def test_no_numeric_columns_returns_empty_summary():
    """
    When all columns are text (no numeric data at all),
    numeric_summary must be an empty dict {}, returning HTTP 200.
    """
    csv = (
        "name,city\n"
        "Ana,Barranquilla\n"
        "Luis,Bogota\n"
        "Carlos,Medellin\n"
    )
    resp = upload_csv(csv)
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body["numeric_summary"] == {}
    assert body["rows"] == 3
    assert body["columns_count"] == 2

    # Verificar que las columnas de texto mantengan sus métricas normales
    name_col = find_column(body, "name")
    assert name_col["missing_values"] == 0
    assert name_col["has_numeric_inconsistencies"] is False

    city_col = find_column(body, "city")
    assert city_col["missing_values"] == 0
    assert city_col["has_numeric_inconsistencies"] is False

    print("[PASS] Test 9: no-numeric CSV returns HTTP 200 with empty numeric_summary and valid metrics.")


# ---------------------------------------------------------------------------
# Test 10: malformed CSV returns 400
# ---------------------------------------------------------------------------

def test_malformed_csv_returns_400():
    """A malformed/corrupted CSV file must return HTTP 400."""
    resp = client.post(
        "/analyze",
        files={"file": ("corrupted.csv", io.BytesIO(b"\xff\xfe\x00\x00\xaa\xbb"), "text/csv")},
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"].lower()
    assert "could not be parsed" in detail

    print("[PASS] Test 10: malformed CSV returns 400 with proper detail message.")


# ---------------------------------------------------------------------------
# Runner (without pytest)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_analyze_valid_csv_returns_200_and_full_shape,
        test_analyze_csv_with_unknown_reports_inconsistency,
        test_text_column_has_no_numeric_inconsistency,
        test_null_values_appear_as_missing_not_invalid,
        test_empty_csv_returns_400,
        test_non_csv_file_returns_400,
        test_missing_file_field_returns_422,
        test_numeric_summary_contains_expected_stats,
        test_no_numeric_columns_returns_empty_summary,
        test_malformed_csv_returns_400,
    ]

    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {t.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print()
    if failed == 0:
        print("[OK] All integration tests passed.")
    else:
        print(f"[WARN] {failed} test(s) failed.")
        sys.exit(1)
