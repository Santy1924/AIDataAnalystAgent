from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="AI Data Analyst Agent",
    description="API para análisis inteligente de datos",
    version="1.0.0",
)

app.include_router(router)


