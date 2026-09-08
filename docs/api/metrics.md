# Metrics API

Authentication:
- Requires `Authorization: Bearer <api-key>` when `PIXIVUTIL_SERVER_API_KEY` is set.
- If `PIXIVUTIL_SERVER_API_KEY` is unset/empty, authentication is disabled.

`GET /metrics`

Prometheus exposition endpoint, in the standard text format. Note this endpoint is served at the root, not under `/api`, and a Prometheus scrape job must send the bearer token when authentication is enabled.

## Exported metrics

`pixivutil_server_info`: build info, carries a `version` label.

Database counts, refreshed every 60s:
- `pixivutil_db_members_total`
- `pixivutil_db_artworks_total`
- `pixivutil_db_pages_total`
- `pixivutil_db_tags_total`
- `pixivutil_db_series_total`

Disk usage, refreshed every 300s:
- `pixivutil_disk_downloads_bytes`
- `pixivutil_disk_database_bytes`

Host system, refreshed every 15s:
- `pixivutil_cpu_usage_percent`
- `pixivutil_memory_used_bytes`
- `pixivutil_memory_total_bytes`
- `pixivutil_sys_disk_used_bytes`
- `pixivutil_sys_disk_total_bytes`

Worker queue, refreshed every 15s from `RABBITMQ_MANAGEMENT_URL`:
- `pixivutil_queue_depth`: messages pending in the main task queue
- `pixivutil_dlq_depth`: messages in the [dead letter queue](/docs/api/dlq.md)

HTTP traffic, recorded per request by middleware, labelled by `method` and `endpoint` (the route template, not the resolved path). `pixivutil_http_requests_total` is additionally labelled by `status_class`:
- `pixivutil_http_requests_total`
- `pixivutil_http_request_duration_seconds`
- `pixivutil_http_request_size_bytes`
- `pixivutil_http_response_size_bytes`
