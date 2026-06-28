with stage_data as (
    select * from {{ ref('stg_telegram_messages') }}
),

aggregates as (
    select
        channel_name,
        min(message_date) as first_post_date,
        max(message_date) as last_post_date,
        count(message_id) as total_posts,
        round(avg(view_count), 2) as avg_views
    from stage_data
    group by channel_name
)

select
    md5(channel_name) as channel_key,
    channel_name,
    
    case 
        when channel_name ilike '%pharm%' then 'Pharmaceutical'
        when channel_name ilike '%cosm%' or channel_name ilike '%beauty%' then 'Cosmetics'
        else 'Medical'
    end as channel_type,
    
    first_post_date,
    last_post_date,
    total_posts,
    avg_views
from aggregates