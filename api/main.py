from fastapi import FastAPI
from api.routers import reports, channels, search

app = FastAPI(
    title="Data Warehouse Analytical API",
    description="REST API endpoints to query dbt analytical marts.",
    version="1.0.0"
)

app.include_router(reports.router)
app.include_router(channels.router)
app.include_router(search.router)

@app.get("/")
def health_check():
    return {"status": "healthy", "warehouse_connected": True}