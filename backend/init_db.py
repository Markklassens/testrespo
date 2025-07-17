#!/usr/bin/env python3
"""
Database initialization script for MarketMindAI
"""

from database import engine
from models import Base

def init_database():
    """Initialize database tables"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False

if __name__ == "__main__":
    init_database()