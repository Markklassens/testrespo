"""
Background scheduler for periodic tasks
"""

import asyncio
import threading
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import get_db
from trending_calculator import update_trending_scores
import time

class TrendingUpdater:
    def __init__(self):
        self.running = False
        self.thread = None
        self.interval = 300  # 5 minutes
        
    def start(self):
        """Start the trending updater background task"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            print("🚀 Trending updater started - will update every 5 minutes")
    
    def stop(self):
        """Stop the trending updater"""
        self.running = False
        if self.thread:
            self.thread.join()
            print("🛑 Trending updater stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            try:
                # Update trending scores
                db = next(get_db())
                result = update_trending_scores(db)
                print(f"✅ Updated trending scores for {result['updated_tools']} tools at {datetime.utcnow()}")
                db.close()
                
                # Sleep for the interval
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"❌ Error updating trending scores: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def update_now(self):
        """Manually trigger an update"""
        try:
            db = next(get_db())
            result = update_trending_scores(db)
            db.close()
            return result
        except Exception as e:
            print(f"❌ Error in manual update: {e}")
            return {"error": str(e)}

# Global instance
trending_updater = TrendingUpdater()

def start_trending_updater():
    """Start the trending updater"""
    trending_updater.start()

def stop_trending_updater():
    """Stop the trending updater"""
    trending_updater.stop()

def manual_update():
    """Manually trigger a trending update"""
    return trending_updater.update_now()