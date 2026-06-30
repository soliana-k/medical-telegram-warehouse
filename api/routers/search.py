from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from api.config import get_db
from api import schemas

router = APIRouter(prefix="/api/search", tags=["Search"])

@router.get("/messages", response_model=List[schemas.MessageSearchResponse])
def search_messages(query: str, limit: int = 20, db: Session = Depends(get_db)):
    sql_query = text("""
        SELECT 
            f.message_id,
            c.channel_name,
            f.message_text AS text_content,  -- FIXED ALIAS
            d.full_date AS timestamp,        -- FIXED: Selected required missing field
            f.view_count,
            f.forward_count,
            f.has_image_flag
        FROM analytics.fct_messages f
        JOIN analytics.dim_channels c ON f.channel_key = c.channel_key
        JOIN analytics.dim_dates d ON f.date_key = d.date_key
        WHERE f.message_text ILIKE :search_str
        ORDER BY f.view_count DESC
        LIMIT :limit;
    """)
    
    result = db.execute(sql_query, {
        "search_str": f"%{query}%", 
        "limit": limit
    }).fetchall()
    
    return result