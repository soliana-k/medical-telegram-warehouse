from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from api.config import get_db
from api import schemas

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/top-products", response_model=List[schemas.TopProductResponse])
def get_top_products(limit: int = 10, db: Session = Depends(get_db)):
  
    query = text("""
        SELECT 
            clean_word AS product_name, 
            COUNT(*)::int AS mention_count
        FROM (
            SELECT regexp_split_to_table(lower(message_text), '\s+') AS word 
            FROM analytics.fct_messages
        ) t,
        LATERAL (SELECT regexp_replace(word, '[^a-zA-Z]', '', 'g') AS clean_word) l
        WHERE clean_word IN ('paracetamol', 'amoxicillin', 'vitamin', 'cream', 'serum', 'gel', 'capsule', 'syrup', 'tablet', 'brent')
          AND length(clean_word) > 2
        GROUP BY clean_word
        ORDER BY mention_count DESC
        LIMIT :limit;
    """)
    result = db.execute(query, {"limit": limit}).fetchall()
    return result

@router.get("/visual-content", response_model=List[schemas.VisualContentStatsResponse])
def get_visual_content_stats(db: Session = Depends(get_db)):
    query = text("""
        SELECT 
            c.channel_name,
            COUNT(f.message_id)::int as total_messages,
            SUM(CASE WHEN f.has_image_flag = true THEN 1 ELSE 0 END)::int as total_images, -- FIXED ALIAS
            ROUND((SUM(CASE WHEN f.has_image_flag = true THEN 1 ELSE 0 END)::numeric / COUNT(f.message_id)) * 100, 2)::float as percentage_with_images, -- FIXED ALIAS
            SUM(CASE WHEN y.image_category = 'promotional' THEN 1 ELSE 0 END)::int as promotional_count,
            SUM(CASE WHEN y.image_category = 'product_display' THEN 1 ELSE 0 END)::int as product_display_count,
            SUM(CASE WHEN y.image_category = 'lifestyle' THEN 1 ELSE 0 END)::int as lifestyle_count
        FROM analytics.fct_messages f
        JOIN analytics.dim_channels c ON f.channel_key = c.channel_key
        LEFT JOIN raw.yolo_detections y ON f.message_id = y.message_id
        GROUP BY c.channel_name;
    """)
    result = db.execute(query).fetchall()
    return result