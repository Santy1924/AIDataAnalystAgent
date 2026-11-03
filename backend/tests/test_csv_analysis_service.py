"""
Pruebas unitarias para csv_analysis_service.py

Escenarios cubiertos:
  1. Columna mixta (age con "unknown") -> debe detectar el valor invalido.
  2. Columna de texto pura (name)      -> NO debe generar falso positivo.
  3. Valores nulos                     -> NO deben reportarse como invalidos.
  4. Nulo + invalido combinados        -> conteo separado y correcto.
  5. Columna completamente numerica    -> sin inconsistencias.
  6. Estructura JSON del resultado     -> todas las claves presentes.
"""

import io
import sys
import os

# Permitir importar desde backend/app sin instalar el paquete
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.csv_analysis_service import analyze_csv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def csv_file(content: str) -> io.BytesIO:
    """Convierte un string CSV en un objeto file-like de bytes."""
    return io.BytesIO(content.strip().encode("utf-8"))


def column_info(result: dict, name: str) -> dict:
    """Devuelve la info de una columna especifica del resultado."""
    for col in result["columns"]:
        if col["name"] == name:
            return col
    raise KeyError(f"Columna '{name}' no encontrada en el resultado.")


# ---------------------------------------------------------------------------
# Test 1: columna mixta -- age con "unknown"
# ---------------------------------------------------------------------------

def test_detects_invalid_in_numeric_column():
    """
    'age' tiene 3 valores numericos y 1 texto ("unknown").
    El sistema debe detectar 1 valor invalido y mostrarlo en los ejemplos.
    """
    csv_content = (
        "name,age,salary\n"
        "Ana,25,2500\n"
        "Luis,30,3200\n"
        "Carlos,unknown,2800\n"
        "Maria,28,3500"
    )

    result = analyze_csv(csv_file(csv_content))
    age = column_info(result, "age")

    assert age["has_numeric_inconsistencies"] is True, (
        "age deberia tener inconsistencias numericas"
    )
    assert age["invalid_numeric_values"] == 1, (
        f"Se esperaba 1 valor invalido, se encontraron {age['invalid_numeric_values']}"
    )
    assert "unknown" in age["invalid_numeric_examples"], (
        f"'unknown' deberia estar en los ejemplos, got: {age['invalid_numeric_examples']}"
    )
    print("[PASS] Test 1: 'unknown' en columna 'age' detectado correctamente.")


# ---------------------------------------------------------------------------
# Test 2: columna de texto pura -- name no genera falso positivo
# ---------------------------------------------------------------------------

def test_no_false_positive_on_text_column():
    """
    'name' contiene solo texto. No debe marcarse como inconsistente.
    """
    csv_content = (
        "name,age,salary\n"
        "Ana,25,2500\n"
        "Luis,30,3200\n"
        "Carlos,29,2800\n"
        "Maria,28,3500"
    )

    result = analyze_csv(csv_file(csv_content))
    name = column_info(result, "name")

    assert name["has_numeric_inconsistencies"] is False, (
        "La columna 'name' NO deberia tener inconsistencias numericas"
    )
    assert name["invalid_numeric_values"] == 0, (
        f"Se esperaba 0 valores invalidos en 'name', got: {name['invalid_numeric_values']}"
    )
    print("[PASS] Test 2: columna 'name' no genera falso positivo.")


# ---------------------------------------------------------------------------
# Test 3: valores nulos no se cuentan como invalidos
# ---------------------------------------------------------------------------

def test_nulls_not_counted_as_invalid():
    """
    'age' tiene un valor nulo (celda vacia). El nulo no debe contarse
    como valor numerico invalido, solo como missing_value.
    """
    csv_content = (
        "name,age,salary\n"
        "Ana,25,2500\n"
        "Luis,,3200\n"
        "Carlos,29,2800\n"
        "Maria,28,3500"
    )

    result = analyze_csv(csv_file(csv_content))
    age = column_info(result, "age")

    assert age["missing_values"] == 1, (
        f"Se esperaba 1 missing value, got: {age['missing_values']}"
    )
    assert age["has_numeric_inconsistencies"] is False, (
        "Un valor nulo NO debe reportarse como inconsistencia numerica"
    )
    assert age["invalid_numeric_values"] == 0, (
        f"Se esperaba 0 invalidos, got: {age['invalid_numeric_values']}"
    )
    print("[PASS] Test 3: valor nulo no confundido con invalido.")


# ---------------------------------------------------------------------------
# Test 4: columna mixta con nulo + valor invalido -- combinacion real
# ---------------------------------------------------------------------------

def test_null_and_invalid_combination():
    """
    'age' tiene 1 nulo Y 1 texto invalido ("unknown").
    Debe reportar solo 1 invalido y 1 nulo, sin duplicar.
    """
    csv_content = (
        "name,age,salary\n"
        "Ana,25,2500\n"
        "Luis,,3200\n"
        "Carlos,unknown,2800\n"
        "Maria,28,3500"
    )

    result = analyze_csv(csv_file(csv_content))
    age = column_info(result, "age")

    assert age["missing_values"] == 1, (
        f"Se esperaba 1 missing value, got: {age['missing_values']}"
    )
    assert age["has_numeric_inconsistencies"] is True, (
        "Debe detectar 'unknown' como valor invalido"
    )
    assert age["invalid_numeric_values"] == 1, (
        f"Se esperaba exactamente 1 invalido (no el nulo), got: {age['invalid_numeric_values']}"
    )
    assert "unknown" in age["invalid_numeric_examples"]
    print("[PASS] Test 4: nulo + invalido separados correctamente.")


# ---------------------------------------------------------------------------
# Test 5: columna completamente numerica -- sin inconsistencias
# ---------------------------------------------------------------------------

def test_fully_numeric_column_no_issues():
    """
    'salary' tiene solo valores numericos. No debe marcar inconsistencias.
    """
    csv_content = (
        "name,age,salary\n"
        "Ana,25,2500\n"
        "Luis,30,3200\n"
        "Carlos,29,2800\n"
        "Maria,28,3500"
    )

    result = analyze_csv(csv_file(csv_content))
    salary = column_info(result, "salary")

    assert salary["has_numeric_inconsistencies"] is False
    assert salary["invalid_numeric_values"] == 0
    print("[PASS] Test 5: columna 'salary' completamente numerica, sin falsos positivos.")


# ---------------------------------------------------------------------------
# Test 6: estructura general del resultado JSON
# ---------------------------------------------------------------------------

def test_result_json_structure():
    """
    Verifica que el resultado contiene todas las claves esperadas
    por el endpoint POST /analyze.
    """
    csv_content = (
        "name,age,salary\n"
        "Ana,25,2500\n"
        "Luis,30,3200"
    )

    result = analyze_csv(csv_file(csv_content))

    assert "rows" in result
    assert "columns_count" in result
    assert "columns" in result
    assert "duplicated_rows" in result
    assert "duplicated_percentage" in result
    assert "numeric_summary" in result

    for col in result["columns"]:
        for key in [
            "name", "data_type", "missing_values", "missing_percentage",
            "unique_values", "unique_percentage", "is_unique",
            "has_numeric_inconsistencies", "invalid_numeric_values",
            "invalid_numeric_examples",
        ]:
            assert key in col, f"Clave '{key}' falta en columna '{col['name']}'"

    print("[PASS] Test 6: estructura JSON correcta.")


# ---------------------------------------------------------------------------
# Runner manual (sin pytest)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_detects_invalid_in_numeric_column,
        test_no_false_positive_on_text_column,
        test_nulls_not_counted_as_invalid,
        test_null_and_invalid_combination,
        test_fully_numeric_column_no_issues,
        test_result_json_structure,
    ]

    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {t.__name__}: {e}")
            failed += 1

    print()
    if failed == 0:
        print("[OK] Todos los tests pasaron correctamente.")
    else:
        print(f"[WARN] {failed} test(s) fallaron.")
        sys.exit(1)
