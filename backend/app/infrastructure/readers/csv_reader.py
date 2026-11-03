from typing import Any
import pandas as pd
from pandas.errors import EmptyDataError, ParserError


class CSVReaderError(Exception):
    """Excepción base para errores durante la lectura de archivos CSV."""
    pass


class EmptyCSVError(CSVReaderError):
    """Lanzada cuando el archivo CSV está vacío o sin datos legibles."""
    pass


class CSVParseError(CSVReaderError):
    """Lanzada cuando el archivo CSV no se puede parsear o tiene codificación incompatible."""
    pass


def read_csv(file: Any) -> pd.DataFrame:
    """
    Lee un archivo CSV (ruta, buffer o file-like object) y retorna un DataFrame de pandas.

    Captura excepciones específicas de pandas y decodificación (EmptyDataError,
    ParserError, UnicodeDecodeError) y las traduce a excepciones de infraestructura
    (EmptyCSVError, CSVParseError). Cualquier otro error inesperado se propaga sin modificar.
    """
    try:
        return pd.read_csv(file)
    except EmptyDataError as exc:
        raise EmptyCSVError("The CSV file is empty.") from exc
    except (ParserError, UnicodeDecodeError) as exc:
        raise CSVParseError("The CSV file could not be parsed.") from exc
