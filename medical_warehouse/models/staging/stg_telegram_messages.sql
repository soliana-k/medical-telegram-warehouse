with source_data as (
    select * from {{ source('raw_sources', 'telegram_messages') }}
),

standardized as (
    select
        cast(message_id as bigint) as message_id,
        cast(channel_name as varchar(255)) as channel_name,
        
        cast(left(date, 19) as timestamp) as message_at,
        cast(left(date, 10) as date) as message_date,
        
        cast(message_text as text) as message_text,
        coalesce(cast(views as integer), 0) as view_count,
        coalesce(cast(forwards as integer), 0) as forward_count,
        
        length(coalesce(message_text, '')) as message_length,
        case 
            when media_type = 'MessageMediaPhoto' then true 
            else false 
        end as has_image_flag

    from source_data
    where message_id is not null
      and message_text is not null 
      and trim(message_text) != ''
)

select * from standardized