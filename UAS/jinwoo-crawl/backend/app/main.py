from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.config import settings
from app.routes import scraper_routes, data_routes, status_routes

app = FastAPI(
    title="JinwooCrawl Intelligence API",
    description="Backend Scraper & Data Ingestion Engine for Big Data UAS Final Project (Issue Attention Cycle)",
    version="1.0.0"
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS
origins = settings.CORS_ORIGINS or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local & tunneling flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(status_routes.router)
app.include_router(scraper_routes.router)
app.include_router(data_routes.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to JinwooCrawl Big Data Ingestion Engine",
        "docs": "/docs",
        "health": "/api/health",
        "tools": "/api/scrape/tools"
    }
