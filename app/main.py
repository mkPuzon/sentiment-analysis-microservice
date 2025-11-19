'''main.py


Nov 2025
'''
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import sqlalchemy
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func, Text
from contextlib import asynccontextmanager

# ---- Configuration & Environment ----

# Load environment variables from .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# ---- Hugging Face Model Loading ----

try:
    sentiment_pipeline = pipeline(
        "sentiment-analysis", 
        model="distilbert-base-uncased-finetuned-sst-2-english"
    )
except Exception as e:
    print(f"Error loading Hugging Face model: {e}")
    sentiment_pipeline = None

# ---- Database Setup (SQLAlchemy) ----

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)
# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for our declarative models
class Base(DeclarativeBase):
    pass
# Define our QueryLog database model
class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    input_text = Column(Text, nullable=False)
    model_label = Column(String, nullable=True)
    model_score = Column(Float, nullable=True)

# Function to create tables (we'll call this on startup)
def create_db_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully.")
    except Exception as e:
        print(f"Error creating database tables: {e}")

# ---- FastAPI App Lifecycle (Startup/Shutdown) ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("FastAPI app starting up...")
    print("Connecting to database...")
    create_db_tables()
    print("Loading Hugging Face model...")
    if sentiment_pipeline is None:
        print("Model loading failed. API will not be functional.")
    else:
        print("Model loaded successfully.")
    yield
    # Code to run on shutdown
    print("FastAPI app shutting down...")
    engine.dispose()
    print("Database connection closed.")

# Initialize the FastAPI app with the lifespan event handler
app = FastAPI(lifespan=lifespan)

# ---- API Request/Response Models (Pydantic) ----

class QueryRequest(BaseModel):
    text: str

class QueryResponse(BaseModel):
    input_text: str
    sentiment_label: str
    sentiment_score: float

# ---- Helper: Database Dependency ----

def get_db():
    """
    Dependency to get a database session for a request.
    Ensures the session is always closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---- API Endpoints ----

@app.get("/")
def read_root():
    return {"message": "Hugging Face Query API is running. POST to /query"}

@app.post("/query", response_model=QueryResponse)
async def query_model(request: QueryRequest):
    """
    Query the sentiment analysis model and log the request/response
    to the PostgreSQL database.
    """
    if sentiment_pipeline is None:
        raise HTTPException(
            status_code=503, 
            detail="Model is not available. Check server logs."
        )
        
    db = SessionLocal()
    try:
        # 1. Query the Hugging Face model
        model_result = sentiment_pipeline(request.text)
        
        # This model returns a list, we'll take the first result
        sentiment_label = model_result[0]['label']
        sentiment_score = model_result[0]['score']

        # 2. Log the query and result to the database
        new_log = QueryLog(
            input_text=request.text,
            model_label=sentiment_label,
            model_score=sentiment_score
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)

        # 3. Return the response
        return QueryResponse(
            input_text=request.text,
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score
        )

    except Exception as e:
        db.rollback()
        print(f"Error during query: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"An internal server error occurred: {e}"
        )
    finally:
        db.close()

if __name__ == "__main__":
    # for debugging; ignored in Docker build
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)