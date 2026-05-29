from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.services.auction.auction_service import sync_expired_auctions

scheduler = BackgroundScheduler(timezone="UTC")

def _run_auction_sync(session_factory):
    db = session_factory()
    try:
        updated = sync_expired_auctions(db)
        if updated:
            print(f"[auction_scheduler] updated auctions: {updated}")
    finally:
        db.close()

def start_auction_scheduler(session_factory, interval_seconds: int = 5):
    if scheduler.running:
        return

    scheduler.add_job(
        _run_auction_sync,
        trigger=IntervalTrigger(seconds=interval_seconds),
        args=[session_factory],
        id="auction_status_sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()

def stop_auction_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)