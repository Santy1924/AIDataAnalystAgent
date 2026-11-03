"""
Unit tests for app.infrastructure.readers.csv_reader

Scenarios:
  1. Valid CSV with mixed types -> returns DataFrame correctly.
  2. Valid CSV with only text columns -> returns DataFrame correctly.
  3. Valid CSV with only numeric columns -> returns DataFrame correctly.
  4. CSV with numeric inconsistencies (e.g. 'unknown') -> preserves raw text as object dtype.
  5. Empty CSV (0 bytes) -> raises EmptyCSVError.
  6. CSV with only whitespace/newlines -> raises EmptyCSVError.
  7. Malformed CSV with undecodable binary bytes -> raises CSVParseError.
  8. Malformed CSV with inconsistent column counts -> raises CSVParseError.
  9. Unexpected non-CSV errors (e.g. ValueError/TypeError) propagate without modification.
"""

import io
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.infrastructure.readers.csv_reader import (
    CSVParseError,
    CSVReaderError,
    EmptyCSVError,
    read_csv,
)


def to_bytes_io(content: str) -> io.BytesIO:
    return io.BytesIO(content.strip().encode("utf-8"))


# ---------------------------------------------------------------------------
# Test 1: Valid CSV with mixed types
# ---------------------------------------------------------------------------
def test_read_valid_csv():
    csv_data = "name,age,salary\nAna,25,2500\nLuis,30,3200"
    df = read_csv(to_bytes_io(csv_data))

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["name", "age", "salary"]
    assert df["name"].tolist() == ["Ana", "Luis"]
    print("[PASS] Test 1: Valid CSV read successfully.")


# ---------------------------------------------------------------------------
# Test 2: CSV with only text columns
# ---------------------------------------------------------------------------
def test_read_text_only_csv():
    csv_data = "name,city\nAna,Barranquilla\nLuis,Bogota"
    df = read_csv(to_bytes_io(csv_data))

    assert len(df) == 2
    assert list(df.columns) == ["name", "city"]
    print("[PASS] Test 2: Text-only CSV read successfully.")


# ---------------------------------------------------------------------------
# Test 3: CSV with only numeric columns
# ---------------------------------------------------------------------------
def test_read_numeric_only_csv():
    csv_data = "a,b\n1,10.5\n2,20.0"
    df = read_csv(to_bytes_io(csv_data))

    assert len(df) == 2
    assert list(df.columns) == ["a", "b"]
    assert pd.api.types.is_numeric_dtype(df["a"])
    assert pd.api.types.is_numeric_dtype(df["b"])
    print("[PASS] Test 3: Numeric-only CSV read successfully.")


# ---------------------------------------------------------------------------
# Test 4: CSV with inconsistencies preserves string values
# ---------------------------------------------------------------------------
def test_read_csv_with_inconsistencies():
    csv_data = "name,age\nAna,25\nCarlos,unknown"
    df = read_csv(to_bytes_io(csv_data))

    assert len(df) == 2
    assert df["age"].iloc[1] == "unknown"
    assert not pd.api.types.is_numeric_dtype(df["age"])
    print("[PASS] Test 4: Inconsistent column preserved as non-numeric type.")


# ---------------------------------------------------------------------------
# Test 5: Empty CSV (0 bytes) raises EmptyCSVError
# ---------------------------------------------------------------------------
def test_read_empty_csv_raises():
    try:
        read_csv(io.BytesIO(b""))
        assert False, "Should have raised EmptyCSVError"
    except EmptyCSVError as exc:
        assert isinstance(exc, CSVReaderError)
        assert "empty" in str(exc).lower()

    print("[PASS] Test 5: Empty CSV raised EmptyCSVError.")


# ---------------------------------------------------------------------------
# Test 6: Whitespace-only CSV raises EmptyCSVError
# ---------------------------------------------------------------------------
def test_read_whitespace_csv_raises():
    try:
        read_csv(io.BytesIO(b"   \n\n\t  \n"))
        assert False, "Should have raised EmptyCSVError"
    except EmptyCSVError:
        pass

    print("[PASS] Test 6: Whitespace-only CSV raised EmptyCSVError.")


# ---------------------------------------------------------------------------
# Test 7: Malformed CSV with undecodable bytes raises CSVParseError
# ---------------------------------------------------------------------------
def test_read_undecodable_bytes_raises():
    try:
        # Invalid utf-8 byte sequence
        read_csv(io.BytesIO(b"\xff\xfe\x00\x00\xaa\xbb"))
        assert False, "Should have raised CSVParseError"
    except CSVParseError as exc:
        assert isinstance(exc, CSVReaderError)

    print("[PASS] Test 7: Undecodable bytes raised CSVParseError.")


# ---------------------------------------------------------------------------
# Test 8: Malformed CSV with irregular columns raises CSVParseError
# ---------------------------------------------------------------------------
def test_read_inconsistent_columns_raises():
    # Header defines 2 columns, but line 3 has 4 columns -> parser error
    malformed_csv = b"col1,col2\n1,2\n3,4,5,6\n7,8"
    try:
        read_csv(io.BytesIO(malformed_csv))
        assert False, "Should have raised CSVParseError"
    except CSVParseError as exc:
        assert isinstance(exc, CSVReaderError)

    print("[PASS] Test 8: Inconsistent columns raised CSVParseError.")


# ---------------------------------------------------------------------------
# Test 9: Unexpected errors propagate without being masked as CSVParseError
# ---------------------------------------------------------------------------
def test_unexpected_errors_propagate():
    try:
        read_csv(12345)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    except CSVParseError:
        assert False, "Should NOT have caught as CSVParseError"

    print("[PASS] Test 9: Unexpected errors propagate unmodified.")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        test_read_valid_csv,
        test_read_text_only_csv,
        test_read_numeric_only_csv,
        test_read_csv_with_inconsistencies,
        test_read_empty_csv_raises,
        test_read_whitespace_csv_raises,
        test_read_undecodable_bytes_raises,
        test_read_inconsistent_columns_raises,
        test_unexpected_errors_propagate,
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
        print("[OK] All csv_reader tests passed.")
    else:
        print(f"[WARN] {failed} test(s) failed.")
        sys.exit(1)
