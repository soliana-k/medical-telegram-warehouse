with source_data as (
    select * from {{ source('raw_sources', 'yolo_detections') }}
)

select
    cast(message_id as bigint) as message_id,
    cast(channel_name as varchar(255)) as channel_name,
    cast(detected_objects as varchar(500)) as detected_class,
    cast(confidence_score as numeric) as confidence_score,
    cast(image_category as varchar(100)) as image_category,
    cast(image_path as text) as image_path
from source_data