from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Demand Sense API",
    description="API for Retail Demand Forecasting",
    version="0.1.0"
)

# CORS Setup
origins = [
    "http://localhost:3000",  # Next.js frontend
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Demand Sense API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

from .app.api.routes import router as prediction_router
app.include_router(prediction_router, prefix="/api/v1")
