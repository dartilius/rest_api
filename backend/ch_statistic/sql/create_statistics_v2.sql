-- Create optimized copies beside existing production tables.
-- Run after the `statistics_tiered` policy is installed, before changing
-- CLICKHOUSE_STATISTICS_TABLE_SUFFIX to `_v2`.

CREATE TABLE IF NOT EXISTS statistic.ad_stat_v2 AS statistic.ad_stat
ENGINE = MergeTree
PARTITION BY toYYYYMM(played, 'Asia/Krasnoyarsk')
ORDER BY (client, played, id)
TTL played + INTERVAL 1 YEAR TO VOLUME 'cold'
SETTINGS storage_policy = 'statistics_tiered';

CREATE TABLE IF NOT EXISTS statistic.music_stat_v2 AS statistic.music_stat
ENGINE = MergeTree
PARTITION BY toYYYYMM(played, 'Asia/Krasnoyarsk')
ORDER BY (client, played, id)
TTL played + INTERVAL 1 YEAR TO VOLUME 'cold'
SETTINGS storage_policy = 'statistics_tiered';

CREATE TABLE IF NOT EXISTS statistic.video_stat_v2 AS statistic.video_stat
ENGINE = MergeTree
PARTITION BY toYYYYMM(played, 'Asia/Krasnoyarsk')
ORDER BY (client, played, id)
TTL played + INTERVAL 1 YEAR TO VOLUME 'cold'
SETTINGS storage_policy = 'statistics_tiered';

CREATE TABLE IF NOT EXISTS statistic.image_stat_v2 AS statistic.image_stat
ENGINE = MergeTree
PARTITION BY toYYYYMM(played, 'Asia/Krasnoyarsk')
ORDER BY (client, played, id)
TTL played + INTERVAL 1 YEAR TO VOLUME 'cold'
SETTINGS storage_policy = 'statistics_tiered';

CREATE TABLE IF NOT EXISTS statistic.ticker_stat_v2 AS statistic.ticker_stat
ENGINE = MergeTree
PARTITION BY toYYYYMM(played, 'Asia/Krasnoyarsk')
ORDER BY (client, played, id)
TTL played + INTERVAL 1 YEAR TO VOLUME 'cold'
SETTINGS storage_policy = 'statistics_tiered';
