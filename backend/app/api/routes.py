from fastapi import APIRouter, File, HTTPException, UploadFile
from pandas.errors import EmptyDataError, ParserError

from app.services.csv_analysis_service import analyze_csv

router = APIRouter()


@router.get("/")
def root():
    return {
        "message": "AI Data Analyst Agent API is running"
    }


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.post("/analyze")
def analyze_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported."
        )

    try:
        result = analyze_csv(file.file)
        return result
    except EmptyDataError:
        raise HTTPException(
            status_code=400,
            detail="The CSV file is empty."
        )
    except (ParserError, UnicodeDecodeError):
        raise HTTPException(
            status_code=400,
            detail="The CSV file could not be parsed."
        )
    finally:
        file.file.close()