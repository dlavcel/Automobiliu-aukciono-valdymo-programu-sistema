from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from backend.api.v1.auth import router as auth_router
from backend.api.v1.listings import router as listings_router
from backend.api.v1.admin_listings import router as admin_listings_router
from backend.api.v1.auctions import router as auctions_router
from backend.api.v1.admin_auctions import router as admin_auctions_router
from backend.api.v1.bids import router as bids_router
from backend.api.v1.auction_history import router as auction_history_router
from backend.db.base import Base
from backend.db.session import engine, SessionLocal
from backend.api.v1.auction_ws import router as auction_ws_router
from backend.api.v1.user_auctions import router as user_auctions_router
from backend.services.auction.auction_scheduler import start_auction_scheduler, stop_auction_scheduler

app = FastAPI(title="Auction")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://localhost:5173",
        "https://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    start_auction_scheduler(SessionLocal, interval_seconds=5)

@app.on_event("shutdown")
def on_shutdown():
    stop_auction_scheduler()

Base.metadata.create_all(bind=engine)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(listings_router, prefix="/api/v1")
app.include_router(admin_listings_router, prefix="/api/v1")
app.include_router(auctions_router, prefix="/api/v1")
app.include_router(admin_auctions_router, prefix="/api/v1")
app.include_router(bids_router, prefix="/api/v1")
app.include_router(auction_history_router, prefix="/api/v1")
app.include_router(auction_ws_router)
app.include_router(user_auctions_router, prefix="/api/v1")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
