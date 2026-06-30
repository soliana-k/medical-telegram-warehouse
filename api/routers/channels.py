from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from api.config import get_db
from api import schemas

router = APIRouter(prefix="/api/channels", tags=["Channels"])

@router.get("/{channel_name}/activity", response_model=List[schemas.ChannelActivityResponse])
def get_channel_activity(channel_name: str, db: Session = Depends(get_db)):
    query = text("""
        SELECT 
            c.channel_name,
            d.full_date as date,
            COUNT(f.message_id)::int as post_count,
            SUM(f.view_count)::int as total_views,
            SUM(f.forward_count)::int as total_forwards
        FROM analytics.fct_messages f
        JOIN analytics.dim_channels c ON f.channel_key = c.channel_key
        JOIN analytics.dim_dates d ON f.date_key = d.date_key
        WHERE LOWER(c.channel_name) = LOWER(:channel_name)
        GROUP BY c.channel_name, d.full_date
        ORDER BY d.full_date DESC;
    """)
    result = db.execute(query, {"channel_name": channel_name}).fetchall()
    
    if not result:
        raise HTTPException(status_code=404, detail=f"No activity records found for channel: {channel_name}")
        
    return result