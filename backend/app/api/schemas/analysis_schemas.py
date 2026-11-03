"""
Presentation-layer HTTP response schemas for the /analyze endpoint.

Design decisions:
- These models are ONLY for the HTTP contract (request/response shape).
- They do NOT contain business logic or domain rules.
- Domain entities will be introduced separately in later phases (domain/entities/).
- Pydantic is used here for FastAPI integration and automatic Swagger docs.

numeric_summary structure (mirrors pandas df.describe().to_dict()):
  {
    "column_name": {
      "count": 3.0,
      "mean": 27.67,
      "std": 2.52,
      "min": 25.0,
      "25%": 26.5,
      "50%": 28.0,
      "75%": 29.0,
      "max": 30.0
    }
  }
  Values may be None when an entire column contains only null entries
  (pandas produces NaN for those statistics, which serializes to null in JSON).
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ColumnReport(BaseModel):
    """
    HTTP response schema for a single column's analysis report.

    Mirrors the per-column dict produced by csv_analysis_service.analyze_csv().
    This is a presentation contract — not a domain entity.
    """

    name: str = Field(description="Column name as it appears in the CSV header.")
    data_type: str = Field(
        description="Pandas dtype string (e.g. 'object', 'int64', 'float64')."
    )
    missing_values: int = Field(
        description="Absolute count of null/NaN cells in this column."
    )
    missing_percentage: float = Field(
        description="Percentage of null cells relative to total rows (0–100)."
    )
    unique_values: int = Field(
        description="Count of distinct non-null values."
    )
    unique_percentage: float = Field(
        description="Percentage of unique non-null values relative to non-null count."
    )
    is_unique: bool = Field(
        description="True when every non-null value in the column is distinct."
    )
    has_numeric_inconsistencies: bool = Field(
        description=(
            "True when the column contains non-numeric text values "
            "inside a column that is primarily numeric."
        )
    )
    invalid_numeric_values: int = Field(
        description=(
            "Count of non-null values that could not be parsed as a number "
            "in a column identified as predominantly numeric."
        )
    )
    invalid_numeric_examples: List[str] = Field(
        description=(
            "Up to 5 sample values that caused numeric inconsistencies. "
            "Empty list when has_numeric_inconsistencies is False."
        )
    )

    model_config = {"from_attributes": True}


class DatasetReport(BaseModel):
    """
    HTTP response schema for the full dataset analysis.

    Top-level response body for POST /analyze.
    This is a presentation contract — not a domain entity.
    """

    rows: int = Field(description="Total number of rows in the uploaded CSV.")
    columns_count: int = Field(description="Total number of columns.")
    columns: List[ColumnReport] = Field(
        description="Per-column analysis report, one entry per CSV column."
    )
    duplicated_rows: int = Field(
        description="Number of fully duplicated rows detected."
    )
    duplicated_percentage: float = Field(
        description="Percentage of duplicated rows relative to total rows (0–100)."
    )
    numeric_summary: Dict[str, Dict[str, Optional[float]]] = Field(
        description=(
            "Descriptive statistics for numeric columns, "
            "equivalent to pandas df.describe().to_dict(). "
            "Keys are column names; inner keys are 'count', 'mean', 'std', "
            "'min', '25%', '50%', '75%', 'max'. "
            "Inner values are None when all column entries are null."
        )
    )

    model_config = {"from_attributes": True}

