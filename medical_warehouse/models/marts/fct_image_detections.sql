{{ config(materialized='table') }}

with yolo_stage as (
    select * from {{ ref('stg_yolo_detections') }}
),

base_messages as (
    select message_id, channel_key, date_key 
    from {{ ref('fct_messages') }}
)

select
    y.message_id,
    m.channel_key, 
    m.date_key,    
    y.detected_class,
    y.confidence_score,
    y.image_category
from yolo_stage y
inner join base_messages m 
    on y.message_id = m.message_id