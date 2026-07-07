import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, bookings, forecasting, hotels, ingestion, ml_pricing, rooms, smart_queries
from app.database.init_db import init_db

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=os.getenv("API_TITLE", "HotelIQ Revenue Management API"),
    version=os.getenv("API_VERSION", "1.0.0"),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(hotels.router)
app.include_router(rooms.router)
app.include_router(bookings.router)
app.include_router(ingestion.router)
app.include_router(analytics.router)
app.include_router(smart_queries.router)
app.include_router(forecasting.router)
app.include_router(ml_pricing.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "HotelIQ API"}

