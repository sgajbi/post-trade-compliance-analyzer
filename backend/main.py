import json
import logging
from datetime import datetime 
from bson import ObjectId 
from fastapi import FastAPI, UploadFile, File, HTTPException 
from fastapi.middleware.cors import CORSMiddleware
from db.mongo import portfolio_collection

import os
from utils.serializers import serialize_portfolio_summary, serialize_portfolio_detail 
from routers import static_data 
from routers import portfolio 

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

app.include_router(static_data.router)
app.include_router(portfolio.router) 

@app.get("/")
def read_root():
    """
    Root endpoint to confirm the backend is running.
    """
    return {"message": "Post-Trade Compliance Analyzer backend is running"}
