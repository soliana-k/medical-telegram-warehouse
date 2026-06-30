from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class TopProductResponse(BaseModel):
    product_name: str
    mention_count: int

    class Config:
        from_attributes = True


class ChannelActivityResponse(BaseModel):
    channel_name: str
    date: datetime
    post_count: int
    engagement_rate: Optional[float] = None

class MessageSearchResponse(BaseModel):
    message_id: int
    channel_name: str
    text_content: str
    timestamp: datetime

class VisualContentStatsResponse(BaseModel):
    channel_name: str
    total_images: int
    percentage_with_images: float