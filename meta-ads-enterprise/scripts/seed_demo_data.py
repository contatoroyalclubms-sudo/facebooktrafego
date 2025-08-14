#!/usr/bin/env python3
"""
Script to seed the database with demonstration data
"""
import asyncio
import asyncpg
import os
from pathlib import Path

async def seed_database():
    """Seed the database with demo data"""
    try:
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/metaads')
        
        print("🌱 Connecting to database...")
        conn = await asyncpg.connect(database_url)
        
        demo_data_path = Path(__file__).parent.parent / 'database' / 'seeds' / 'demo_data.sql'
        
        print("📄 Reading demo data SQL file...")
        with open(demo_data_path, 'r', encoding='utf-8') as f:
            demo_sql = f.read()
        
        print("🚀 Executing demo data insertion...")
        await conn.execute(demo_sql)
        
        print("✅ Demo data seeded successfully!")
        
        campaigns_count = await conn.fetchval("SELECT COUNT(*) FROM campaigns")
        metrics_count = await conn.fetchval("SELECT COUNT(*) FROM campaign_metrics")
        alerts_count = await conn.fetchval("SELECT COUNT(*) FROM alerts")
        insights_count = await conn.fetchval("SELECT COUNT(*) FROM ai_insights")
        
        print(f"📊 Data Summary:")
        print(f"   • Campaigns: {campaigns_count}")
        print(f"   • Metrics: {metrics_count}")
        print(f"   • Alerts: {alerts_count}")
        print(f"   • AI Insights: {insights_count}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error seeding database: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(seed_database())
