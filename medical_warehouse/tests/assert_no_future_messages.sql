select *
from {{ ref('stg_telegram_messages') }}
where message_at > current_timestamp