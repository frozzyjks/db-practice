from fastapi import FastAPI
from src.task3.router import router

app = FastAPI(
    title="SPIMEX Trading API",
    description="Микросервис для получения данных торгов СПИМЕКС",
    version="1.0.0"
)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "SPIMEX Trading API", "docs": "/docs"}