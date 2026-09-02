-- Execute only after the table uses storage_policy = 'statistics_tiered'.
-- This is intentionally not a Django migration: applying it blindly to a
-- legacy table with hundreds of millions of rows is unsafe.

ALTER TABLE statistic.ad_stat
    MODIFY TTL played + INTERVAL 1 YEAR TO VOLUME 'cold';

ALTER TABLE statistic.music_stat
    MODIFY TTL played + INTERVAL 1 YEAR TO VOLUME 'cold';

ALTER TABLE statistic.video_stat
    MODIFY TTL played + INTERVAL 1 YEAR TO VOLUME 'cold';

ALTER TABLE statistic.image_stat
    MODIFY TTL played + INTERVAL 1 YEAR TO VOLUME 'cold';

ALTER TABLE statistic.image_stat_backup
    MODIFY TTL played + INTERVAL 1 YEAR TO VOLUME 'cold';

ALTER TABLE statistic.ticker_stat
    MODIFY TTL played + INTERVAL 1 YEAR TO VOLUME 'cold';
