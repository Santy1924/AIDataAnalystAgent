import pandas as pd


def analyze_csv(file) -> dict:
    df = pd.read_csv(file)

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns.tolist()

    return {
        "rows": len(df),
        "columns_count": len(df.columns),
        "columns": [
            {
                "name": column,
                "data_type": str(df[column].dtype),
                "missing_values": int(
                    df[column].isna().sum()
                ),
            }
            for column in df.columns
        ],
        "numeric_summary": df[numeric_columns]
        .describe()
        .to_dict(),
    }