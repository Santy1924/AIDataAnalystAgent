import pandas as pd


def analyze_csv(file) -> dict:
    df = pd.read_csv(file)

    numeric_columns = df.select_dtypes(include="number").columns.tolist()

    rows = len(df)

    # Analizar cada columna
    columns_info = []

    for column in df.columns:
        missing_values = int(df[column].isna().sum())

        missing_percentage = (
            round((missing_values / rows) * 100, 2)
            if rows > 0
            else 0.0
        )

        columns_info.append({
            "name": column,
            "data_type": str(df[column].dtype),
            "missing_values": missing_values,
            "missing_percentage": missing_percentage,
        })

    # Detectar filas duplicadas
    duplicated_rows = int(df.duplicated().sum())

    duplicated_percentage = (
        round((duplicated_rows / rows) * 100, 2)
        if rows > 0
        else 0.0
    )

    # Resumen estadístico de columnas numéricas
    numeric_summary = df[numeric_columns].describe().to_dict()

    return {
        "rows": rows,
        "columns_count": len(df.columns),
        "columns": columns_info,
        "duplicated_rows": duplicated_rows,
        "duplicated_percentage": duplicated_percentage,
        "numeric_summary": numeric_summary,
    }