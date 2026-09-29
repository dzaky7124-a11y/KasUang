from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path
from app.config import BASE_DIR
from app.database import init_db, get_session
from app.routers import auth, wallets, categories, transactions, excel_import, ai_analytics, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    init_db()
    with next(get_session()) as session:
        categories.ensure_default_categories(session)
    yield

app = FastAPI(
    title="KasPintar AI",
    description="Aplikasi Manajemen Kas, Keuangan, dan Analisis AI Multiplatform (Android & Web)",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for web and mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router)
app.include_router(wallets.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(excel_import.router)
app.include_router(ai_analytics.router)
app.include_router(admin.router)

# Mount static folder
static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount sample_data folder
sample_dir = BASE_DIR / "sample_data"
sample_dir.mkdir(parents=True, exist_ok=True)
app.mount("/sample_data", StaticFiles(directory=str(sample_dir)), name="sample_data")

# Serve index.html for Root and SPA fallback
@app.get("/")
async def serve_index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "KasPintar AI API Backend is running"}

@app.get("/manifest.json")
async def serve_manifest():
    manifest_file = static_dir / "manifest.json"
    if manifest_file.exists():
        return FileResponse(str(manifest_file), media_type="application/manifest+json")
    return {}

@app.get("/sw.js")
async def serve_sw():
    sw_file = static_dir / "sw.js"
    if sw_file.exists():
        return FileResponse(str(sw_file), media_type="application/javascript")
    return {}
