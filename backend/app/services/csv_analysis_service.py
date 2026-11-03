
import pandas as pd

from app.infrastructure.readers.csv_reader import read_csv


def analyze_csv(file) -> dict:
    df = read_csv(file)

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

        # Contar valores únicos
        unique_values = int(df[column].nunique())

        # Contar valores que no están vacíos
        non_missing_values = rows - missing_values

        # Calcular porcentaje de valores únicos
        unique_percentage = (
            round((unique_values / non_missing_values) * 100, 2)
            if non_missing_values > 0
            else 0.0
        )

        # Verificar si todos los valores no vacíos son únicos
        is_unique = (
            unique_values == non_missing_values
            and non_missing_values > 0
        )

        # Inicializar detección de inconsistencias
        invalid_numeric_values = 0
        invalid_numeric_examples = []
        has_numeric_inconsistencies = False

        # Detectar posibles inconsistencias numéricas
        # Primero revisamos si la columna ya es numérica
        if column in numeric_columns:
            numeric_values = pd.to_numeric(
                df[column],
                errors="coerce"
            )

            invalid_numeric_values = int(
                numeric_values.isna().sum() - missing_values
            )

            has_numeric_inconsistencies = (
                invalid_numeric_values > 0
            )

            if has_numeric_inconsistencies:
                invalid_numeric_examples = (
                    df.loc[
                        numeric_values.isna() & df[column].notna(),
                        column
                    ]
                    .astype(str)
                    .unique()
                    .tolist()[:5]
                )

        else:
            # Para columnas de texto: verificar si la columna
            # "debería" ser numérica analizando qué proporción
            # de sus valores no nulos son convertibles a número.
            converted_values = pd.to_numeric(
                df[column],
                errors="coerce"
            )

            non_null_count = int(df[column].notna().sum())
            valid_numeric_count = int(converted_values.notna().sum())

            # Consideramos que la columna "debería ser numérica"
            # solo si la MAYORÍA (>50%) de sus valores no nulos
            # son numéricos. Esto evita marcar columnas de texto
            # puras (como `name`) como inconsistentes.
            if non_null_count > 0 and (
                valid_numeric_count / non_null_count
            ) > 0.5:
                # Los valores inválidos son los que no son nulos
                # en el DataFrame original pero SÍ se volvieron
                # NaN al convertir — es decir, los no numéricos.
                invalid_mask = df[column].notna() & converted_values.isna()
                invalid_numeric_values = int(invalid_mask.sum())

                has_numeric_inconsistencies = (
                    invalid_numeric_values > 0
                )

                if has_numeric_inconsistencies:
                    invalid_numeric_examples = (
                        df.loc[invalid_mask, column]
                        .astype(str)
                        .unique()
                        .tolist()[:5]
                    )

        # Agregar información de la columna
        columns_info.append({
            "name": column,
            "data_type": str(df[column].dtype),
            "missing_values": missing_values,
            "missing_percentage": missing_percentage,
            "unique_values": unique_values,
            "unique_percentage": unique_percentage,
            "is_unique": is_unique,
            "has_numeric_inconsistencies": has_numeric_inconsistencies,
            "invalid_numeric_values": invalid_numeric_values,
            "invalid_numeric_examples": invalid_numeric_examples,
        })

    # Detectar filas duplicadas
    duplicated_rows = int(df.duplicated().sum())

    duplicated_percentage = (
        round((duplicated_rows / rows) * 100, 2)
        if rows > 0
        else 0.0
    )

    # Resumen estadístico de columnas numéricas
    if numeric_columns:
        numeric_summary = df[numeric_columns].describe().to_dict()
    else:
        numeric_summary = {}

    return {
        "rows": rows,
        "columns_count": len(df.columns),
        "columns": columns_info,
        "duplicated_rows": duplicated_rows,
        "duplicated_percentage": duplicated_percentage,
        "numeric_summary": numeric_summary,
    }
