from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.database import Base, engine
from backend.routers import transactions, webhooks, analytics

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Meridian Payments API",
    description="Internal payment processing and analytics platform.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/health")
def health():
    return {"status": "ok", "service": "meridian-api"}
