import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import static_data
from routers import portfolio
from routers import rag 

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(static_data.router)
app.include_router(portfolio.router)
app.include_router(rag.router)

@app.get("/")
def read_root():
    """
    Root endpoint to confirm the backend is running.
    """
    return {"message": "Post-Trade Compliance Analyzer backend is running"}
