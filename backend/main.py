from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from contextlib import asynccontextmanager
from .db import create_db_and_tables
from .api import debug, kids, chores, approvals, ledger, finances, system, management
from .services.automation import AutomationService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB exists
    create_db_and_tables()
    
    # Start Automation
    automation = AutomationService()
    automation.start()
    
    yield
    # Shutdown: Clean up if needed

app = FastAPI(
    title="Chores Kiosk API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS (Allow all for local LAN/Dev simplicity)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
# Mount Static Files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount Admin Web
os.makedirs("backend/admin", exist_ok=True) # Ensure it exists
app.mount("/admin", StaticFiles(directory="backend/admin", html=True), name="admin")

# Include Routers
app.include_router(debug.router)
app.include_router(kids.router)
app.include_router(chores.router)
app.include_router(approvals.router)
app.include_router(ledger.router)
app.include_router(finances.router)
app.include_router(finances.router)
app.include_router(system.router)
app.include_router(management.router)

# Old health check moved to system.router /api/system/status

@app.get("/")
def root():
    return {"message": "Chores Kiosk API is running. Go to /docs for Swagger UI."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
